"""
generate_mock_data.py

Generates realistic, relationally-consistent mock data for the
E-Commerce Sales & Customer Retention Analysis schema (customers,
products, orders) and exports it two ways:

    1. mock_data_output/mock_data.sql  -- one file, batch INSERT statements,
       ready to run straight in MySQL Workbench (Query tab or "Run SQL Script").
    2. mock_data_output/customers.csv, products.csv, orders.csv -- one file
       per table, for Workbench's Table Data Import Wizard.

REQUIREMENTS:
    pip install faker pandas
    (or: pip install -r requirements.txt)

USAGE:
    python generate_mock_data.py

NOTE: This script only generates DATA. Run 01_schema.sql from the main
project first to create the `ecommerce_analytics` database and tables --
this script assumes they already exist and simply truncates + repopulates
them.
"""

import os
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

# =========================================================================
# CONFIGURATION
# Row counts follow a realistic e-commerce ratio: a large, high-volume
# fact table (orders) sitting on top of much smaller dimension tables
# (customers, products). Adjust these constants for a different split.
# =========================================================================
RANDOM_SEED            = 42     # fixed seed -> same "random" dataset every run
NUM_CUSTOMERS           = 500
NUM_PRODUCTS            = 150
NUM_ORDER_ROWS          = 5000  # target row count for the orders (line-item) table
ORDER_DATE_RANGE_DAYS   = 365   # orders are spread across the last 12 months
SQL_BATCH_SIZE          = 500   # rows per multi-row INSERT statement
OUTPUT_DIR              = "mock_data_output"

random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)
fake = Faker()


# =========================================================================
# PRODUCT CATALOG TEMPLATES
# Faker has no built-in "realistic e-commerce product name" generator, so
# product names are built from curated adjective/noun combinations per
# category. Prices are randomized within a category-appropriate range and
# snapped to a ".99" ending to mimic real retail pricing.
# =========================================================================
CATEGORY_TEMPLATES = {
    "Electronics": {
        "adjectives": ["Wireless", "Bluetooth", "Smart", "Portable", "USB-C",
                       "Noise-Cancelling", "4K", "HD", "Compact", "Rechargeable"],
        "nouns": ["Earbuds", "Speaker", "Charger", "Webcam", "Monitor",
                  "Keyboard", "Mouse", "Power Bank", "Router", "Headphones"],
        "price_range": (15.00, 299.00),
    },
    "Home & Kitchen": {
        "adjectives": ["Stainless Steel", "Ceramic", "Non-Stick", "Electric",
                       "Insulated", "Glass", "Bamboo", "Cast Iron"],
        "nouns": ["Water Bottle", "Coffee Mug", "Knife Set", "Blender",
                  "Cutting Board", "Toaster", "Kettle", "Food Container Set"],
        "price_range": (9.00, 89.00),
    },
    "Apparel": {
        "adjectives": ["Organic Cotton", "Slim Fit", "Classic", "Merino Wool",
                       "Waterproof", "Lightweight", "Fleece-Lined"],
        "nouns": ["T-Shirt", "Hoodie", "Jacket", "Jeans", "Socks", "Cap",
                  "Scarf", "Sweater"],
        "price_range": (12.00, 79.00),
    },
    "Sports & Outdoors": {
        "adjectives": ["Premium", "Adjustable", "Foldable", "Anti-Slip",
                       "Insulated", "Lightweight", "Heavy-Duty"],
        "nouns": ["Yoga Mat", "Dumbbell Set", "Running Shoes", "Water Bottle",
                  "Resistance Bands", "Tent", "Backpack", "Camping Chair"],
        "price_range": (14.00, 149.00),
    },
    "Accessories": {
        "adjectives": ["Leather", "Vegan Leather", "Minimalist",
                       "RFID-Blocking", "Woven", "Polarized"],
        "nouns": ["Wallet", "Belt", "Sunglasses", "Watch", "Tote Bag",
                  "Keychain", "Card Holder"],
        "price_range": (9.00, 129.00),
    },
    "Home & Office": {
        "adjectives": ["LED", "Adjustable", "Ergonomic", "Wireless",
                       "Compact", "Foldable"],
        "nouns": ["Desk Lamp", "Office Chair", "Monitor Stand",
                  "Desk Organizer", "Whiteboard", "Footrest"],
        "price_range": (14.00, 199.00),
    },
    "Beauty & Personal Care": {
        "adjectives": ["Organic", "Fragrance-Free", "Hydrating", "Vitamin C",
                       "SPF 30", "Sulfate-Free"],
        "nouns": ["Face Serum", "Shampoo", "Moisturizer", "Lip Balm",
                  "Sunscreen", "Body Wash"],
        "price_range": (6.00, 49.00),
    },
    "Books & Stationery": {
        "adjectives": ["Hardcover", "Bestselling", "Illustrated",
                       "Pocket-Sized", "Recycled Paper"],
        "nouns": ["Notebook", "Planner", "Journal", "Pen Set",
                  "Sticky Notes", "Desk Calendar"],
        "price_range": (3.00, 34.00),
    },
}

