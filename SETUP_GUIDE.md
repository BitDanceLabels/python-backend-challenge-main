# Django Supplier Price List - Complete Setup Guide

## Overview

This is a Django application for managing Suppliers and their Price List Items with an approval workflow. The system includes:

- **Models**: Supplier, Ingredient, PriceListItem
- **Admin Interface**: Full CRUD with approval workflow
- **Import/Export**: CSV import with idempotency and CSV export
- **Approval Workflow**: Approve/Reject/Unapprove with audit trail
- **Read-only Enforcement**: Approved items lock price fields
- **Tests**: Pytest suite for approval workflow

## Features Implemented

### Core Features (Required)
- [x] Data models with proper constraints and indexes
- [x] Django Admin interface with filters, search, and actions
- [x] CSV import with idempotency (no duplicates on re-import)
- [x] CSV export functionality
- [x] Approval workflow with audit fields (approved_by, approved_at)
- [x] Read-only enforcement for approved items
- [x] Alias search in admin

### Bonus Features (1 Required)
- [x] **Pytest Test Suite**: Comprehensive tests for approval workflow and read-only rule

### Technical Highlights
- Case-insensitive unique constraint on Ingredient name (database level)
- N+1 query optimization with `select_related()` in admin
- Idempotent CSV import (same file can be imported multiple times safely)
- Full audit trail for approvals

## Prerequisites

- Docker and Docker Compose installed
- Git (for version control)

## Quick Start (5 minutes)

### 1. Clone and Navigate

```bash
cd "c:\Users\Nhut\OneDrive\CVNhutPham-16102025\python-backend-challenge-main (1)\python-backend-challenge-main"
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Or create .env manually with these values:
DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=1
```

### 3. Start Services

```bash
# Start PostgreSQL and Django
docker-compose up -d

# Wait for database to be ready (about 10 seconds)
docker-compose logs -f db

# Press Ctrl+C when you see "database system is ready to accept connections"
```

### 4. Run Migrations

```bash
docker-compose exec web python manage.py migrate
```

### 5. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser

# Enter credentials:
# Username: admin
# Email: admin@example.com
# Password: admin123 (type twice)
```

### 6. Import Sample Data

```bash
docker-compose exec web python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv
```

Expected output:
```
Import report:
  Created: 5
  Updated: 0
  Skipped: 2 (1 blank price, 1 duplicate)
```

### 7. Access Admin Interface

Open browser: http://localhost:8000/admin

Login with:
- Username: `admin`
- Password: `admin123`

## Using the Admin Interface

### Viewing Price List Items

1. Navigate to **Price list items**
2. Use filters on the right:
   - Supplier
   - Status (Pending/Approved/Rejected)
   - Currency
3. Use search box for:
   - SKU
   - Supplier name
   - Ingredient name
   - Ingredient aliases

### Approving Items

1. Select items with checkboxes
2. Choose **"Approve selected items"** from Actions dropdown
3. Click "Go"
4. Items are now **read-only** (price, currency, pack_size, uom, effective_date, ingredient)

### Unapproving Items

1. Select approved items
2. Choose **"Unapprove selected items"**
3. Click "Go"
4. Items become editable again

### Exporting to CSV

1. Filter items as needed
2. Select items with checkboxes
3. Choose **"Export selected items to CSV"**
4. Click "Go"
5. File downloads as `price_list_items.csv`

## Management Commands

### Import Prices

```bash
docker-compose exec web python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv
```

**Features:**
- Idempotent: Re-running won't create duplicates
- Handles: currency symbols ($), commas, whitespace
- Skips: Blank prices, missing required fields
- Creates: Suppliers and Ingredients automatically
- Updates: Existing items if supplier/sku/date match

**Import Report Shows:**
- Created count
- Updated count
- Skipped count with reasons

### Other Commands

```bash
# Run Django shell
docker-compose exec web python manage.py shell

# Create additional superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

## Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run with verbose output
docker-compose exec web pytest -v

# Run specific test file
docker-compose exec web pytest apps/core/tests/test_approval_readonly.py

