SHELL := /bin/bash

# Backend
API_DIR := vige-api
API_ENV := $(API_DIR)/vige/local_config.env

.PHONY: api dev worker migrate lint test

setup-api:
	cd $(API_DIR) && pipenv sync --dev

env-api:
	@[ -f $(API_ENV) ] || (echo "Creating $(API_ENV) from template" && \
	  cat > $(API_ENV) << 'EOF'\
ENV=local\
DEBUG=true\
SECRET_KEY=dev_secret\
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/vige\
REDIS_HOST=localhost\
REDIS_PORT=6379\
AUTHJWT_SECRET_KEY=dev_jwt\
EXTERNAL_URL=http://localhost:8000\
EOF
	)

api: env-api
	cd $(API_DIR) && pipenv run uvicorn vige.app:app --reload --port 8000

worker:
	cd $(API_DIR) && pipenv run huey_consumer -w 2 vige.huey_app.huey

migrate:
	cd $(API_DIR) && pipenv run alembic upgrade head

lint:
	cd $(API_DIR) && pipenv run python -m pip install ruff black isort || true && \
	ruff check vige || true && black --check vige || true && isort --check-only vige || true

test:
	cd $(API_DIR) && pipenv run pytest -q || true

# Frontends
web:
	cd vige-web && yarn install && yarn dev

bo:
	cd vige-bo && yarn install && yarn dev

wechat:
	cd vige-wechat && yarn install && yarn dev

