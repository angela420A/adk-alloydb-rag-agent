

# -----------------------------------------------------------------------------
# Setup & Verification
# -----------------------------------------------------------------------------
verify-env:
	@if [ -z "$$APP_ENV" ]; then \
		echo "❌ Error: APP_ENV is not set. Please run: export APP_ENV=<dev|staging|prod>"; \
		exit 1; \
	fi
	@echo "🔍 Environment: .env.$${APP_ENV}"
	@set -a; . ./.env.$${APP_ENV}; set +a; \
	echo "  APP_ENV              : $$APP_ENV"; \
	echo "  GOOGLE_CLOUD_PROJECT : $$GOOGLE_CLOUD_PROJECT"; \
	echo "  GOOGLE_CLOUD_LOCATION: $$GOOGLE_CLOUD_LOCATION"; \
	echo "  ROOT_MODEL           : $$ROOT_MODEL"


# -----------------------------------------------------------------------------
# ADK
# -----------------------------------------------------------------------------
# Run the agent locally with specified environment configuration
run-agent:
	uv run --env-file .env.${APP_ENV} adk web


# -----------------------------------------------------------------------------
# MCP & ToolBox
# -----------------------------------------------------------------------------
# Download MCP Toolbox for Database Binary file
# Note: Check the latest version in https://github.com/googleapis/mcp-toolbox/releases
# Note: Also if are in Linux or Windows OS, then check the link above, to change the OS/Architecture
VERSION = v1.9.0
# Command in root path
toolbox-dw:
	curl -L -o toolbox https://storage.googleapis.com/mcp-toolbox-for-databases/${VERSION}/darwin/arm64/toolbox
	chmod +x toolbox


# Use Toolbox on local device
toolbox:
	set -a; . .env.${APP_ENV}; set +a; \
	./toolbox --config "gamaplay_agent/mcps/toolbox_alloydb.yaml"

toolbox-ui:
	set -a; . .env.${APP_ENV}; set +a; \
	./toolbox --config "gamaplay_agent/mcps/toolbox_alloydb.yaml" --ui

toolbox-port:
	set -a; . .env.${APP_ENV}; set +a; \
	./toolbox --config "gamaplay_agent/mcps/toolbox_alloydb.yaml" --port 7000


# -----------------------------------------------------------------------------
# Deploy Agent App to Agent Runtime
# -----------------------------------------------------------------------------
agent-deploy-dry:
	uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate > gamaplay_agent/utils/.requirements.txt 2>/dev/null && \
	set -a; . ./.env.$${APP_ENV}; set +a; \
	uv run --env-file .env.$${APP_ENV} -m gamaplay_agent.utils.deploy --dry-run

agent-deploy:
	uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate > gamaplay_agent/utils/.requirements.txt 2>/dev/null && \
	set -a; . ./.env.$${APP_ENV}; set +a; \
	uv run --env-file .env.$${APP_ENV} -m gamaplay_agent.utils.deploy
		