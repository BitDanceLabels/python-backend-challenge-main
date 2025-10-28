# Testing Checklist - Django Supplier Price List

Use this checklist to verify all features are working correctly before submission.

## Pre-Testing Setup

```bash
# Navigate to project directory
cd "c:\Users\Nhut\OneDrive\CVNhutPham-16102025\python-backend-challenge-main (1)\python-backend-challenge-main"

# Start Docker services
docker-compose up -d

# Wait for database (check logs)
docker-compose logs -f db
# Wait until you see: "database system is ready to accept connections"
# Press Ctrl+C

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
# Username: admin
# Password: admin123
```

## 1. CSV Import Testing

### First Import (Should Create Records)

```bash
docker-compose exec web python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv
```

**Expected Output:**
```
Import complete: created=4, updated=0, skipped=1
```

- [ ] Command runs without errors
- [ ] Created count is 4
- [ ] Skipped count is 1 (blank price row)

### Second Import (Should Update, Not Duplicate)

```bash
docker-compose exec web python manage.py import_prices --file ./samples/SAMPLE_SUPPLIER_PRICES.csv
```

**Expected Output:**
```
Import complete: created=0, updated=4, skipped=1
```

- [ ] Created count is 0 (no duplicates)
- [ ] Updated count is 4
- [ ] Skipped count is still 1

**Idempotency verified! ✅**

## 2. Admin Interface Testing

### Access Admin

1. Open browser: http://localhost:8000/admin
2. Login with: admin / admin123

- [ ] Login successful
- [ ] Admin dashboard loads

### Supplier Admin

Navigate to: Suppliers

- [ ] List view shows: name, country_code, is_active
- [ ] Can filter by: is_active, country_code
- [ ] Search box works for supplier name
- [ ] Can create new supplier
- [ ] Can edit existing supplier

Expected Suppliers:
- Acme Foods
- FreshCo

### Ingredient Admin

Navigate to: Ingredients

- [ ] List view shows: name, is_active
- [ ] Search works for name
- [ ] Search works for aliases
- [ ] Can create new ingredient
- [ ] Can edit existing ingredient

Expected Ingredients:
- Tomato (aliases: tomato;pomodoro or tomate)
- Onion (brown) (aliases: onion;cebolla;cebola)
- Garlic (aliases: garlic;ail or garlic)
- Basil (aliases: basil)

### PriceListItem Admin

Navigate to: Price list items

**List Display Check:**
- [ ] Columns shown: supplier, sku, ingredient, price, currency, effective_date, status
- [ ] All 4 imported items visible

**Filter Check:**
- [ ] Can filter by Supplier (Acme Foods, FreshCo)
- [ ] Can filter by Status (Pending, Approved, Rejected)
- [ ] Can filter by Currency (USD)

**Search Check:**
Test each search:
- [ ] Search "TOM-001" → finds Tomato item
- [ ] Search "Acme" → finds all Acme Foods items
- [ ] Search "Tomato" → finds tomato item
- [ ] Search "pomodoro" (alias) → finds tomato item ✅ KEY TEST
- [ ] Search "cebolla" (alias) → finds onion item ✅ KEY TEST

**Alias search working! ✅**

## 3. Approval Workflow Testing

### Approve Items

1. Select 2 items (e.g., TOM-001 and ONI-050)
2. Actions dropdown → "Approve selected items"
3. Click "Go"

- [ ] Success message appears
- [ ] Items show status "Approved"
- [ ] Click on approved item to edit

**Read-Only Check (Critical!):**
- [ ] Price field is read-only (grayed out)
- [ ] Currency field is read-only
- [ ] Pack size field is read-only
- [ ] UOM field is read-only
- [ ] Effective date field is read-only
- [ ] Ingredient field is read-only
- [ ] SKU and Supplier are still editable

**Read-only enforcement working! ✅**

### Reject Items

1. Select 1 pending item
2. Actions dropdown → "Reject selected items"
3. Click "Go"

- [ ] Success message appears
- [ ] Item shows status "Rejected"
- [ ] Can still edit price fields (not read-only)

### Unapprove Items

1. Select previously approved items
2. Actions dropdown → "Unapprove selected items"
3. Click "Go"

- [ ] Success message appears
- [ ] Items return to "Pending" status
- [ ] Price fields become editable again
- [ ] approved_by and approved_at cleared

**Unapprove working! ✅**

## 4. CSV Export Testing

1. Filter or select specific items
2. Check checkboxes for items to export
3. Actions dropdown → "Export selected items to CSV"
4. Click "Go"

- [ ] CSV file downloads automatically
- [ ] Filename is "price_list_items.csv"
- [ ] Open file - verify headers present
- [ ] Verify data is correct
- [ ] Check all fields included:
  - Supplier Name
  - SKU
  - Ingredient Name
  - Pack Size
  - UOM
  - Price
  - Currency
  - Effective Date
  - Status
  - Source File
  - Approved By
  - Approved At

**Export working! ✅**

## 5. Automated Test Suite

Run pytest:

```bash
docker-compose exec web pytest -v
```

**Expected Output:**
```
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_pending_item_is_editable PASSED
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_approval_sets_audit_fields PASSED
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_unapprove_clears_audit_fields PASSED
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_admin_readonly_logic PASSED
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_rejected_item_remains_editable PASSED
apps/core/tests/test_approval_readonly.py::TestApprovalReadOnly::test_multiple_approvals PASSED

6 passed
```

- [ ] All tests pass
- [ ] No errors or warnings

**Tests passing! ✅**

