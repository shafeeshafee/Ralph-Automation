#!/bin/bash
# /opt/monitoring/scripts/maintenance/backup.sh

# Configuration
BACKUP_DIR="/backup/monitoring"
RETENTION_DAYS=30
PROMETHEUS_DATA="/var/lib/prometheus"
GRAFANA_DATA="/var/lib/grafana"
CONFIG_DIR="/opt/monitoring"
TODAY=$(date +%Y%m%d)
LOG_FILE="/var/log/monitoring/backup.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Create backup directories
create_backup_dirs() {
    mkdir -p "${BACKUP_DIR}/{prometheus,grafana,configs,logs}"
    chmod 700 "${BACKUP_DIR}"
}

# Backup Prometheus data
backup_prometheus() {
    log "Starting Prometheus backup..."
    
    # Snapshot Prometheus data using API
    curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
    
    # Wait for snapshot to complete
    sleep 10
    
    # Copy snapshot
    SNAPSHOT_DIR=$(ls -td ${PROMETHEUS_DATA}/snapshots/* | head -1)
    tar czf "${BACKUP_DIR}/prometheus/prometheus_data_${TODAY}.tar.gz" -C ${SNAPSHOT_DIR} .
    
    # Backup configs
    tar czf "${BACKUP_DIR}/prometheus/prometheus_config_${TODAY}.tar.gz" /etc/prometheus/
    
    log "Prometheus backup completed"
}

# Backup Grafana
backup_grafana() {
    log "Starting Grafana backup..."
    
    systemctl stop grafana-server
    
    # Backup Grafana data
    tar czf "${BACKUP_DIR}/grafana/grafana_data_${TODAY}.tar.gz" ${GRAFANA_DATA}
    
    # Backup Grafana configs
    tar czf "${BACKUP_DIR}/grafana/grafana_config_${TODAY}.tar.gz" /etc/grafana/
    
    systemctl start grafana-server
    
    log "Grafana backup completed"
}

# Backup ML models and configs
backup_ml_components() {
    log "Starting ML components backup..."
    
    tar czf "${BACKUP_DIR}/configs/ml_models_${TODAY}.tar.gz" ${CONFIG_DIR}/python/models/
    
    log "ML components backup completed"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    find ${BACKUP_DIR} -type f -mtime +${RETENTION_DAYS} -delete
    
    log "Cleanup completed"
}

# Upload to remote storage (example with AWS S3)
upload_to_remote() {
    log "Uploading backups to remote storage..."
    
    aws s3 sync ${BACKUP_DIR} s3://${BACKUP_BUCKET}/monitoring/${TODAY}/
    
    log "Remote upload completed"
}

# Main backup script
main() {
    log "Starting backup process..."
    
    create_backup_dirs
    backup_prometheus
    backup_grafana
    backup_ml_components
    cleanup_old_backups
    upload_to_remote
    
    log "Backup process completed successfully"
}

# Run main function
main