# Column -> SQL type map, used when rendering INSERT statements so every
# value is formatted (and quoted, or not) correctly for its MySQL type.
TABLE_COLUMNS = {
    "customers": [
        ("customer_id", "int"),
        ("first_name", "str"),
        ("last_name", "str"),
        ("email", "str"),
        ("country", "str"),
        ("signup_date", "date"),
    ],
    "products": [
        ("product_id", "int"),
        ("product_name", "str"),
        ("category", "str"),
        ("unit_price", "decimal"),
    ],
    "orders": [
        ("order_item_id", "int"),
        ("order_id", "int"),
        ("customer_id", "int"),
        ("product_id", "int"),
        ("quantity", "int"),
        ("unit_price_at_order", "decimal"),
        ("order_date", "date"),
    ],
}


def clip(text, max_len):
    """Defensively truncate to a column's VARCHAR length so generated
    data can never violate the schema, even on rare long Faker outputs."""
    return str(text)[:max_len]


def generate_price(price_range):
    """Random price within range, snapped to a '.99' retail ending."""
    low, high = price_range
    raw = random.uniform(low, high)
    return float(f"{int(raw)}.99")


# =========================================================================
# CUSTOMERS
# =========================================================================
def generate_customers(n):
    fake.unique.clear()
    customers = []
    for customer_id in range(1, n + 1):
        customers.append({
            "customer_id": customer_id,
            "first_name": clip(fake.first_name(), 50),
            "last_name": clip(fake.last_name(), 50),
            "email": clip(fake.unique.email(), 100),
            "country": clip(fake.country(), 50),
            # signed up sometime in the 18-1 months before today, so
            # every customer's signup predates the order date window below
            "signup_date": fake.date_between(start_date="-540d", end_date="-30d"),
        })
    return customers


# =========================================================================
# PRODUCTS
# =========================================================================
def generate_products(n):
    products = []
    seen_names = set()
    category_names = list(CATEGORY_TEMPLATES.keys())
    product_id = 1
    attempts = 0
    max_attempts = n * 20  # safety valve against infinite loops

    while len(products) < n and attempts < max_attempts:
        attempts += 1
        category = random.choice(category_names)
        template = CATEGORY_TEMPLATES[category]
        adjective = random.choice(template["adjectives"])
        noun = random.choice(template["nouns"])
        name = f"{adjective} {noun}"

        dedup_key = (category, name)
        if dedup_key in seen_names:
            continue
        seen_names.add(dedup_key)

        products.append({
            "product_id": product_id,
            "product_name": clip(name, 100),
            "category": clip(category, 50),
            "unit_price": generate_price(template["price_range"]),
        })
        product_id += 1

    return products


# =========================================================================
# ORDERS (line-item grain -- matches 01_schema.sql exactly)
# =========================================================================
def generate_orders(customers, products, target_rows):
    today = date.today()
    start_date = today - timedelta(days=ORDER_DATE_RANGE_DAYS)

    # Pareto-weighted sampling gives a realistic 80/20-style skew: a small
    # group of "regulars" and "bestsellers" account for a disproportionate
    # share of orders, instead of every customer/product buying equally --
    # which is what actually happens in real transaction data and is
    # exactly the kind of signal an RFM analysis is built to surface.
    customer_weights = [random.paretovariate(1.5) for _ in customers]
    product_weights = [random.paretovariate(1.2) for _ in products]

    orders = []
    order_item_id = 1
    order_id = 1000

    while len(orders) < target_rows:
        order_id += 1
        customer = random.choices(customers, weights=customer_weights, k=1)[0]
        order_date = fake.date_between(start_date=start_date, end_date=today)
        items_in_order = random.choices([1, 2, 3, 4], weights=[55, 28, 12, 5], k=1)[0]

        products_in_this_order = set()
        for _ in range(items_in_order):
            if len(orders) >= target_rows:
                break

            product = random.choices(products, weights=product_weights, k=1)[0]
            if product["product_id"] in products_in_this_order:
                continue  # don't duplicate the same product within one checkout
            products_in_this_order.add(product["product_id"])

            quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 12, 8, 5], k=1)[0]

            # unit_price_at_order can trail slightly below the current
            # catalog price -- simulating the historical-price snapshot
            # this column exists to protect (see 01_schema.sql notes).
            price_variance = random.uniform(0.95, 1.0)
            unit_price_at_order = round(product["unit_price"] * price_variance, 2)

            orders.append({
                "order_item_id": order_item_id,
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price_at_order": unit_price_at_order,
                "order_date": order_date,
            })
            order_item_id += 1

    return orders


