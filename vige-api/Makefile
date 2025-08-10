default: clean test

install:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

run:
	uvicorn vige.app:app --host 192.168.1.5 --port 8000 --reload --log-level debug

worker:
	DEBUG=0 huey_consumer vige.huey_app.huey

upgrade-db:
	alembic upgrade head

config-db:
	alembic -c vige/migrations/alembic.ini current

db:
	alembic revision --autogenerate -m "$(filter-out $@,$(MAKECMDGOALS))"

lint:
	flake8

test .coverage:
	pytest --cov-report=term:skip-covered --cov=. --reset-db .

htmlcov: .coverage
	@coverage html --skip-covered
	@echo "open htmlcov/index.html"

clean:
	rm -f .coverage
	rm -fr htmlcov

# ci: clean lint test htmlcov
ci: clean test

smtp-server:
	python -m smtpd -n -c DebuggingServer localhost:10025

%:
	@:

TRANSLATIONS=vige/translations
DOMAIN=messages

babel-extract:
	pybabel extract -F $(TRANSLATIONS)/messages.cfg --no-location -k lazy_gettext -o $(TRANSLATIONS)/messages.pot vige

babel-init: babel-extract
	pybabel init -D $(DOMAIN) -i $(TRANSLATIONS)/messages.pot -d $(TRANSLATIONS) -l $(LANG)

babel-update: babel-extract
	pybabel update -D $(DOMAIN) -i $(TRANSLATIONS)/messages.pot --no-wrap -d $(TRANSLATIONS)
babel-compile:
	pybabel compile -D $(DOMAIN) -d $(TRANSLATIONS)

# create admin
create-role:
	python -m vige.cli bo_create_role -n admin

create-user:
	python -m vige.cli bo_create_user -n admin

set-role:
	python -m vige.cli bo_set_role -u admin -r admin

set-perm:
	python -m vige.cli bo_set_perm -r admin -p all
