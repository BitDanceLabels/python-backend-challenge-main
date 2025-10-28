# Django Mini Test Starter

This repo is a **ready-to-run skeleton** for your 90‑minute Django mini test.

## Quickstart
```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
# import sample
docker compose exec web python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv
# run tests (one is intentionally failing for N+1)
docker compose exec web pytest
```

## Intentional failing test
`apps/core/tests/test_n_plus_one.py` is designed to **fail** until you add `select_related('supplier', 'ingredient')` to your queryset where appropriate.

## What to build
See the full instructions in *README.md* (bundled alongside this repo if provided).
