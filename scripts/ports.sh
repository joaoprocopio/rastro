#!/usr/bin/env bash
# Gives this worktree free random ports and its own compose project, so its stack runs beside other stacks.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

set_env() {
  local file=$1 pair
  shift
  for pair in "$@"; do
    sed -i "/^${pair%%=*}=/d" "$file"
    echo "${pair%%=*}='${pair#*=}'" >>"$file"
  done
}

# A second run keeps the ports, because a running stack still publishes them.
if ! grep -qs '^COMPOSE_PROJECT_NAME=' .env; then
  # The range sits below the kernel's ephemeral ports, which outgoing connections take at any moment.
  read -r api postgres clickhouse_native clickhouse_http otel_healthcheck otel_http grafana <<<"$(
    seq 20000 32767 | grep -vxFf <(ss -Hltn | awk '{print $4}' | sed 's/.*://') | shuf -n 7 | xargs
  )"
  project=rastro-$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9\n' -)

  [ -f .env ] || cp .env.example .env

  set_env .env \
    "COMPOSE_PROJECT_NAME=$project" \
    "RASTRO_API_PORT=$api" \
    "RASTRO_POSTGRES_PORT=$postgres" \
    "RASTRO_CLICKHOUSE_NATIVE_PORT=$clickhouse_native" \
    "RASTRO_CLICKHOUSE_HTTP_PORT=$clickhouse_http" \
    "RASTRO_OTEL_HEALTHCHECK_PORT=$otel_healthcheck" \
    "RASTRO_OTEL_HTTP_PORT=$otel_http" \
    "RASTRO_GRAFANA_PORT=$grafana" \
    "RASTRO_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:$postgres/postgres" \
    "RASTRO_OTEL_HTTP_ENDPOINT=http://localhost:$otel_http"
fi

grep -E '^(COMPOSE_PROJECT_NAME|[A-Z_]+_PORT)=' .env
echo "commands on the host: uv run --env-file .env ..."
