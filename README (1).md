# E-Commerce Sales & Customer Retention Analysis (MySQL)

A portfolio project demonstrating end-to-end relational database design and
business-focused SQL analysis: schema design, realistic mock data, and three
analytical queries (monthly trends, product performance, and RFM customer
segmentation) built entirely in MySQL using CTEs, window-style aggregation,
and CASE-based logic.

## Tech Stack
- **MySQL 8.0+**
- Common Table Expressions (CTEs)
- `DATEDIFF`, `DATE_FORMAT`, `CASE WHEN` segmentation logic
- Python (`faker`, `pandas`) for relational mock data generation

## Repository Structure
| File | Purpose |
|---|---|
| `01_schema.sql` | DDL — creates `customers`, `products`, and `orders` (line-item grain) with PK/FK constraints and indexes |
| `02_seed_data.sql` | DML — contains 500 customers, 150 products, and 5,000 realistic order line items generated via Python Faker |
| `03_analysis_queries.sql` | Query A (monthly trend), Query B (top products), Query C (RFM segmentation) |
| `data_generator.py` | Python ETL script utilizing the Faker library to generate the relational mock dataset in `02_seed_data.sql` |

`data_generator.py` also drops a CSV copy of the same dataset into
`csv_exports/` (`customers.csv`, `products.csv`, `orders.csv`), for anyone
who prefers MySQL Workbench's Table Data Import Wizard over running SQL
directly.

## How to Run
```bash
mysql -u your_username -p < 01_schema.sql
mysql -u your_username -p < 02_seed_data.sql
mysql -u your_username -p < 03_analysis_queries.sql
```
Or run each file in order inside a MySQL client / Workbench session.

**To regenerate `02_seed_data.sql`** with a fresh dataset:
```bash
pip install -r requirements.txt
python data_generator.py
```

## Key Business Insights (from the generated dataset)

**Scale:** 500 customers, 150 products, and 5,000 order line items across
2,987 orders, spanning the last 12 months. Simulated total revenue:
**$657,973.14**.

**Product performance:** Revenue leadership skews toward the
**Home & Office** category — the **Foldable Monitor Stand** and
**Wireless Whiteboard** are the top two products by revenue, each backed by
a distinct pattern: the Monitor Stand wins on high unit volume (289 sold),
while the Whiteboard wins on fewer, higher-ticket sales. The
**Woven Belt** (Accessories) and **Portable Monitor** (Electronics) round
out the top four, showing revenue leadership genuinely spans categories
rather than concentrating in one — worth knowing before deciding where to
concentrate marketing spend.

**Customer retention (RFM):** At this scale, segmentation surfaces a
much clearer picture of the customer base:
- **VIP (166 customers, ~33%)** — averaging **$2,979** in lifetime spend.
  This third of the customer base is the primary revenue engine and the
  highest-priority group for loyalty perks and retention investment.
- **Churned (132 customers, ~26%)** — no purchase in 120+ days, averaging
  $451 lifetime spend. A meaningful revenue pool that's gone quiet —
  a natural win-back campaign target.
- **At Risk (65 customers, ~13%)** and **Loyal (65 customers, ~13%)** —
  similar-sized groups sitting on opposite trajectories: At Risk customers
  are recent-but-slowing VIPs-in-waiting, while Loyal customers are
  frequent buyers who haven't hit VIP spend thresholds yet — both are
  natural nudge/upsell targets.
- **New / Low Engagement (39 customers, ~8%)** — single recent orders with
  no repeat pattern yet; worth nurturing with onboarding content before
  they either convert to Loyal or drift to Churned.

## Why This Project Matters
This project mirrors a real retention analytics workflow: instead of
just reporting "what happened," Query C converts raw transaction history
into a segmented, exportable customer list that a CRM or marketing team
could act on directly — connecting SQL technique (CTEs, `DATEDIFF`,
`CASE WHEN`) to a measurable business outcome (reducing churn, growing
customer lifetime value). Generating the underlying data with `data_generator.py`
rather than hand-typing it also demonstrates a repeatable, version-controllable
approach to building test datasets — the same pattern used to seed staging
environments in production data engineering work.
