# Django Mini-Test — Import & Admin (90 minutes)

**Goal:** Demonstrate practical Django skills on models, admin, data import/export, and basic workflow. AI tools are **allowed** with disclosure (see `AI_USAGE.md`).

---

## Timebox

- **Total time:** ~90 minutes (hard cap).
- **Deliverables:** Working code + small README notes + `AI_USAGE.md` + short screencast link.
- **Stack provided:** Django, Postgres (via Docker), pytest (optional bonus), django-import-export (optional).

---

## What you build

Create a minimal Django app for **Suppliers** and their **Price List Items** with a lightweight approval flow.

### Data Model
- **Supplier**: `name` (required), `country_code` (2-letter), `contact_email` (optional), `is_active` (bool, default true), timestamps.
- **Ingredient**: `name` (case-insensitive unique), `aliases` (free-text, optional), `is_active` (bool), timestamps.
- **PriceListItem**: FK `supplier`, optional FK `ingredient`, `sku` (text), `pack_size` (text), `uom` (text), `price` (decimal), `currency` (text), `effective_date` (date), `status` (`pending|approved|rejected`), `source_file` (text), timestamps.
  - **Rule:** once `status="approved"`, price/editing must be blocked unless explicitly **Unapproved** via an admin action (also record who/unwhen).

### Admin UI (required)
- Register **Supplier**, **Ingredient**, **PriceListItem**.
- List display with sensible columns; filters for supplier/status; search (`supplier name`, `sku`, `ingredient name` and matches on `aliases`).
- Bulk actions: **Approve**, **Reject**, **Unapprove** (with audit of user & timestamp). Approved rows become read-only for price fields.

### Import (required)
- Provide one of:
  - Admin action **“Import from CSV”**, or
  - Management command `import_prices --file path.csv`.
- Read the supplied CSV (headers can vary; see sample). Handle:
  - trimming/whitespace, currency symbols, blank prices
  - idempotency: re-running import for the same file must not create duplicates. Hint: stable key = (`supplier`, `sku`, `effective_date`, normalized `price`).
- On row error, skip safely and collect an **import report** summary (count created/updated/skipped with reasons).

### Export (required)
- Export filtered `PriceListItem` rows to CSV from admin (or management command).

### Bonus (pick **one**)
- A) **Async stub**: Celery task (or simple background stub) that prints/returns “matched X items” when queued from an admin action.
- B) **Search**: Add fuzzy search using Postgres trigram (`pg_trgm`) or a simple `icontains` fallback that includes `aliases` join.
- C) **Test**: A small `pytest` covering the import validator OR the read-only-on-approval rule.

---

## AI Usage Policy (required)

- AI tools are allowed. Add an `AI_USAGE.md` describing:
  - Which tools you used and why
  - Prompts/snippets that materially shaped the code (or a concise summary)
  - What you wrote vs. what was AI-generated and then edited

---

## How we run it

Provide steps in your project README. A typical flow is:

```bash
# one-time
docker compose up -d
python manage.py migrate
python manage.py createsuperuser  # or use provided fixture

# import (choose one style)
python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv

# run server
python manage.py runserver

# (optional) tests
pytest -q
```

If you use environment variables, document them and provide `.env.example`.

---

## Hidden correctness checks (disclosed)

- Re-importing the same CSV should not make duplicates (idempotent key).
- Approved `PriceListItem` must be read-only until **Unapprove** action.
- Admin search should find an item by an **ingredient alias** (not just exact name).

---

## Submission checklist

- [ ] Code compiles and runs; migrations included
- [ ] Admin actions: Approve/Reject/Unapprove working with audit fields
- [ ] Import handles trimming, symbols, and duplicates safely
- [ ] Export working
- [ ] `AI_USAGE.md` present and honest
- [ ] Short screencast (5–7 min) link in your README (run-through + trade-offs)
- [ ] Bonus task chosen and implemented (optional)

---

## What we evaluate (100 pts)

- **Model design (20)**: sensible constraints, indexes, CI-unique ingredient names
- **Admin UX (20)**: list display, filters, actions, alias search
- **Import/Export (25)**: validation, idempotency, report clarity
- **Code quality (15)**: structure, typing, readability
- **Bonus (10)**: async/search/test
- **Docs & setup (10)**: clear instructions, .env example

Good luck! Keep scope tight and prioritize correctness over breadth.
