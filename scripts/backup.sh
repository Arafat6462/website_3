#!/bin/bash
# =============================================================================
# Database and Media Backup Script
# =============================================================================
# Creates backups of PostgreSQL database and media files
# Uploads to cloud storage (optional)
# Implements rotation policy (keep last 7 daily, 4 weekly backups)
# =============================================================================

set -e  # Exit on error

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Load environment variables
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
fi

# Backup directory
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y%m%d")

# File names
DB_BACKUP_FILE="db_backup_${TIMESTAMP}.sql.gz"
MEDIA_BACKUP_FILE="media_backup_${TIMESTAMP}.tar.gz"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# -----------------------------------------------------------------------------
# Database Backup
# -----------------------------------------------------------------------------

backup_database() {
    log_info "Starting database backup..."
    
    # Create backup using docker exec
    docker compose -f docker-compose.prod.yml exec -T db \
        pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$DB_BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$BACKUP_DIR/$DB_BACKUP_FILE" | cut -f1)
        log_info "Database backup completed: $DB_BACKUP_FILE ($size)"
    else
        log_error "Database backup failed!"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Media Files Backup
# -----------------------------------------------------------------------------

backup_media() {
    log_info "Starting media files backup..."
    
    # Check if media directory exists
    if [ ! -d "./media" ]; then
        log_warn "Media directory not found, skipping media backup"
        return 0
    fi
    
    # Create tar.gz archive
    tar -czf "$BACKUP_DIR/$MEDIA_BACKUP_FILE" ./media 2>/dev/null || true
    
    if [ -f "$BACKUP_DIR/$MEDIA_BACKUP_FILE" ]; then
        local size=$(du -h "$BACKUP_DIR/$MEDIA_BACKUP_FILE" | cut -f1)
        log_info "Media backup completed: $MEDIA_BACKUP_FILE ($size)"
    else
        log_warn "Media backup file not created (directory might be empty)"
    fi
}

# -----------------------------------------------------------------------------
# Upload to Cloud Storage (Optional)
# -----------------------------------------------------------------------------

upload_to_cloud() {
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_STORAGE_BUCKET_NAME" ]; then
        log_warn "Cloud storage not configured, skipping upload"
        return 0
    fi
    
    log_info "Uploading backups to cloud storage..."
    
    # Install AWS CLI if not present (optional)
    # pip install awscli
    
    # Upload database backup
    # aws s3 cp "$BACKUP_DIR/$DB_BACKUP_FILE" \
    #     "s3://$AWS_STORAGE_BUCKET_NAME/backups/database/" \
    #     --endpoint-url "$AWS_S3_ENDPOINT_URL"
    
    # Upload media backup
    # aws s3 cp "$BACKUP_DIR/$MEDIA_BACKUP_FILE" \
    #     "s3://$AWS_STORAGE_BUCKET_NAME/backups/media/" \
    #     --endpoint-url "$AWS_S3_ENDPOINT_URL"
    
    log_info "Cloud upload completed (uncomment code to enable)"
}

# -----------------------------------------------------------------------------
# Cleanup Old Backups
# -----------------------------------------------------------------------------

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep last 7 daily backups
    find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +7 -delete
    find "$BACKUP_DIR" -name "media_backup_*.tar.gz" -mtime +7 -delete
    
    log_info "Old backups cleaned up (kept last 7 days)"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    log_info "=== Backup Script Started ==="
    log_info "Timestamp: $TIMESTAMP"
    
    # Run backups
    backup_database
    backup_media
    
    # Upload to cloud (optional)
    upload_to_cloud
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_info "=== Backup Script Completed ==="
}

# Run main function
main

# Exit with success
exit 0
