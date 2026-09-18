#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# OneGov AI — Development Setup Script
# Run once after cloning the repo:  chmod +x scripts/setup.sh && ./scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()    { echo -e "${GREEN}[SETUP]${NC} $1"; }
warn()   { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
section(){ echo -e "\n${BLUE}══ $1 ══${NC}"; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
section "Checking prerequisites"

command -v docker  >/dev/null 2>&1 || error "Docker is not installed. Visit https://docs.docker.com/get-docker/"
command -v git     >/dev/null 2>&1 || error "Git is not installed."

DOCKER_RUNNING=$(docker info >/dev/null 2>&1 && echo "yes" || echo "no")
[ "$DOCKER_RUNNING" = "no" ] && error "Docker Desktop is not running. Please start it."

log "Docker: $(docker --version)"

# ── Environment files ─────────────────────────────────────────────────────────
section "Setting up environment files"

if [ ! -f ".env" ]; then
    cp .env.example .env
    log "Created root .env from .env.example"
else
    warn "Root .env already exists — skipping"
fi

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    log "Created backend/.env from .env.example"

    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")

    # Replace placeholder secrets
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/CHANGE_THIS_TO_A_RANDOM_64_CHAR_SECRET/$SECRET_KEY/" backend/.env
        sed -i '' "s/CHANGE_THIS_TO_A_DIFFERENT_RANDOM_64_CHAR_SECRET/$JWT_SECRET/" backend/.env
    else
        sed -i "s/CHANGE_THIS_TO_A_RANDOM_64_CHAR_SECRET/$SECRET_KEY/" backend/.env
        sed -i "s/CHANGE_THIS_TO_A_DIFFERENT_RANDOM_64_CHAR_SECRET/$JWT_SECRET/" backend/.env
    fi
    log "Generated secure random secrets"
else
    warn "backend/.env already exists — skipping"
fi

if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    log "Created frontend/.env.local"
else
    warn "frontend/.env.local already exists — skipping"
fi

# ── Docker compose ────────────────────────────────────────────────────────────
section "Starting Docker services"
log "Pulling images (this may take a few minutes on first run)..."
docker compose pull

log "Starting PostgreSQL and Redis..."
docker compose up -d postgres redis
log "Waiting for PostgreSQL to be healthy..."
until docker compose exec postgres pg_isready -U onegov >/dev/null 2>&1; do
    printf "."
    sleep 2
done
echo ""
log "PostgreSQL is ready ✓"

# ── Database migrations ───────────────────────────────────────────────────────
section "Running database migrations"
log "Starting backend service temporarily for migrations..."
docker compose up -d backend
sleep 5
log "Running Alembic migrations..."
docker compose exec backend alembic upgrade head
log "Migrations complete ✓"

# ── Database seeding ──────────────────────────────────────────────────────────
section "Seeding database"
docker compose exec backend python scripts/seed.py
log "Database seeded with sample data ✓"

# ── Ollama model ──────────────────────────────────────────────────────────────
section "Setting up Ollama (local AI)"
log "Starting Ollama service..."
docker compose up -d ollama
log "Pulling llama3.2 model (this downloads ~2GB — may take several minutes)..."
docker compose exec ollama ollama pull llama3.2 || warn "Could not pull llama3.2. You can pull it manually later."
log "Pulling nomic-embed-text for embeddings..."
docker compose exec ollama ollama pull nomic-embed-text || warn "Could not pull nomic-embed-text."

# ── Frontend dependencies ─────────────────────────────────────────────────────
section "Installing frontend dependencies"
if command -v node >/dev/null 2>&1; then
    log "Node.js: $(node --version)"
    cd frontend && npm install --legacy-peer-deps
    cd ..
    log "npm packages installed ✓"
else
    warn "Node.js not found locally — frontend deps will be installed inside Docker"
fi

# ── Start full stack ──────────────────────────────────────────────────────────
section "Starting full application"
docker compose up -d
sleep 5

# ── Done ──────────────────────────────────────────────────────────────────────
section "Setup complete! 🎉"
echo ""
echo -e "  ${GREEN}Frontend:${NC}       http://localhost:3000"
echo -e "  ${GREEN}Backend API:${NC}    http://localhost:8000"
echo -e "  ${GREEN}Swagger Docs:${NC}   http://localhost:8000/docs"
echo -e "  ${GREEN}Nginx:${NC}          http://localhost:80"
echo ""
echo -e "  ${BLUE}Admin login:${NC}    admin@onegov.ai / Admin@1234!"
echo -e "  ${BLUE}Test login:${NC}     user@onegov.ai  / User@1234!"
echo ""
echo -e "  Run ${YELLOW}docker compose logs -f backend${NC} to watch backend logs"
echo -e "  Run ${YELLOW}docker compose down${NC} to stop all services"
echo ""
