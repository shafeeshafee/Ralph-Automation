#!/bin/bash
# /opt/monitoring/scripts/maintenance/maintenance.sh

# Configuration
LOG_FILE="/var/log/monitoring/maintenance.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Check system resources
check_resources() {
    log "Checking system resources..."
    
    # Check disk space
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ ${DISK_USAGE} -gt 85 ]; then
        log "WARNING: High disk usage: ${DISK_USAGE}%"
    fi
    
    # Check memory usage
    FREE_MEM=$(free -m | awk '/^Mem:/{print $4}')
    if [ ${FREE_MEM} -lt 1024 ]; then
        log "WARNING: Low memory available: ${FREE_MEM}MB"
    fi
}

# Clean up old data
cleanup_data() {
    log "Starting data cleanup..."
    
    # Clean up old Prometheus data (if not using retention settings)
    find ${PROMETHEUS_DATA} -type f -name "*.tmp" -delete
    
    # Clean up old ML model files
    find ${CONFIG_DIR}/python/models -type f -mtime +30 -name "*.pkl" -delete
    
    # Clean up old log files
    find /var/log/monitoring -type f -mtime +90 -delete
}

# Check and rotate logs
rotate_logs() {
    log "Rotating logs..."
    
    # Force log rotation
    logrotate -f /etc/logrotate.d/monitoring
}

# Verify services
check_services() {
    log "Verifying services..."
    
    services=("prometheus" "grafana-server" "ml-forecasting" "node_exporter")
    
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet $service; then
            log "WARNING: ${service} is not running"
            systemctl restart ${service}
            log "Attempted to restart ${service}"
        fi
    done
}

# Verify ML models
verify_ml_models() {
    log "Verifying ML models..."
    
    # Check if ML predictions are being generated
    LAST_PREDICTION=$(find ${CONFIG_DIR}/data -type f -name "prediction_*.json" -mmin -60)
    if [ -z "$LAST_PREDICTION" ]; then
        log "WARNING: No recent ML predictions found"
    fi
}

# Main maintenance function
main() {
    log "Starting maintenance tasks..."
    
    check_resources
    cleanup_data
    rotate_logs
    check_services
    verify_ml_models
    
    log "Maintenance tasks completed"
}

# Run main function
main