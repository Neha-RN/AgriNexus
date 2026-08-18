from __future__ import annotations

import os

import psycopg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agrinexus:agrinexus_dev@localhost:5432/agrinexus",
)

COUNTRIES = [
    ("IN", "India"),
    ("BR", "Brazil"),
    ("CN", "China"),
    ("RU", "Russia"),
    ("ZA", "South Africa"),
]

FIELDS = [
    {
        "country_code": "IN",
        "name": "TN Rice Field 001",
        "crop_type": "Rice",
        "area_hectares": 2.40,
        "geometry": (
            "MULTIPOLYGON(((80.1200 10.9200,"
            "80.1250 10.9200,"
            "80.1250 10.9250,"
            "80.1200 10.9250,"
            "80.1200 10.9200)))"
        ),
    },
    {
        "country_code": "BR",
        "name": "MT Soybean Field 001",
        "crop_type": "Soybean",
        "area_hectares": 18.75,
        "geometry": (
            "MULTIPOLYGON(((-56.1000 -13.2500,"
            "-56.0950 -13.2500,"
            "-56.0950 -13.2450,"
            "-56.1000 -13.2450,"
            "-56.1000 -13.2500)))"
        ),
    },
    {
        "country_code": "CN",
        "name": "Henan Wheat Field 001",
        "crop_type": "Wheat",
        "area_hectares": 6.80,
        "geometry": (
            "MULTIPOLYGON(((114.3000 34.7200,"
            "114.3050 34.7200,"
            "114.3050 34.7250,"
            "114.3000 34.7250,"
            "114.3000 34.7200)))"
        ),
    },
    {
        "country_code": "RU",
        "name": "Rostov Wheat Field 001",
        "crop_type": "Wheat",
        "area_hectares": 32.50,
        "geometry": (
            "MULTIPOLYGON(((39.6500 47.2000,"
            "39.6550 47.2000,"
            "39.6550 47.2050,"
            "39.6500 47.2050,"
            "39.6500 47.2000)))"
        ),
    },
    {
        "country_code": "ZA",
        "name": "Free State Maize Field 001",
        "crop_type": "Maize",
        "area_hectares": 24.10,
        "geometry": (
            "MULTIPOLYGON(((26.2000 -28.9500,"
            "26.2050 -28.9500,"
            "26.2050 -28.9450,"
            "26.2000 -28.9450,"
            "26.2000 -28.9500)))"
        ),
    },
]


def main() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for code, name in COUNTRIES:
                cur.execute(
                    """
                    INSERT INTO countries (code, name)
                    VALUES (%s, %s)
                    ON CONFLICT (code)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (code, name),
                )

            for field in FIELDS:
                cur.execute(
                    """
                    INSERT INTO fields (
                        country_id,
                        name,
                        crop_type,
                        area_hectares,
                        geometry
                    )
                    SELECT
                        c.id,
                        %s,
                        %s,
                        %s,
                        ST_GeomFromText(%s, 4326)
                    FROM countries c
                    WHERE c.code = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM fields f
                        WHERE f.name = %s
                    )
                    """,
                    (
                        field["name"],
                        field["crop_type"],
                        field["area_hectares"],
                        field["geometry"],
                        field["country_code"],
                        field["name"],
                    ),
                )

        conn.commit()

    print("BRICS seed data inserted successfully.")


if __name__ == "__main__":
    main()