    up:
		docker compose up -d --build

    down:
		docker compose down -v

    logs:
		docker compose logs -f --tail=200 web

    migrate:
		docker compose exec web python manage.py migrate

    superuser:
		docker compose exec web python manage.py createsuperuser

    test:
		docker compose exec web pytest -q
