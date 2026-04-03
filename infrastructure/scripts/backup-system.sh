#!/bin/bash
# Automated backup system for Ponder production environment
# Supports database, file system, and configuration backups with retention policies

set -e

# Configuration
BACKUP_BASE_DIR="/var/backups/ponder"
RETENTION_DAYS=30
RETENTION_WEEKS=12
RETENTION_MONTHS=12
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
ENCRYPTION_KEY_FILE="/etc/ponder/backup.key"
LOG_FILE="/var/log/ponder/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Initialize backup environment
init_backup_env() {
    log "INFO" "Initializing backup environment..."
    
    # Create backup directories
    mkdir -p "$BACKUP_BASE_DIR"/{daily,weekly,monthly,temp}
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Create backup directories with proper permissions
    chmod 750 "$BACKUP_BASE_DIR"
    chmod 640 "$LOG_FILE" 2>/dev/null || touch "$LOG_FILE" && chmod 640 "$LOG_FILE"
    
    # Generate encryption key if it doesn't exist
    if [[ ! -f "$ENCRYPTION_KEY_FILE" ]]; then
        log "INFO" "Generating backup encryption key..."
        mkdir -p "$(dirname "$ENCRYPTION_KEY_FILE")"
        openssl rand -base64 32 > "$ENCRYPTION_KEY_FILE"
        chmod 600 "$ENCRYPTION_KEY_FILE"
        log "SUCCESS" "Backup encryption key generated"
    fi
    
    log "SUCCESS" "Backup environment initialized"
}

# Database backup function
backup_database() {
    local backup_type=$1
    local backup_dir="$BACKUP_BASE_DIR/$backup_type"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$backup_dir/database_${timestamp}.sql"
    
    log "INFO" "Starting database backup ($backup_type)..."
    
    # Load environment variables
    source /opt/ponder/.env.production 2>/dev/null || {
        log "ERROR" "Could not load production environment variables"
        return 1
    }
    
    # Create database backup
    if docker-compose -f /opt/ponder/docker-compose.yml exec -T db pg_dump \
        -U "${POSTGRES_USER}" \
        -h localhost \
        -p 5432 \
        --verbose \
        --clean \
        --if-exists \
        --create \
        "${POSTGRES_DB}" > "$backup_file"; then
        
        log "SUCCESS" "Database backup created: $backup_file"
        
        # Compress and encrypt backup
        if compress_and_encrypt "$backup_file"; then
            rm "$backup_file"  # Remove uncompressed file
            log "SUCCESS" "Database backup compressed and encrypted"
        else
            log "ERROR" "Failed to compress and encrypt database backup"
            return 1
        fi
    else
        log "ERROR" "Database backup failed"
        return 1
    fi
}

# File system backup function
backup_filesystem() {
    local backup_type=$1
    local backup_dir="$BACKUP_BASE_DIR/$backup_type"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$backup_dir/filesystem_${timestamp}.tar"
    
    log "INFO" "Starting filesystem backup ($backup_type)..."
    
    # Directories to backup
    local backup_paths=(
        "/opt/ponder/backend/app/data"
        "/opt/ponder/frontend/public"
        "/opt/ponder/infrastructure/nginx/conf.d"
        "/opt/ponder/.env.production"
        "/etc/ponder"
    )
    
    # Create filesystem backup
    if tar -cf "$backup_file" \
        --exclude='*.log' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        "${backup_paths[@]}" 2>/dev/null; then
        
        log "SUCCESS" "Filesystem backup created: $backup_file"
        
        # Compress and encrypt backup
        if compress_and_encrypt "$backup_file"; then
            rm "$backup_file"  # Remove uncompressed file
            log "SUCCESS" "Filesystem backup compressed and encrypted"
        else
            log "ERROR" "Failed to compress and encrypt filesystem backup"
            return 1
        fi
    else
        log "ERROR" "Filesystem backup failed"
        return 1
    fi
}

