"""Initial sample data for the ecommerce SQLite database.

Runs at API startup; inserts only when the tables are empty, so a container
rebuilt from scratch always comes up with a usable catalog.
"""

from datetime import datetime, timezone

from db import ECOMMERCE_DB

SEED_PRODUCTS = [
    # Phones - sold by Tech Store Chile SpA (80.567.890-1)
    {
        "id": "prod_phone001",
        "name": "iPhone 15 Pro",
        "price": 999.99,
        "stock": 25,
        "sku": "APL-IP15P-256",
        "seller_id": "80.567.890-1",
    },
    {
        "id": "prod_phone002",
        "name": "Samsung Galaxy S24",
        "price": 849.99,
        "stock": 30,
        "sku": "SAM-GS24-128",
        "seller_id": "80.567.890-1",
    },
    {
        "id": "prod_phone003",
        "name": "Google Pixel 8",
        "price": 699.99,
        "stock": 18,
        "sku": "GOO-PX8-128",
        "seller_id": "80.567.890-1",
    },
    # Mugs - sold by Hogar y Cocina SpA (83.890.123-4)
    {
        "id": "prod_mug001",
        "name": "Ceramic Coffee Mug - White",
        "price": 12.99,
        "stock": 150,
        "sku": "MUG-CER-WHT",
        "seller_id": "83.890.123-4",
    },
    {
        "id": "prod_mug002",
        "name": "Travel Thermos Mug",
        "price": 24.99,
        "stock": 75,
        "sku": "MUG-TRM-BLK",
        "seller_id": "83.890.123-4",
    },
    # Shoes - sold by Deportes y Más S.A. (81.678.901-2)
    {
        "id": "prod_shoe001",
        "name": "Nike Air Max 90",
        "price": 129.99,
        "stock": 40,
        "sku": "NIK-AM90-42",
        "seller_id": "81.678.901-2",
    },
    {
        "id": "prod_shoe002",
        "name": "Adidas Ultraboost",
        "price": 179.99,
        "stock": 35,
        "sku": "ADI-UB-43",
        "seller_id": "81.678.901-2",
    },
    {
        "id": "prod_shoe003",
        "name": "Converse Chuck Taylor",
        "price": 59.99,
        "stock": 60,
        "sku": "CNV-CT-41",
        "seller_id": "81.678.901-2",
    },
    # T-Shirts - sold by Moda Urbana Ltda. (82.789.012-3)
    {
        "id": "prod_tshirt01",
        "name": "Cotton Basic Tee - Black",
        "price": 19.99,
        "stock": 200,
        "sku": "TEE-BAS-BLK-M",
        "seller_id": "82.789.012-3",
    },
    {
        "id": "prod_tshirt02",
        "name": "Cotton Basic Tee - White",
        "price": 19.99,
        "stock": 180,
        "sku": "TEE-BAS-WHT-M",
        "seller_id": "82.789.012-3",
    },
    {
        "id": "prod_tshirt03",
        "name": "Graphic Print Tee",
        "price": 29.99,
        "stock": 90,
        "sku": "TEE-GFX-001",
        "seller_id": "82.789.012-3",
    },
    # Headphones - sold by Audio Premium Chile S.A. (84.901.234-5)
    {
        "id": "prod_audio01",
        "name": "Sony WH-1000XM5",
        "price": 349.99,
        "stock": 20,
        "sku": "SNY-WH1000-BLK",
        "seller_id": "84.901.234-5",
    },
    {
        "id": "prod_audio02",
        "name": "AirPods Pro 2",
        "price": 249.99,
        "stock": 45,
        "sku": "APL-APP2-WHT",
        "seller_id": "84.901.234-5",
    },
    {
        "id": "prod_audio03",
        "name": "JBL Tune 510BT",
        "price": 49.99,
        "stock": 80,
        "sku": "JBL-T510-BLU",
        "seller_id": "84.901.234-5",
    },
    # Sports Equipment - sold by Deportes y Más S.A. (81.678.901-2)
    {
        "id": "prod_sport01",
        "name": "Spalding Basketball",
        "price": 29.99,
        "stock": 50,
        "sku": "SPL-BB-OFF",
        "seller_id": "81.678.901-2",
    },
    {
        "id": "prod_sport02",
        "name": "Wilson Tennis Racket",
        "price": 89.99,
        "stock": 25,
        "sku": "WIL-TR-PRO",
        "seller_id": "81.678.901-2",
    },
    {
        "id": "prod_sport03",
        "name": "Yoga Mat - Purple",
        "price": 34.99,
        "stock": 65,
        "sku": "YOG-MAT-PRP",
        "seller_id": "81.678.901-2",
    },
    # Accessories - sold by Moda Urbana Ltda. (82.789.012-3)
    {
        "id": "prod_acc001",
        "name": "Leather Wallet",
        "price": 49.99,
        "stock": 70,
        "sku": "ACC-WAL-BRN",
        "seller_id": "82.789.012-3",
    },
    {
        "id": "prod_acc002",
        "name": "Sunglasses - Aviator",
        "price": 79.99,
        "stock": 40,
        "sku": "ACC-SUN-AVT",
        "seller_id": "82.789.012-3",
    },
    {
        "id": "prod_acc003",
        "name": "Canvas Backpack",
        "price": 59.99,
        "stock": 55,
        "sku": "ACC-BAG-CNV",
        "seller_id": "82.789.012-3",
    },
]

SEED_CUSTOMERS = [
    {"id": "cust_john001", "name": "John Smith", "email": "john.smith@example.com"},
    {"id": "cust_jane002", "name": "Jane Doe", "email": "jane.doe@example.com"},
    {"id": "cust_mike003", "name": "Mike Johnson", "email": "mike.j@example.com"},
]


def seed_data() -> None:
    """Populate the database with initial sample data (only if empty)."""
    if len(ECOMMERCE_DB["products"]) > 0:
        return

    now = datetime.now(timezone.utc).isoformat()

    for product in SEED_PRODUCTS:
        record = {**product, "created_at": now, "updated_at": now}
        ECOMMERCE_DB["products"][record["id"]] = record

    for customer in SEED_CUSTOMERS:
        record = {**customer, "created_at": now, "updated_at": now}
        ECOMMERCE_DB["customers"][record["id"]] = record
