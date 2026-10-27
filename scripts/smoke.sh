#!/usr/bin/env bash
# Runs the compose stack against a new database and calls every route of /api/v1/auth/.
set -euo pipefail

cd "$(dirname "$0")/.."

database="rastro_smoke_$$"
url="postgresql+psycopg://postgres:postgres@postgres:5432/$database"
api="http://localhost:8000"
work="$(mktemp -d)"
running_before="$(docker compose ps --services --status running)"

cleanup() {
  docker compose exec -T postgres psql -qU postgres -c "DROP DATABASE IF EXISTS $database WITH (FORCE)" >/dev/null || true
  started="$(comm -13 <(sort <<<"$running_before") <(docker compose config --services | sort))"
  # shellcheck disable=SC2086
  [ -n "$started" ] && docker compose rm -sf $started >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

cat >"$work/override.yaml" <<EOF
services:
  migrate: {environment: {RASTRO_POSTGRES_URL: "$url"}}
  api: {environment: {RASTRO_POSTGRES_URL: "$url"}}
  worker: {environment: {RASTRO_POSTGRES_URL: "$url"}}
EOF

docker compose up -d --wait postgres
docker compose exec -T postgres psql -qU postgres -c "CREATE DATABASE $database"
docker compose -f compose.yaml -f "$work/override.yaml" up --build -d --wait

for _ in $(seq 30); do curl -sf -o /dev/null "$api/api/v1/auth/csrf" && break; sleep 1; done

fail() { echo "smoke: $1" >&2; exit 1; }
expect() { [ "$2" = "$3" ] || fail "$1: expected $3, got $2"; }
cookie() { sed -nE "s/^set-cookie: $1=([^;]*).*/\1/Ip" "$2" | tr -d '\r'; }

status="$(curl -s -o /dev/null -w '%{http_code}' "$api/openapi.json")"
expect "GET /openapi.json" "$status" 404

curl -s -D "$work/csrf" -o /dev/null "$api/api/v1/auth/csrf"
csrf="$(cookie rastro_csrf "$work/csrf")"
[ -n "$csrf" ] || fail "GET /csrf set no rastro_csrf cookie"

post() {
  local data="${3:-}"
  [ -n "$data" ] || data='{}'
  curl -s -D "$work/headers" -o "$work/body" -w '%{http_code}' \
    -H "Cookie: rastro_csrf=$csrf${2:+; rastro_session=$2}" -H "X-CSRF-Token: $csrf" \
    -H 'content-type: application/json' -d "$data" "$api/api/v1/auth/$1"
}

credentials='{"email":"smoke@x.com","password":"password123"}'
expect "POST /register" "$(post register "" '{"email":"smoke@x.com","password":"password123","display_name":"Smoke"}')" 201
expect "POST /session/start" "$(post session/start "" "$credentials")" 204
session="$(cookie rastro_session "$work/headers")"
[ -n "$session" ] || fail "POST /session/start set no rastro_session cookie"

body="$(curl -s -H "Cookie: rastro_session=$session" "$api/api/v1/auth/session")"
expect "GET /session" "$body" '{"email":"smoke@x.com","display_name":"Smoke"}'

expect "POST /session/end" "$(post session/end "$session")" 204

status="$(curl -s -o /dev/null -w '%{http_code}' -H "Cookie: rastro_csrf=$csrf" \
  -H 'X-CSRF-Token: wrong' -H 'content-type: application/json' -d '{}' "$api/api/v1/auth/session/start")"
expect "POST /session/start with a wrong CSRF header" "$status" 403

docker compose ps --services --status running | grep -qx worker || fail "the worker is not running"
echo "smoke: ok"