# =========================================================================
# SQL EXPORT
# =========================================================================
def escape_sql_string(value):
    return str(value).replace("'", "''")


def format_sql_value(value, col_type):
    if col_type == "int":
        return str(int(value))
    if col_type == "decimal":
        return f"{float(value):.2f}"
    # "str" and "date" both render as a quoted, escaped SQL literal
    return f"'{escape_sql_string(value)}'"


def build_insert_statements(table_name, rows, batch_size):
    columns_spec = TABLE_COLUMNS[table_name]
    column_names = [col for col, _ in columns_spec]
    statements = []

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        value_tuples = []
        for row in batch:
            formatted = [format_sql_value(row[col], col_type) for col, col_type in columns_spec]
            value_tuples.append(f"({', '.join(formatted)})")

        statement = (
            f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES\n    "
            + ",\n    ".join(value_tuples)
            + ";"
        )
        statements.append(statement)

    return statements


def write_sql_file(customers, products, orders, output_path):
    lines = [
        "-- =====================================================================",
        "-- Auto-generated mock data for ecommerce_analytics",
        f"-- Source: generate_mock_data.py | seed={RANDOM_SEED}",
        f"-- Rows: {len(customers)} customers, {len(products)} products, {len(orders)} order line items",
        "-- =====================================================================",
        "",
        "USE ecommerce_analytics;",
        "",
        "-- Clear existing data (FK-safe order) before reloading.",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE TABLE orders;",
        "TRUNCATE TABLE products;",
        "TRUNCATE TABLE customers;",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "",
        "-- ---------------------------------------------------------------------",
        f"-- customers ({len(customers)} rows)",
        "-- ---------------------------------------------------------------------",
    ]
    lines.extend(build_insert_statements("customers", customers, SQL_BATCH_SIZE))
    lines.append("")
    lines.append("-- ---------------------------------------------------------------------")
    lines.append(f"-- products ({len(products)} rows)")
    lines.append("-- ---------------------------------------------------------------------")
    lines.extend(build_insert_statements("products", products, SQL_BATCH_SIZE))
    lines.append("")
    lines.append("-- ---------------------------------------------------------------------")
    lines.append(f"-- orders ({len(orders)} rows)")
    lines.append("-- ---------------------------------------------------------------------")
    lines.extend(build_insert_statements("orders", orders, SQL_BATCH_SIZE))
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# =========================================================================
# MAIN
# =========================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating customers...")
    customers = generate_customers(NUM_CUSTOMERS)

    print("Generating products...")
    products = generate_products(NUM_PRODUCTS)

    print("Generating orders (this is the big one)...")
    orders = generate_orders(customers, products, NUM_ORDER_ROWS)

    # ---- Referential integrity self-check --------------------------------
    valid_customer_ids = {c["customer_id"] for c in customers}
    valid_product_ids = {p["product_id"] for p in products}
    assert all(o["customer_id"] in valid_customer_ids for o in orders), \
        "FK integrity violation: an order references a customer_id that does not exist."
    assert all(o["product_id"] in valid_product_ids for o in orders), \
        "FK integrity violation: an order references a product_id that does not exist."
    print("Referential integrity check passed: all order rows reference valid customers and products.")

    # ---- CSV export (pandas) ----------------------------------------------
    customers_df = pd.DataFrame(customers)
    products_df = pd.DataFrame(products)
    orders_df = pd.DataFrame(orders)

    customers_df.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    orders_df.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"), index=False)

    # ---- Combined batch-INSERT .sql export --------------------------------
    sql_path = os.path.join(OUTPUT_DIR, "mock_data.sql")
    write_sql_file(customers, products, orders, sql_path)

    total_revenue = sum(o["quantity"] * o["unit_price_at_order"] for o in orders)

    print("\nDone. Files written to '{}':".format(OUTPUT_DIR))
    print(f"  customers.csv   -> {len(customers_df):,} rows")
    print(f"  products.csv    -> {len(products_df):,} rows")
    print(f"  orders.csv      -> {len(orders_df):,} rows")
    print(f"  mock_data.sql   -> all three tables, batched {SQL_BATCH_SIZE} rows/INSERT")
    print(f"\nSimulated total revenue across generated orders: ${total_revenue:,.2f}")


if __name__ == "__main__":
    main()
