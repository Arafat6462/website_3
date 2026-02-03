#!/bin/bash

###############################################################################
# Production Readiness Validation Script
#
# Automates verification of production deployment prerequisites.
# Run this before deploying to production to catch issues early.
#
# Usage: bash scripts/validate_production.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Print functions
print_header() {
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  PRODUCTION READINESS VALIDATION                             ║${NC}"
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

###############################################################################
# VALIDATION FUNCTIONS
###############################################################################

check_environment_file() {
    print_section "Environment Configuration"
    
    if [ -f ".env.production" ]; then
        print_pass "Production environment file exists"
        
        # Check critical variables
        source .env.production 2>/dev/null || true
        
        if [ "$DEBUG" = "False" ]; then
            print_pass "DEBUG is False"
        else
            print_fail "DEBUG should be False in production"
        fi
        
        if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" != "your-secret-key-here" ]; then
            print_pass "SECRET_KEY is configured"
        else
            print_fail "SECRET_KEY not properly configured"
        fi
        
        if [ -n "$ALLOWED_HOSTS" ] && [ "$ALLOWED_HOSTS" != "*" ]; then
            print_pass "ALLOWED_HOSTS is configured"
        else
            print_fail "ALLOWED_HOSTS should be set to specific domains"
        fi
        
        if [ -n "$DB_PASSWORD" ] && [ "$DB_PASSWORD" != "changeme" ]; then
            print_pass "Database password is configured"
        else
            print_fail "Database password should be changed from default"
        fi
        
        if [ -n "$REDIS_PASSWORD" ]; then
            print_pass "Redis password is configured"
        else
            print_warn "Redis password not set (recommended for production)"
        fi
        
    else
        print_fail "Production environment file not found (.env.production)"
        echo "  Create it with: cp .env.production.example .env.production"
    fi
}

check_file_permissions() {
    print_section "File Permissions"
    
    if [ -f ".env.production" ]; then
        PERMS=$(stat -c "%a" .env.production 2>/dev/null || stat -f "%A" .env.production 2>/dev/null)
        if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
            print_pass "Environment file has restrictive permissions ($PERMS)"
        else
            print_warn "Environment file permissions should be 600 (current: $PERMS)"
            echo "  Fix with: chmod 600 .env.production"
        fi
    fi
    
    if [ -f "scripts/deploy.sh" ]; then
        if [ -x "scripts/deploy.sh" ]; then
            print_pass "Deployment script is executable"
        else
            print_fail "Deployment script is not executable"
            echo "  Fix with: chmod +x scripts/*.sh"
        fi
    fi
}

check_docker() {
    print_section "Docker & Docker Compose"
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
        print_pass "Docker installed (version $DOCKER_VERSION)"
    else
        print_fail "Docker is not installed"
        echo "  Install with: curl -fsSL https://get.docker.com | sh"
    fi
    
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
        print_pass "Docker Compose installed (version $COMPOSE_VERSION)"
    else
        print_fail "Docker Compose is not installed"
        echo "  Install with: sudo apt install docker-compose-plugin"
    fi
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_pass "Docker daemon is running"
    else
        print_fail "Docker daemon is not running"
        echo "  Start with: sudo systemctl start docker"
    fi
}

check_required_files() {
    print_section "Required Files"
    
    local files=(
        "Dockerfile.prod"
        "docker-compose.prod.yml"
        "src/gunicorn.conf.py"
        "nginx/nginx.conf"
        "nginx/conf.d/app.conf"
        "scripts/backup.sh"
        "scripts/deploy.sh"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_pass "$file exists"
        else
            print_fail "$file is missing"
        fi
    done
}

check_ssl_certificates() {
    print_section "SSL Certificates"
    
    if [ -d "nginx/ssl" ]; then
        if [ -f "nginx/ssl/cert.pem" ] && [ -f "nginx/ssl/key.pem" ]; then
            print_pass "SSL certificates found"
            
            # Check certificate expiry
            if command -v openssl &> /dev/null; then
                EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/cert.pem 2>/dev/null | cut -d= -f2)
                if [ -n "$EXPIRY" ]; then
                    print_pass "Certificate expires: $EXPIRY"
                fi
            fi
        else
            print_warn "SSL certificates not found in nginx/ssl/"
            echo "  Generate with Let's Encrypt or upload commercial certificate"
        fi
    else
        print_warn "SSL directory not found (nginx/ssl/)"
        echo "  Create and add certificates: mkdir -p nginx/ssl"
    fi
}

check_directories() {
    print_section "Required Directories"
    
    local dirs=(
        "logs/django"
        "logs/nginx"
        "backups"
        "media"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_pass "$dir directory exists"
        else
            print_warn "$dir directory missing (will be created automatically)"
        fi
    done
}

check_docker_compose_syntax() {
    print_section "Docker Compose Validation"
    
    if [ -f "docker-compose.prod.yml" ]; then
        if docker compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
            print_pass "docker-compose.prod.yml syntax is valid"
        else
            print_fail "docker-compose.prod.yml has syntax errors"
            echo "  Check with: docker compose -f docker-compose.prod.yml config"
        fi
    fi
}

check_network_ports() {
    print_section "Network Port Availability"
    
    local ports=(80 443)
    
    for port in "${ports[@]}"; do
        if command -v netstat &> /dev/null; then
            if netstat -tuln | grep -q ":$port "; then
                print_warn "Port $port is already in use"
                echo "  Check with: sudo netstat -tuln | grep :$port"
            else
                print_pass "Port $port is available"
            fi
        elif command -v ss &> /dev/null; then
            if ss -tuln | grep -q ":$port "; then
                print_warn "Port $port is already in use"
                echo "  Check with: sudo ss -tuln | grep :$port"
            else
                print_pass "Port $port is available"
            fi
        else
            print_warn "Cannot check port $port (netstat/ss not available)"
        fi
    done
}

check_disk_space() {
    print_section "System Resources"
    
    # Check available disk space
    DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}')
    DISK_PERCENT=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$DISK_PERCENT" -lt 80 ]; then
        print_pass "Disk space available: $DISK_AVAIL ($DISK_PERCENT% used)"
    else
        print_warn "Disk space low: $DISK_AVAIL available ($DISK_PERCENT% used)"
    fi
    
    # Check available memory
    if command -v free &> /dev/null; then
        MEM_AVAIL=$(free -h | awk 'NR==2 {print $7}')
        print_pass "Memory available: $MEM_AVAIL"
    fi
}

check_git_status() {
    print_section "Git Repository"
    
    if [ -d ".git" ]; then
        print_pass "Git repository detected"
        
        # Check for uncommitted changes
        if [ -z "$(git status --porcelain)" ]; then
            print_pass "No uncommitted changes"
        else
            print_warn "Uncommitted changes detected"
            echo "  Commit or stash changes before deployment"
        fi
        
        # Check current branch
        BRANCH=$(git rev-parse --abbrev-ref HEAD)
        print_pass "Current branch: $BRANCH"
        
        if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
            print_pass "On production branch"
        else
            print_warn "Not on main/master branch"
        fi
    else
        print_warn "Not a git repository"
    fi
}

check_security_settings() {
    print_section "Security Configuration"
    
    if [ -f ".env.production" ]; then
        source .env.production 2>/dev/null || true
        
        if [ "$SECURE_SSL_REDIRECT" = "True" ]; then
            print_pass "SSL redirect enabled"
        else
            print_warn "SSL redirect not enabled"
        fi
        
        if [ -n "$CORS_ALLOWED_ORIGINS" ] && [ "$CORS_ALLOWED_ORIGINS" != "*" ]; then
            print_pass "CORS restricted to specific origins"
        else
            print_fail "CORS should be restricted to frontend domain"
        fi
        
        if [ "$SESSION_COOKIE_SECURE" = "True" ]; then
            print_pass "Secure session cookies enabled"
        else
            print_warn "Session cookies should be secure in production"
        fi
    fi
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    print_header
    
    check_environment_file
    check_file_permissions
    check_docker
    check_required_files
    check_ssl_certificates
    check_directories
    check_docker_compose_syntax
    check_network_ports
    check_disk_space
    check_git_status
    check_security_settings
    
    # Print summary
    echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  VALIDATION SUMMARY                                          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${GREEN}✓ Passed:${NC} $PASSED"
    echo -e "${YELLOW}⚠ Warnings:${NC} $WARNINGS"
    echo -e "${RED}✗ Failed:${NC} $FAILED"
    
    echo ""
    
    if [ $FAILED -gt 0 ]; then
        echo -e "${RED}❌ Production readiness validation FAILED${NC}"
        echo -e "${RED}   Fix the issues above before deploying to production${NC}\n"
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Production readiness validation PASSED with WARNINGS${NC}"
        echo -e "${YELLOW}   Review warnings above before deploying${NC}\n"
        exit 0
    else
        echo -e "${GREEN}✅ Production readiness validation PASSED${NC}"
        echo -e "${GREEN}   Ready for production deployment${NC}\n"
        exit 0
    fi
}

# Run main function
main