# Docker volumes backup function
backup_docker_volumes() {
    local backup_type=$1
    local backup_dir="$BACKUP_BASE_DIR/$backup_type"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    log "INFO" "Starting Docker volumes backup ($backup_type)..."
    
    # Backup PostgreSQL data volume
    local postgres_backup="$backup_dir/postgres_data_${timestamp}.tar.gz"
    if docker run --rm \
        -v ponder_postgres_data:/data \
        -v "$backup_dir":/backup \
        alpine tar czf "/backup/postgres_data_${timestamp}.tar.gz" -C /data .; then
        
        log "SUCCESS" "PostgreSQL volume backup created"
        
        # Encrypt the backup
        if encrypt_file "$postgres_backup"; then
            rm "$postgres_backup"
            log "SUCCESS" "PostgreSQL volume backup encrypted"
        fi
    else
        log "ERROR" "PostgreSQL volume backup failed"
    fi
    
    # Backup Redis data volume
    local redis_backup="$backup_dir/redis_data_${timestamp}.tar.gz"
    if docker run --rm \
        -v ponder_redis_data:/data \
        -v "$backup_dir":/backup \
        alpine tar czf "/backup/redis_data_${timestamp}.tar.gz" -C /data .; then
        
        log "SUCCESS" "Redis volume backup created"
        
        # Encrypt the backup
        if encrypt_file "$redis_backup"; then
            rm "$redis_backup"
            log "SUCCESS" "Redis volume backup encrypted"
        fi
    else
        log "ERROR" "Redis volume backup failed"
    fi
}

# Compress and encrypt function
compress_and_encrypt() {
    local file=$1
    local compressed_file="${file}.gz"
    local encrypted_file="${compressed_file}.enc"
    
    # Compress
    if gzip "$file"; then
        # Encrypt
        if openssl enc -aes-256-cbc -salt -in "$compressed_file" -out "$encrypted_file" -pass file:"$ENCRYPTION_KEY_FILE"; then
            rm "$compressed_file"
            return 0
        else
            log "ERROR" "Encryption failed for $compressed_file"
            return 1
        fi
    else
        log "ERROR" "Compression failed for $file"
        return 1
    fi
}

# Encrypt file function
encrypt_file() {
    local file=$1
    local encrypted_file="${file}.enc"
    
    if openssl enc -aes-256-cbc -salt -in "$file" -out "$encrypted_file" -pass file:"$ENCRYPTION_KEY_FILE"; then
        return 0
    else
        log "ERROR" "Encryption failed for $file"
        return 1
    fi
}

# Upload to S3 function
upload_to_s3() {
    local backup_type=$1
    local backup_dir="$BACKUP_BASE_DIR/$backup_type"
    
    if [[ -z "$S3_BUCKET" ]]; then
        log "INFO" "S3 backup not configured, skipping upload"
        return 0
    fi
    
    log "INFO" "Uploading $backup_type backups to S3..."
    
    # Upload encrypted backups to S3
    if aws s3 sync "$backup_dir" "s3://$S3_BUCKET/ponder-backups/$backup_type/" \
        --exclude "*" \
        --include "*.enc" \
        --storage-class STANDARD_IA; then
        
        log "SUCCESS" "$backup_type backups uploaded to S3"
    else
        log "ERROR" "Failed to upload $backup_type backups to S3"
        return 1
    fi
}

# Cleanup old backups function
cleanup_old_backups() {
    log "INFO" "Cleaning up old backups..."
    
    # Daily backups - keep for RETENTION_DAYS
    find "$BACKUP_BASE_DIR/daily" -name "*.enc" -mtime +$RETENTION_DAYS -delete
    
    # Weekly backups - keep for RETENTION_WEEKS * 7 days
    local weekly_days=$((RETENTION_WEEKS * 7))
    find "$BACKUP_BASE_DIR/weekly" -name "*.enc" -mtime +$weekly_days -delete
    
    # Monthly backups - keep for RETENTION_MONTHS * 30 days
    local monthly_days=$((RETENTION_MONTHS * 30))
    find "$BACKUP_BASE_DIR/monthly" -name "*.enc" -mtime +$monthly_days -delete
    
    log "SUCCESS" "Old backups cleaned up"
}

# Health check function
health_check() {
    log "INFO" "Performing backup system health check..."
    
    local issues=0
    
    # Check backup directories
    for dir in daily weekly monthly; do
        if [[ ! -d "$BACKUP_BASE_DIR/$dir" ]]; then
            log "ERROR" "Backup directory missing: $BACKUP_BASE_DIR/$dir"
            ((issues++))
        fi
    done
    
    # Check encryption key
    if [[ ! -f "$ENCRYPTION_KEY_FILE" ]]; then
        log "ERROR" "Encryption key file missing: $ENCRYPTION_KEY_FILE"
        ((issues++))
    fi
    
    # Check disk space
    local available_space=$(df "$BACKUP_BASE_DIR" | awk 'NR==2 {print $4}')
    local required_space=1048576  # 1GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        log "WARNING" "Low disk space for backups: ${available_space}KB available"
        ((issues++))
    fi
    
    # Check Docker services
    if ! docker-compose -f /opt/ponder/docker-compose.yml ps | grep -q "Up"; then
        log "ERROR" "Some Docker services are not running"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "SUCCESS" "Backup system health check passed"
        return 0
    else
        log "ERROR" "Backup system health check failed with $issues issues"
        return 1
    fi
}

