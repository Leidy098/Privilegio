import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr
from typing import Any

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor
from werkzeug.exceptions import HTTPException


app = Flask(__name__)

PRODUCT_TABLE = '"Privilegio_App_product"'
SHOPPING_CART_TABLE = '"Privilegio_App_shoppingcart"'
CART_ITEM_TABLE = '"Privilegio_App_cartitem"'
SIZE_CHART_TABLE = '"Privilegio_App_categorysizechart"'
SIZE_ENTRY_TABLE = '"Privilegio_App_sizeentry"'

SIZES_ORDER = ["S", "M", "L", "XL"]
FIT_THRESHOLD = 0.20


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: dict[str, Any] | None = None

    def to_response(self) -> tuple[dict[str, Any], int]:
        payload: dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload, self.status_code


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "privilegio"),
        user=os.getenv("POSTGRES_USER", "privilegio"),
        password=os.getenv("POSTGRES_PASSWORD", "privilegio"),
        cursor_factory=RealDictCursor,
    )


def calculate_tax(subtotal: Decimal) -> Decimal:
    raw_rate = os.getenv("TAX_RATE", "0.19")
    try:
        rate = Decimal(raw_rate)
    except InvalidOperation as exc:
        raise ApiError(500, "invalid_tax_rate", "Configured tax rate is invalid.") from exc
    return (subtotal * rate).quantize(Decimal("0.01"))


def validate_payload(payload: Any) -> tuple[str, list[dict[str, int]]]:
    if not isinstance(payload, dict):
        raise ApiError(400, "invalid_body", "Request body must be a JSON object.")

    customer_email = payload.get("customer_email")
    items = payload.get("items")

    if not isinstance(customer_email, str) or "@" not in parseaddr(customer_email)[1]:
        raise ApiError(400, "invalid_customer_email", "customer_email is required and must be valid.")
    if not isinstance(items, list) or not items:
        raise ApiError(400, "invalid_items", "items must contain at least one cart line.")

    normalized_items: list[dict[str, int]] = []
    seen_products: set[int] = set()

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ApiError(400, "invalid_item", "Each item must be an object.", {"index": index})

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if not isinstance(product_id, int) or product_id < 1:
            raise ApiError(400, "invalid_product_id", "product_id must be a positive integer.", {"index": index})
        if not isinstance(quantity, int) or quantity < 1:
            raise ApiError(400, "invalid_quantity", "quantity must be a positive integer.", {"index": index})
        if product_id in seen_products:
            raise ApiError(400, "duplicated_item", "A product cannot be repeated in the cart.", {"product_id": product_id})

        seen_products.add(product_id)
        normalized_items.append({"product_id": product_id, "quantity": quantity})

    return customer_email, normalized_items


def fetch_products(cursor, product_ids: list[int]) -> dict[int, dict[str, Any]]:
    placeholders = ", ".join(["%s"] * len(product_ids))
    query = f"""
        SELECT id, price, is_active
        FROM {PRODUCT_TABLE}
        WHERE id IN ({placeholders})
    """
    cursor.execute(query, product_ids)
    rows = cursor.fetchall()
    products = {int(row["id"]): row for row in rows}

    for product_id in product_ids:
        product = products.get(product_id)
        if not product or not product["is_active"]:
            raise ApiError(404, "product_not_available", f"Product {product_id} is not available.")

    return products


