from decimal import Decimal
from django.db import migrations

SHIRT_DATA = [
    ("S",  "chest",     86.0, 90.0),
    ("M",  "chest",     91.0, 96.0),
    ("L",  "chest",     97.0, 102.0),
    ("XL", "chest",    103.0, 110.0),
    ("S",  "waist",     70.0, 74.0),
    ("M",  "waist",     75.0, 80.0),
    ("L",  "waist",     81.0, 87.0),
    ("XL", "waist",     88.0, 95.0),
    ("S",  "shoulders", 42.0, 44.0),
    ("M",  "shoulders", 44.0, 46.0),
    ("L",  "shoulders", 46.0, 48.0),
    ("XL", "shoulders", 48.0, 51.0),
    ("S",  "neck",      37.0, 38.0),
    ("M",  "neck",      38.0, 40.0),
    ("L",  "neck",      40.0, 42.0),
    ("XL", "neck",      42.0, 44.0),
]

PANTS_DATA = [
    ("S",  "waist",      68.0, 72.0),
    ("M",  "waist",      73.0, 78.0),
    ("L",  "waist",      79.0, 85.0),
    ("XL", "waist",      86.0, 93.0),
    ("S",  "hips",       90.0, 94.0),
    ("M",  "hips",       95.0, 100.0),
    ("L",  "hips",      101.0, 107.0),
    ("XL", "hips",      108.0, 115.0),
    ("S",  "leg_length", 76.0, 79.0),
    ("M",  "leg_length", 79.0, 82.0),
    ("L",  "leg_length", 82.0, 85.0),
    ("XL", "leg_length", 85.0, 88.0),
]

OUTERWEAR_DATA = [
    ("S",  "chest",      88.0,  92.0),
    ("M",  "chest",      93.0,  98.0),
    ("L",  "chest",      99.0, 104.0),
    ("XL", "chest",     105.0, 112.0),
    ("S",  "waist",      72.0,  76.0),
    ("M",  "waist",      77.0,  82.0),
    ("L",  "waist",      83.0,  89.0),
    ("XL", "waist",      90.0,  97.0),
    ("S",  "shoulders",  43.0,  45.0),
    ("M",  "shoulders",  45.0,  47.0),
    ("L",  "shoulders",  47.0,  49.0),
    ("XL", "shoulders",  49.0,  52.0),
    ("S",  "hips",       92.0,  96.0),
    ("M",  "hips",       97.0, 102.0),
    ("L",  "hips",      103.0, 109.0),
    ("XL", "hips",      110.0, 117.0),
    ("S",  "arm_length", 58.0,  60.0),
    ("M",  "arm_length", 60.0,  62.0),
    ("L",  "arm_length", 62.0,  64.0),
    ("XL", "arm_length", 64.0,  66.0),
]


def seed_charts(apps, schema_editor):
    CategorySizeChart = apps.get_model("Privilegio_App", "CategorySizeChart")
    SizeEntry = apps.get_model("Privilegio_App", "SizeEntry")

    datasets = [
        ("shirt",     SHIRT_DATA,     Decimal("0.0")),
        ("pants",     PANTS_DATA,     Decimal("0.0")),
        ("outerwear", OUTERWEAR_DATA, Decimal("2.0")),
    ]

    for category, rows, margin in datasets:
        chart = CategorySizeChart.objects.create(category=category, coat_margin=margin)
        SizeEntry.objects.bulk_create([
            SizeEntry(
                chart=chart,
                size=size,
                measurement=measurement,
                min_cm=Decimal(str(min_cm)),
                max_cm=Decimal(str(max_cm)),
            )
            for size, measurement, min_cm, max_cm in rows
        ])


def unseed_charts(apps, schema_editor):
    CategorySizeChart = apps.get_model("Privilegio_App", "CategorySizeChart")
    CategorySizeChart.objects.filter(category__in=["shirt", "pants", "outerwear"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("Privilegio_App", "0003_categorysizechart_sizeentry"),
    ]

    operations = [
        migrations.RunPython(seed_charts, unseed_charts),
    ]
