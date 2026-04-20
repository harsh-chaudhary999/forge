# forge-product.md — Product Configuration Template
# Copy this file to your product root and fill in every field.
# The conductor, eval drivers, and deploy drivers read this file.
# No TBD values allowed — leave a field blank rather than writing TBD.

## Identity

name: my-product
description: One sentence describing what this product does.
version: 1.0.0

# When true, conductor State 4b requires approved ~/forge/brain/prds/<task-id>/qa/manual-test-cases.csv
# (qa-prd-analysis + qa-manual-test-cases-from-prd) and [P4.0-QA-CSV] BEFORE [P4.0-EVAL-YAML] and TDD RED.
forge_qa_csv_before_eval: false

## Repos

# List every repo in this product. Order determines default merge order.
repos:
  - name: backend
    path: ~/projects/my-product/backend
    language: typescript          # typescript | python | go | java | ruby | rust
    framework: express            # express | fastapi | gin | spring | rails | actix
    role: api-server              # api-server | worker | scheduler | gateway

  - name: web
    path: ~/projects/my-product/web
    language: typescript
    framework: react
    role: web-frontend

  - name: app
    path: ~/projects/my-product/app
    language: swift               # swift | kotlin | react-native | flutter
    framework: swiftui            # swiftui | uikit | jetpack-compose | rn | flutter
    role: mobile-app

  - name: infra
    path: ~/projects/my-product/infra
    language: terraform
    framework: terraform
    role: infrastructure

## Services (per repo)

# Defines how to start, stop, and health-check each service.
# Used by deploy-driver-local-process and eval-product-stack-up.
services:
  backend:
    port: 3000
    start: npm run dev
    stop: kill $(lsof -t -i:3000)
    health_check: curl -sf http://localhost:3000/health
    build: npm run build
    test: npm test
    env_file: .env.local

  web:
    port: 5173
    start: npm run dev
    stop: kill $(lsof -t -i:5173)
    health_check: curl -sf http://localhost:5173
    build: npm run build
    test: npm test
    env_file: .env.local

  app:
    platform: ios                 # ios | android | both
    simulator_id: default         # for iOS: xcrun simctl list devices
    emulator_id: emulator-5554    # for Android: adb devices
    bundle_id: com.myproduct.app  # iOS bundle ID
    package_name: com.myproduct  # Android package name
    build: xcodebuild -scheme MyProduct -destination 'id=default'
    test: xcodebuild test -scheme MyProductTests -destination 'id=default'

## Infrastructure

# Connection details for each infrastructure component.
# Used by eval drivers. Credentials should reference env vars, not hardcoded values.
infrastructure:
  mysql:
    host: localhost
    port: 3306
    database: myproduct_dev
    user: "${DB_USER}"
    password: "${DB_PASSWORD}"
    reset: |
      mysql -u $DB_USER -p$DB_PASSWORD myproduct_dev < db/schema.sql
      mysql -u $DB_USER -p$DB_PASSWORD myproduct_dev < db/seeds.sql

  redis:
    host: localhost
    port: 6379
    database: 0
    password: "${REDIS_PASSWORD}"    # leave empty string if no auth
    reset: redis-cli FLUSHDB

  kafka:
    bootstrap_servers: localhost:9092
    topics:
      - name: user.events
        partitions: 3
        replication_factor: 1
      - name: order.events
        partitions: 3
        replication_factor: 1
    reset: |
      kafka-topics.sh --delete --topic ".*" --bootstrap-server localhost:9092
      kafka-topics.sh --create --topic user.events --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092

  elasticsearch:
    host: localhost
    port: 9200
    username: "${ES_USERNAME}"
    password: "${ES_PASSWORD}"
    indices:
      - name: products
        mapping_file: infra/es/products-mapping.json
      - name: users
        mapping_file: infra/es/users-mapping.json
    reset: |
      curl -X DELETE "localhost:9200/products,users"
      curl -X PUT "localhost:9200/products" -H "Content-Type: application/json" -d @infra/es/products-mapping.json

## Contracts

# Paths to contract files — read by spec-reviewer and council negotiation.
contracts:
  rest_api: docs/contracts/api.md          # REST API contract (endpoints, request/response schemas)
  database_schema: docs/contracts/db.md    # Database schema contract (tables, columns, indexes)
  event_bus: docs/contracts/events.md      # Event bus contract (topics, payload schemas)
  cache: docs/contracts/cache.md           # Cache contract (key patterns, TTLs, invalidation)
  search: docs/contracts/search.md         # Search contract (index mappings, query patterns)

## Merge Order

# Order in which PRs must be merged for coordinated releases.
# Backend contracts must land before frontend/mobile consumes them.
merge_order:
  - infra       # schema migrations first
  - backend     # API implementation second
  - web         # frontend third
  - app         # mobile last (or parallel with web)

## Deploy Strategy

# Used by deploy drivers.
deploy:
  strategy: local-process         # local-process | docker-compose | systemd | pm2-ssh
  docker_compose_file: docker-compose.yml   # if strategy=docker-compose
  systemd_service: myproduct      # if strategy=systemd
  pm2_app_name: myproduct         # if strategy=pm2-ssh
  ssh_host: "${DEPLOY_HOST}"      # if strategy=pm2-ssh or systemd
  ssh_user: "${DEPLOY_USER}"

## Brain

# Where Forge stores decisions, retrospectives, and patterns for this product.
brain_path: ~/forge/brain/my-product
