.PHONY: dev build clean install db-up db-down test

# Development
install:
	pnpm install

dev:
	pnpm dev

# Database
db-up:
	docker-compose -f infra/docker-compose.yml up -d

db-down:
	docker-compose -f infra/docker-compose.yml down

db-migrate:
	pnpm db:migrate

db-studio:
	pnpm db:studio

# Build
build:
	pnpm build

# Clean
clean:
	pnpm clean

# Type checking
type-check:
	pnpm type-check

# Lint
lint:
	pnpm lint

# Test
test:
	pnpm test

# Full setup for new developer
setup: install db-up
	@echo "✅ Setup complete! Run 'make dev' to start development."