# Restore function
restore_backup() {
    local backup_file=$1
    local restore_type=$2
    
    if [[ -z "$backup_file" || -z "$restore_type" ]]; then
        log "ERROR" "Usage: restore_backup <backup_file> <database|filesystem|volumes>"
        return 1
    fi
    
    log "WARNING" "Starting restore process for $restore_type from $backup_file"
    log "WARNING" "This will overwrite existing data. Continue? (y/N)"
    read -r confirmation
    
    if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
        log "INFO" "Restore cancelled"
        return 0
    fi
    
    # Decrypt and decompress backup
    local temp_dir="$BACKUP_BASE_DIR/temp/restore_$$"
    mkdir -p "$temp_dir"
    
    local decrypted_file="$temp_dir/backup.gz"
    local restored_file="$temp_dir/backup"
    
    # Decrypt
    if openssl enc -aes-256-cbc -d -in "$backup_file" -out "$decrypted_file" -pass file:"$ENCRYPTION_KEY_FILE"; then
        log "SUCCESS" "Backup decrypted"
    else
        log "ERROR" "Failed to decrypt backup"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Decompress
    if gunzip "$decrypted_file"; then
        log "SUCCESS" "Backup decompressed"
    else
        log "ERROR" "Failed to decompress backup"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Restore based on type
    case $restore_type in
        "database")
            log "INFO" "Restoring database..."
            if docker-compose -f /opt/ponder/docker-compose.yml exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "$restored_file"; then
                log "SUCCESS" "Database restored successfully"
            else
                log "ERROR" "Database restore failed"
                rm -rf "$temp_dir"
                return 1
            fi
            ;;
        "filesystem")
            log "INFO" "Restoring filesystem..."
            if tar -xf "$restored_file" -C /; then
                log "SUCCESS" "Filesystem restored successfully"
            else
                log "ERROR" "Filesystem restore failed"
                rm -rf "$temp_dir"
                return 1
            fi
            ;;
        *)
            log "ERROR" "Unknown restore type: $restore_type"
            rm -rf "$temp_dir"
            return 1
            ;;
    esac
    
    # Cleanup
    rm -rf "$temp_dir"
    log "SUCCESS" "Restore completed"
}

# Main backup function
run_backup() {
    local backup_type=$1
    
    log "INFO" "Starting $backup_type backup process..."
    
    # Initialize environment
    init_backup_env
    
    # Run health check
    if ! health_check; then
        log "ERROR" "Health check failed, aborting backup"
        return 1
    fi
    
    # Perform backups
    local backup_success=true
    
    if ! backup_database "$backup_type"; then
        backup_success=false
    fi
    
    if ! backup_filesystem "$backup_type"; then
        backup_success=false
    fi
    
    if ! backup_docker_volumes "$backup_type"; then
        backup_success=false
    fi
    
    # Upload to S3 if configured
    if [[ "$backup_success" == "true" ]]; then
        upload_to_s3 "$backup_type"
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    if [[ "$backup_success" == "true" ]]; then
        log "SUCCESS" "$backup_type backup completed successfully"
        
        # Send success notification
        send_notification "SUCCESS" "$backup_type backup completed successfully"
        return 0
    else
        log "ERROR" "$backup_type backup completed with errors"
        
        # Send error notification
        send_notification "ERROR" "$backup_type backup completed with errors"
        return 1
    fi
}

# Send notification function
send_notification() {
    local status=$1
    local message=$2
    
    # Send to monitoring system if available
    if command -v curl &> /dev/null && [[ -n "${MONITORING_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$MONITORING_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"status\":\"$status\",\"message\":\"$message\",\"service\":\"backup-system\",\"timestamp\":\"$(date -Iseconds)\"}" \
            &>/dev/null || true
    fi
    
    # Log notification
    log "INFO" "Notification sent: $status - $message"
}

# Main script logic
case "${1:-daily}" in
    "daily")
        run_backup "daily"
        ;;
    "weekly")
        run_backup "weekly"
        ;;
    "monthly")
        run_backup "monthly"
        ;;
    "health")
        init_backup_env
        health_check
        ;;
    "restore")
        restore_backup "$2" "$3"
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {daily|weekly|monthly|health|restore <backup_file> <type>|cleanup}"
        echo ""
        echo "Backup types:"
        echo "  daily   - Create daily backup"
        echo "  weekly  - Create weekly backup"
        echo "  monthly - Create monthly backup"
        echo "  health  - Check backup system health"
        echo "  restore - Restore from backup file"
        echo "  cleanup - Clean up old backups"
        exit 1
        ;;
esac