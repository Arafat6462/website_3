#!/bin/bash
# =============================================================================
# Production Deployment Script
# =============================================================================
# Automates the deployment process:
# 1. Pull latest code
# 2. Build Docker images
# 3. Run database migrations
# 4. Collect static files
# 5. Restart services with zero downtime
# =============================================================================

set -e  # Exit on error

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment mode
MODE="${1:-update}"  # update, fresh, rollback

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}==>${NC} $1"
}

# -----------------------------------------------------------------------------
# Pre-deployment Checks
# -----------------------------------------------------------------------------

pre_deployment_checks() {
    log_step "Running pre-deployment checks..."
    
    # Check if .env.production exists
    if [ ! -f .env.production ]; then
        log_error ".env.production file not found!"
        log_info "Copy .env.production.example to .env.production and configure it"
        exit 1
    fi
    
    # Check if docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running!"
        exit 1
    fi
    
    # Check if docker-compose.prod.yml exists
    if [ ! -f docker-compose.prod.yml ]; then
        log_error "docker-compose.prod.yml not found!"
        exit 1
    fi
    
    log_info "Pre-deployment checks passed ✓"
}

# -----------------------------------------------------------------------------
# Backup Current State
# -----------------------------------------------------------------------------

backup_before_deploy() {
    log_step "Creating backup before deployment..."
    
    # Run backup script if it exists
    if [ -f scripts/backup.sh ]; then
        bash scripts/backup.sh
    else
        log_warn "Backup script not found, skipping backup"
    fi
}

# -----------------------------------------------------------------------------
# Pull Latest Code
# -----------------------------------------------------------------------------

pull_code() {
    log_step "Pulling latest code from repository..."
    
    # Uncomment to enable git pull
    # git pull origin main
    
    log_info "Code updated (git pull disabled, uncomment to enable)"
}

# -----------------------------------------------------------------------------
# Build Docker Images
# -----------------------------------------------------------------------------

build_images() {
    log_step "Building Docker images..."
    
    docker compose -f docker-compose.prod.yml build --no-cache web
    
    log_info "Docker images built ✓"
}

# -----------------------------------------------------------------------------
# Database Migration
# -----------------------------------------------------------------------------

run_migrations() {
    log_step "Running database migrations..."
    
    docker compose -f docker-compose.prod.yml run --rm web \
        python manage.py migrate --noinput
    
    log_info "Migrations completed ✓"
}

# -----------------------------------------------------------------------------
# Collect Static Files
# -----------------------------------------------------------------------------

collect_static() {
    log_step "Collecting static files..."
    
    docker compose -f docker-compose.prod.yml run --rm web \
        python manage.py collectstatic --noinput
    
    log_info "Static files collected ✓"
}

# -----------------------------------------------------------------------------
# Restart Services
# -----------------------------------------------------------------------------

restart_services() {
    log_step "Restarting services..."
    
    # Restart with zero downtime
    docker compose -f docker-compose.prod.yml up -d --no-deps --build web
    
    # Wait for health check
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check service health
    if docker compose -f docker-compose.prod.yml ps | grep -q "unhealthy"; then
        log_error "Some services are unhealthy!"
        docker compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    log_info "Services restarted successfully ✓"
}

# -----------------------------------------------------------------------------
# Fresh Deployment
# -----------------------------------------------------------------------------

fresh_deployment() {
    log_step "Starting fresh deployment..."
    
    # Stop and remove all containers
    docker compose -f docker-compose.prod.yml down
    
    # Remove volumes (WARNING: This deletes data!)
    log_warn "This will delete all data. Press Ctrl+C to cancel..."
    sleep 5
    
    docker compose -f docker-compose.prod.yml down -v
    
    # Build images
    build_images
    
    # Start services
    docker compose -f docker-compose.prod.yml up -d
    
    # Wait for database
    sleep 10
    
    # Run migrations
    run_migrations
    
    # Collect static
    collect_static
    
    # Create superuser
    log_step "Create superuser (optional):"
    docker compose -f docker-compose.prod.yml exec web \
        python manage.py createsuperuser || true
    
    log_info "Fresh deployment completed ✓"
}

# -----------------------------------------------------------------------------
# Update Deployment
# -----------------------------------------------------------------------------

update_deployment() {
    log_step "Starting update deployment..."
    
    # Backup current state
    backup_before_deploy
    
    # Pull latest code
    pull_code
    
    # Build images
    build_images
    
    # Run migrations
    run_migrations
    
    # Collect static
    collect_static
    
    # Restart services
    restart_services
    
    log_info "Update deployment completed ✓"
}

# -----------------------------------------------------------------------------
# Rollback Deployment
# -----------------------------------------------------------------------------

rollback_deployment() {
    log_step "Starting rollback..."
    
    # This is a placeholder - implement your rollback strategy
    log_warn "Rollback not implemented yet"
    log_info "To rollback manually:"
    log_info "1. Restore database from backup"
    log_info "2. Checkout previous git commit"
    log_info "3. Run: bash scripts/deploy.sh update"
}

# -----------------------------------------------------------------------------
# Post-deployment Tasks
# -----------------------------------------------------------------------------

post_deployment() {
    log_step "Running post-deployment tasks..."
    
    # Show service status
    log_info "Service Status:"
    docker compose -f docker-compose.prod.yml ps
    
    # Show logs
    log_info "Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=50 web
    
    log_info "Deployment completed successfully! 🚀"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    log_info "========================================="
    log_info "   E-Commerce Deployment Script"
    log_info "========================================="
    log_info "Mode: $MODE"
    log_info ""
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Execute based on mode
    case "$MODE" in
        fresh)
            fresh_deployment
            ;;
        update)
            update_deployment
            ;;
        rollback)
            rollback_deployment
            ;;
        *)
            log_error "Invalid mode: $MODE"
            log_info "Usage: $0 {fresh|update|rollback}"
            exit 1
            ;;
    esac
    
    # Post-deployment tasks
    post_deployment
}

# Run main function
main

exit 0
