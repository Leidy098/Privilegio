from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .interfaces import TaxCalculator

SIZES_ORDER = ["S", "M", "L", "XL"]
FIT_THRESHOLD = 0.20  # bottom/top 20% of a range = holgado/ceñido


class ColombiaIVACalculator(TaxCalculator):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return (subtotal * Decimal("0.19")).quantize(Decimal("0.01"))


@dataclass
class SizeRecommendation:
    out_of_range: bool
    recommended_size: str | None
    fit: str | None
    message: str
    conflict: bool
    suggest_next_size: str | None


class SizeRecommendationCalculator:
    def calculate(
        self,
        measurements: dict[str, float],
        entries: list[Any],
        coat_margin: float = 0.0,
    ) -> SizeRecommendation:
        adjusted = {k: v + coat_margin for k, v in measurements.items()}

        # Group entries: measurement → size → (min, max)
        by_measurement: dict[str, dict[str, tuple[float, float]]] = {}
        for entry in entries:
            by_measurement.setdefault(entry.measurement, {})[entry.size] = (
                float(entry.min_cm),
                float(entry.max_cm),
            )

        measurement_results: dict[str, tuple[str, str]] = {}  # measurement → (size, fit)
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
            return SizeRecommendation(
                out_of_range=True,
                recommended_size=None,
                fit=None,
                message="Tus medidas están fuera del rango disponible para este producto.",
                conflict=False,
                suggest_next_size=None,
            )

        if not measurement_results:
            return SizeRecommendation(
                out_of_range=True,
                recommended_size=None,
                fit=None,
                message="No se pudieron evaluar las medidas ingresadas.",
                conflict=False,
                suggest_next_size=None,
            )

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
                "Ceñido": f"La prenda tendrá un ajuste ceñido. También podrías probar la talla {suggest_next}."
                if suggest_next
                else "La prenda tendrá un ajuste ceñido.",
            }
            message = (
                f"Te recomendamos talla {recommended_size} con ajuste {overall_fit.lower()}. "
                f"{fit_descriptions[overall_fit]}"
            )

        return SizeRecommendation(
            out_of_range=False,
            recommended_size=recommended_size,
            fit=overall_fit,
            message=message,
            conflict=conflict,
            suggest_next_size=suggest_next,
        )