def create_cart(customer_email: str, items: list[dict[str, int]]) -> dict[str, Any]:
    connection = get_connection()
    now = datetime.now(timezone.utc)

    try:
        with connection:
            with connection.cursor() as cursor:
                product_map = fetch_products(cursor, [item["product_id"] for item in items])

                cursor.execute(
                    """
                    INSERT INTO {shopping_cart_table}
                    (customer_email, status, subtotal, tax, total, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """.format(shopping_cart_table=SHOPPING_CART_TABLE),
                    (customer_email, "draft", Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), now, now),
                )
                cart_id = int(cursor.fetchone()["id"])

                serialized_items: list[dict[str, Any]] = []
                subtotal = Decimal("0.00")

                for item in items:
                    product = product_map[item["product_id"]]
                    unit_price = Decimal(product["price"]).quantize(Decimal("0.01"))
                    line_total = (unit_price * Decimal(item["quantity"])).quantize(Decimal("0.01"))
                    subtotal += line_total

                    cursor.execute(
                        """
                        INSERT INTO {cart_item_table}
                        (cart_id, product_id, quantity, unit_price, line_total)
                        VALUES (%s, %s, %s, %s, %s)
                        """.format(cart_item_table=CART_ITEM_TABLE),
                        (cart_id, item["product_id"], item["quantity"], unit_price, line_total),
                    )

                    serialized_items.append(
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                            "unit_price": f"{unit_price:.2f}",
                            "line_total": f"{line_total:.2f}",
                        }
                    )

                subtotal = subtotal.quantize(Decimal("0.01"))
                tax = calculate_tax(subtotal)
                total = (subtotal + tax).quantize(Decimal("0.01"))

                cursor.execute(
                    """
                    UPDATE {shopping_cart_table}
                    SET subtotal = %s, tax = %s, total = %s, updated_at = %s
                    WHERE id = %s
                    """.format(shopping_cart_table=SHOPPING_CART_TABLE),
                    (subtotal, tax, total, now, cart_id),
                )

                return {
                    "id": cart_id,
                    "customer_email": customer_email,
                    "status": "draft",
                    "subtotal": f"{subtotal:.2f}",
                    "tax": f"{tax:.2f}",
                    "total": f"{total:.2f}",
                    "items": serialized_items,
                }
    except psycopg2.Error as exc:
        raise ApiError(500, "database_error", "Database operation failed.", {"hint": str(exc).strip()}) from exc
    finally:
        connection.close()


def fetch_size_chart(cursor, category: str) -> tuple[float, list[dict]]:
    cursor.execute(
        f"SELECT id, coat_margin FROM {SIZE_CHART_TABLE} WHERE category = %s",
        (category,),
    )
    row = cursor.fetchone()
    if row is None:
        raise ApiError(404, "chart_not_found", f"No hay tabla de tallas para la categoría '{category}'.")
    cursor.execute(
        f"SELECT size, measurement, min_cm, max_cm FROM {SIZE_ENTRY_TABLE} WHERE chart_id = %s",
        (row["id"],),
    )
    return float(row["coat_margin"]), [dict(e) for e in cursor.fetchall()]


