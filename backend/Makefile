.PHONY: build up logs sh test down migrate smoke wait-for-health

# Build the app Docker image
build:
	docker compose build

# Start all services in detached mode
up:
	docker compose up -d

# Follow app service logs
logs:
	docker compose logs -f app

# Open a shell in the app container
sh:
	docker exec -it llmpaa-app /bin/bash

# Run pytest inside the app container
test:
	docker compose run --rm app pytest

# Stop and remove all containers and volumes
down:
	docker compose down -v

# Run database migrations
migrate:
	@echo "Running database migrations..."
	docker compose exec app alembic upgrade head
	@echo "✓ Migrations complete"

# Wait for health endpoint to be ready
wait-for-health:
	@echo "Waiting for application to be ready..."
	@./.scripts/wait_for.sh http://localhost:8000/health 60 2

# Smoke test: wait for health, then send test request
smoke: wait-for-health
	@echo ""
	@echo "Running smoke test..."
	@echo "Sending test request to /assess endpoint..."
	@response=$$(curl -X POST http://localhost:8000/assess \
		-H "Content-Type: application/json" \
		-H "x-api-key: $${API_KEY:-dev-key}" \
		-d '{"transcript":"Rep: Hi, how can I help you today?\nBuyer: I am looking for a solution to improve our sales process.\nRep: What specific challenges are you facing?\nBuyer: Our team struggles with follow-ups and tracking customer interactions.\nRep: That sounds frustrating. How does this impact your revenue?\nBuyer: We estimate we are losing about 20% of potential deals.\nRep: If you could solve this, what would that mean for your business?\nBuyer: It would significantly increase our close rate and revenue.","metadata":{"rep_id":"test-rep","buyer_id":"test-buyer"}}' \
		-s -w "\nHTTP_STATUS:%{http_code}"); \
	body=$$(echo "$$response" | sed '$$d'); \
	status=$$(echo "$$response" | tail -1 | cut -d: -f2); \
	echo "$$body" | jq '.'; \
	echo ""; \
	echo "HTTP Status: $$status"; \
	if [ "$$status" = "200" ]; then \
		echo "✓ Smoke test complete"; \
	else \
		echo "✗ Smoke test failed with status $$status"; \
		exit 1; \
	fi