# Run with coverage
docker-compose exec web pytest --cov=apps.core
```

**Test Coverage:**
- Approval workflow (approve, reject, unapprove)
- Audit field management (approved_by, approved_at)
- Read-only enforcement in admin
- Multiple approval scenarios

## Architecture Details

### Models

**Supplier**
- name (CharField, required)
- country_code (2-letter code, optional)
- contact_email (optional)
- is_active (default True)
- Unique together: (name, country_code)

**Ingredient**
- name (CharField, case-insensitive unique)
- aliases (TextField, semicolon-separated)
- is_active (default True)
- Database constraint: `LOWER(name)` must be unique

**PriceListItem**
- supplier (FK → Supplier, CASCADE)
- ingredient (FK → Ingredient, SET_NULL, optional)
- sku (CharField, required)
- pack_size, uom (optional)
- price (Decimal, 12 digits, 2 decimal places)
- currency (default USD)
- effective_date (DateField, required)
- status (pending/approved/rejected, default pending)
- source_file (optional)
- approved_by (FK → User, SET_NULL)
- approved_at (DateTimeField)
- Index: (supplier, sku, effective_date)

### Approval Workflow

**States:**
1. **Pending** (default): Editable
2. **Approved**: Read-only price fields, audit trail set
3. **Rejected**: Editable

**Transitions:**
- Pending → Approved: Sets approved_by, approved_at
- Approved → Pending: Clears audit fields (Unapprove action)
- Any → Rejected: Status change only

**Read-only Fields (when approved):**
- price
- currency
- pack_size
- uom
- effective_date
- ingredient
- source_file

### Import Idempotency

**Key:** `(supplier, sku, effective_date)`

Uses Django's `update_or_create()`:
- If match found: Updates price, pack_size, etc.
- If no match: Creates new record
- Guarantees: No duplicates even if CSV imported multiple times

### N+1 Query Prevention

Admin queryset uses:
```python
queryset.select_related('supplier', 'ingredient', 'approved_by')
```

**Result:** Single query instead of N+3 queries when listing items

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps

# Restart database
docker-compose restart db

# View database logs
docker-compose logs db
```

### Migration Errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

### Import Command Not Found

```bash
# Verify __init__.py files exist
ls apps/core/management/__init__.py
ls apps/core/management/commands/__init__.py

# Restart web container
docker-compose restart web
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml
# For web: Change "8000:8000" to "8001:8000"
# For db: Change "5432:5432" to "5433:5432"

# Update DATABASE_URL in .env
DATABASE_URL=postgres://postgres:postgres@db:5433/postgres
```

## Development Workflow

### Making Model Changes

```bash
# 1. Edit models.py
# 2. Create migration
docker-compose exec web python manage.py makemigrations

# 3. Apply migration
docker-compose exec web python manage.py migrate

# 4. Verify changes
docker-compose exec web python manage.py showmigrations
```

### Adding Admin Customizations

Edit `apps/core/admin.py`:
- Add `list_display` fields
- Add `list_filter` options
- Add custom admin actions
- Override `get_queryset()` for optimizations

### Creating Management Commands

1. Create file: `apps/core/management/commands/mycommand.py`
2. Implement `Command` class with `handle()` method
3. Run: `docker-compose exec web python manage.py mycommand`

## Production Considerations

**Security:**
- [ ] Change `SECRET_KEY` to random string
- [ ] Set `DEBUG=0`
- [ ] Add `ALLOWED_HOSTS` in settings
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS
- [ ] Set up proper user authentication

**Performance:**
- [ ] Use PostgreSQL connection pooling (pgbouncer)
- [ ] Add Redis for caching
- [ ] Enable Django query logging
- [ ] Set up monitoring (Sentry, DataDog)

**Database:**
- [ ] Regular backups
- [ ] Set up read replicas
- [ ] Monitor query performance
- [ ] Add database indexes as needed

## API Endpoints

Currently only admin interface is available:
- `/admin/` - Django Admin

Future additions could include:
- REST API with Django REST Framework
- GraphQL API
- Bulk import API endpoint

## Time Spent

**Total Development Time:** ~60 minutes

Breakdown:
- Code analysis: 10 min
- Model enhancements: 5 min
- Admin export feature: 10 min
- Test suite creation: 15 min
- Configuration & migrations: 10 min
- Documentation: 10 min

## Screencast Link

[TODO: Add screencast link showing:
- Docker setup and migration
- CSV import demonstration
- Admin workflow (approve/reject/unapprove)
- CSV export
- Test suite execution
- Trade-offs discussion]

## Trade-offs & Design Decisions

### 1. Case-Insensitive Ingredient Names
**Decision:** Use database constraint with `LOWER(name)`
**Why:** Prevents duplicates like "Tomato" and "tomato" at DB level
**Trade-off:** Requires PostgreSQL or similar database

### 2. Idempotency Key
**Decision:** `(supplier, sku, effective_date)` as unique key
**Why:** Same product from same supplier on same date = update not create
**Trade-off:** Can't have multiple prices for same item on same date

### 3. Soft Approval State
**Decision:** Status field instead of separate approved_items table
**Why:** Simpler queries, easier to understand
**Trade-off:** Can't track approval history (only current state)

### 4. CSV Import Strategy
**Decision:** Management command + optional admin action
**Why:** Management command is more flexible for automation
**Trade-off:** Admin users need terminal access or separate admin action

### 5. Export vs Django-Import-Export
**Decision:** Custom CSV export action
**Why:** Full control, no external dependency complexity
**Trade-off:** Less feature-rich than django-import-export library

## Contact & Support

For questions or issues:
1. Check this README
2. Review `AI_USAGE.md` for implementation details
3. Check Django logs: `docker-compose logs -f web`
4. Review test suite: `apps/core/tests/`

## License

[Your License Here]