def calculate_recommendation(
    measurements: dict[str, float],
    entries: list[dict],
    coat_margin: float,
) -> dict[str, Any]:
    adjusted = {k: v + coat_margin for k, v in measurements.items()}

    by_measurement: dict[str, dict[str, tuple[float, float]]] = {}
    for entry in entries:
        by_measurement.setdefault(entry["measurement"], {})[entry["size"]] = (
            float(entry["min_cm"]),
            float(entry["max_cm"]),
        )

    measurement_results: dict[str, tuple[str, str]] = {}
    out_of_range_fields: list[str] = []

    for measurement, value in adjusted.items():
        if measurement not in by_measurement:
            continue
        size_ranges = by_measurement[measurement]
        matched = False
        for size in SIZES_ORDER:
            if size not in size_ranges:
                continue
            min_cm, max_cm = size_ranges[size]
            if min_cm <= value <= max_cm:
                span = max_cm - min_cm
                position = (value - min_cm) / span if span > 0 else 0.5
                if position <= FIT_THRESHOLD:
                    fit = "Holgado"
                elif position >= (1 - FIT_THRESHOLD):
                    fit = "Ceñido"
                else:
                    fit = "Regular"
                measurement_results[measurement] = (size, fit)
                matched = True
                break
        if not matched:
            out_of_range_fields.append(measurement)

    if out_of_range_fields:
        return {
            "out_of_range": True, "recommended_size": None, "fit": None,
            "message": "Tus medidas están fuera del rango disponible para este producto.",
            "conflict": False, "suggest_next_size": None,
        }

    if not measurement_results:
        return {
            "out_of_range": True, "recommended_size": None, "fit": None,
            "message": "No se pudieron evaluar las medidas ingresadas.",
            "conflict": False, "suggest_next_size": None,
        }

    sizes_found = {s for s, _ in measurement_results.values()}
    conflict = len(sizes_found) > 1
    recommended_size = max(sizes_found, key=lambda s: SIZES_ORDER.index(s))

    fits_for_recommended = [f for s, f in measurement_results.values() if s == recommended_size]
    if not fits_for_recommended:
        fits_for_recommended = [f for _, f in measurement_results.values()]
    overall_fit = Counter(fits_for_recommended).most_common(1)[0][0]

    suggest_next: str | None = None
    if overall_fit == "Ceñido" and not conflict:
        idx = SIZES_ORDER.index(recommended_size)
        if idx < len(SIZES_ORDER) - 1:
            suggest_next = SIZES_ORDER[idx + 1]

    if conflict:
        field_notes = ", ".join(
            f"tu {m} corresponde a talla {s}"
            for m, (s, _) in measurement_results.items()
            if s != recommended_size
        )
        message = (
            f"Te recomendamos talla {recommended_size} para mayor comodidad. "
            f"{field_notes.capitalize()}."
        )
    else:
        fit_descriptions = {
            "Regular": "La prenda se ajustará cómodamente a tu cuerpo.",
            "Holgado": "La prenda tendrá un ajuste holgado.",
            "Ceñido": (
                f"La prenda tendrá un ajuste ceñido. También podrías probar la talla {suggest_next}."
                if suggest_next
                else "La prenda tendrá un ajuste ceñido."
            ),
        }
        message = (
            f"Te recomendamos talla {recommended_size} con ajuste {overall_fit.lower()}. "
            f"{fit_descriptions[overall_fit]}"
        )

    return {
        "out_of_range": False,
        "recommended_size": recommended_size,
        "fit": overall_fit,
        "message": message,
        "conflict": conflict,
        "suggest_next_size": suggest_next,
    }


@app.errorhandler(ApiError)
def handle_api_error(error: ApiError):
    payload, status_code = error.to_response()
    return jsonify(payload), status_code


@app.errorhandler(HTTPException)
def handle_http_error(error: HTTPException):
    payload = {
        "error": {
            "code": error.name.lower().replace(" ", "_"),
            "message": error.description,
        }
    }
    return jsonify(payload), error.code or 500


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    payload = {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred.",
            "details": {"hint": str(error)},
        }
    }
    return jsonify(payload), 500


@app.get("/health")
def healthcheck():
    return jsonify({"status": "ok"}), 200


@app.post("/api/v2/carts/")
def create_cart_endpoint():
    customer_email, items = validate_payload(request.get_json(silent=True))
    response = create_cart(customer_email, items)
    return jsonify(response), 201


@app.post("/api/v2/size-recommendation/")
def size_recommendation_endpoint():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError(400, "invalid_body", "Request body must be a JSON object.")

    product_id = payload.get("product_id")
    measurements = payload.get("measurements")

    if not isinstance(product_id, int) or product_id < 1:
        raise ApiError(400, "invalid_product_id", "product_id must be a positive integer.")
    if not isinstance(measurements, dict) or not measurements:
        raise ApiError(400, "invalid_measurements", "measurements must be a non-empty object.")

    validated: dict[str, float] = {}
    for key, value in measurements.items():
        if not isinstance(value, (int, float)) or not (20 <= float(value) <= 200):
            raise ApiError(400, "invalid_measurement", f"'{key}' debe estar entre 20 y 200 cm.")
        validated[key] = float(value)

    connection = get_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT category FROM {PRODUCT_TABLE} WHERE id = %s AND is_active = TRUE",
                    (product_id,),
                )
                product = cursor.fetchone()
                if product is None:
                    raise ApiError(404, "product_not_found", f"Producto {product_id} no disponible.")
                coat_margin, entries = fetch_size_chart(cursor, product["category"])

        result = calculate_recommendation(validated, entries, coat_margin)
        return jsonify(result), 200
    except ApiError:
        raise
    except psycopg2.Error as exc:
        raise ApiError(500, "database_error", "Error en base de datos.", {"hint": str(exc).strip()}) from exc
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