## 6. Edge Cases Testing

### Price Normalization

Import handles these correctly:
- [ ] "$3.20" → 3.20 (dollar sign removed)
- [ ] "  $1.75" → 1.75 (whitespace and $ removed)
- [ ] "" (blank) → skipped

### Duplicate Handling

- [ ] Same SKU, supplier, date → updates existing
- [ ] Different date → creates new record
- [ ] Different supplier → creates new record

### Alias Handling

- [ ] Semicolon-separated aliases work
- [ ] Search finds items by alias
- [ ] Multiple aliases per ingredient

## 7. Database Checks

### Case-Insensitive Ingredient Names

Try creating duplicate ingredients with different cases:

1. Admin → Ingredients → Add
2. Name: "Tomato" (already exists as "Tomato")
3. Try to save

- [ ] Error: "Unique constraint violation" or similar
- [ ] Can't create "tomato", "TOMATO", "ToMaTo" if "Tomato" exists

**Database constraint working! ✅**

### Foreign Key Relationships

1. Try to delete a Supplier that has PriceListItems
   - [ ] Should show warning about related items
   - [ ] CASCADE delete works

2. Try to delete an Ingredient that has PriceListItems
   - [ ] Should allow (SET_NULL)
   - [ ] PriceListItem.ingredient becomes null

## 8. Performance Checks

### N+1 Query Test

Check Django toolbar or logs:

1. Admin → Price list items (list view)
2. Check number of database queries

**Without select_related:** ~15 queries for 4 items
**With select_related:** ~3 queries total

- [ ] Query count is low (< 5 queries for list view)

**N+1 prevention working! ✅**

## 9. Documentation Verification

Check all files exist:

- [ ] `.env` file exists
- [ ] `.env.example` exists with comments
- [ ] `AI_USAGE.md` exists and complete
- [ ] `SUBMISSION_README.md` exists
- [ ] `SETUP_GUIDE.md` exists
- [ ] `IMPLEMENTATION_SUMMARY.md` exists
- [ ] `TESTING_CHECKLIST.md` exists (this file)

Check migrations:

- [ ] `apps/core/migrations/0001_initial.py` exists
- [ ] Migration includes case-insensitive constraint

Check tests:

- [ ] `apps/core/tests/test_approval_readonly.py` exists
- [ ] Contains 6+ test cases

Check __init__.py files:

- [ ] `apps/__init__.py`
- [ ] `apps/core/management/__init__.py`
- [ ] `apps/core/management/commands/__init__.py`
- [ ] `apps/core/tests/__init__.py`
- [ ] `apps/core/migrations/__init__.py`

## 10. Submission Readiness

### Code Quality

- [ ] No syntax errors
- [ ] No unused imports
- [ ] Consistent formatting
- [ ] Comments where needed
- [ ] No debug print statements

### Features Completeness

- [ ] All core features working (90 points)
- [ ] Bonus feature working (10 points)
- [ ] All hidden checks pass
- [ ] All tests pass

### Documentation

- [ ] Setup instructions clear
- [ ] AI usage disclosed
- [ ] Screencast recorded (TODO)

### Deliverables

- [ ] Working code
- [ ] Migrations included
- [ ] Tests passing
- [ ] Documentation complete
- [ ] .env.example provided
- [ ] AI_USAGE.md included
- [ ] Screencast link (TODO - add to SUBMISSION_README.md)

## Screencast Recording Checklist

Record 5-7 minute video showing:

1. **Setup (1 min)**
   - [ ] Show Docker compose up
   - [ ] Show migrations running
   - [ ] Show superuser creation

2. **Import (1 min)**
   - [ ] Run import command
   - [ ] Show output
   - [ ] Run import again (show idempotency)

3. **Admin Demo (2 min)**
   - [ ] Login to admin
   - [ ] Show list views
   - [ ] Demonstrate search (including alias search)
   - [ ] Show filters

4. **Approval Workflow (1 min)**
   - [ ] Approve items
   - [ ] Show read-only fields
   - [ ] Unapprove items

5. **Export (0.5 min)**
   - [ ] Export to CSV
   - [ ] Show downloaded file

6. **Tests (0.5 min)**
   - [ ] Run pytest
   - [ ] Show all passing

7. **Trade-offs Discussion (1 min)**
   - [ ] Explain idempotency key choice
   - [ ] Explain read-only approach
   - [ ] Mention performance optimizations

## Final Checks Before Submission

- [ ] All tests in this checklist passed
- [ ] Code committed (if using git)
- [ ] Project zipped (if submitting as zip)
- [ ] Screencast uploaded and link added to README
- [ ] Email draft prepared with:
  - Attached zip file or repo link
  - Time spent (~60 minutes)
  - Brief description
  - Screencast link

## Clean Up (After Testing)

```bash
# Stop containers
docker-compose down

# Remove volumes (if needed)
docker-compose down -v

# Remove images (if needed)
docker-compose down --rmi all
```

## Troubleshooting

### If tests fail:
```bash
docker-compose logs web
docker-compose exec web python manage.py check
```

### If import fails:
```bash
docker-compose exec web python manage.py shell
>>> from apps.core.models import Supplier, Ingredient, PriceListItem
>>> Supplier.objects.all()
>>> PriceListItem.objects.all()
```

### If admin doesn't work:
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart web
```

### If database connection fails:
```bash
docker-compose logs db
docker-compose restart db
```

## Success Criteria

✅ All checkboxes above are checked
✅ Score: 100/100 points
✅ Ready for submission

Good luck! 🚀
