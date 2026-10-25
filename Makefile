# Short names for the commands used every day.
# Run `make` or `make help` to list them.

COMPOSE := docker compose -f compose/compose.yaml
PYTHON_SERVICES := gateway orders mock-bank

.DEFAULT_GOAL := help
.PHONY: help install up down clean ps logs seed load smoke lint test test-python test-java

help: ## List the commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

install: ## Install every Python service's packages into .venv
	uv sync --all-packages

up: ## Build and start the whole system, and wait until it is healthy
	$(COMPOSE) up --build --detach --wait

down: ## Stop the system; the database keeps its data
	$(COMPOSE) down

clean: ## Stop the system and delete the database's data
	$(COMPOSE) down --volumes

ps: ## Show each container and its health
	$(COMPOSE) ps

logs: ## Follow the logs of every service
	$(COMPOSE) logs --follow --tail 50

seed: ## Load the synthetic data: 200 products, 1,000,000 orders, 200,000 charges
	$(COMPOSE) exec -T postgres psql -q -v ON_ERROR_STOP=1 -U orders -d orders < scripts/seed/orders.sql > /dev/null
	$(COMPOSE) exec -T postgres psql -q -v ON_ERROR_STOP=1 -U payments -d payments < scripts/seed/payments.sql > /dev/null
	$(COMPOSE) exec -T redis redis-cli DEL products:all > /dev/null
	@echo "Seeded."

load: ## Send steady traffic (override with RATE=20 DURATION=10m)
	$(COMPOSE) --profile load run --rm loadgen

smoke: ## One request through every service, to prove the flow works
	./scripts/smoke.sh

lint: ## Check the Python code's style and formatting
	uvx ruff check .
	uvx ruff format --check .

test: test-python test-java ## Run every test

test-python: ## Run the Python tests, one service at a time
	@for service in $(PYTHON_SERVICES); do \
		echo "== $$service"; \
		uv run --directory services/$$service pytest -q || exit 1; \
	done

test-java: ## Run the payments tests
	cd services/payments && ./mvnw -q -B test
