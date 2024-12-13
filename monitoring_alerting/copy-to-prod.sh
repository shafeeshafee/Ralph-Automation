#!/bin/bash

# copy_to_prod.sh
# Script to copy monitoring_alerting files from dev to prod

# Set strict error handling
set -euo pipefail
IFS=$'\n\t'

# Define source and destination directories
SRC_DIR="$HOME/monitoring_alerting/dev"
DEST_DIR="$HOME/monitoring_alerting/prod"

# Define timestamp function for logging
timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Define logging function
log() {
    echo "[$(timestamp)] $1"
}

# Function to check if source directory exists
check_source_dir() {
    if [ ! -d "$SRC_DIR" ]; then
        log "ERROR: Source directory $SRC_DIR does not exist"
        exit 1
    fi
}

# Function to create backup of existing prod directory if it exists
create_backup() {
    if [ -d "$DEST_DIR" ]; then
        BACKUP_DIR="${DEST_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        log "Creating backup of existing prod directory to $BACKUP_DIR"
        cp -r "$DEST_DIR" "$BACKUP_DIR"
        if [ $? -eq 0 ]; then
            log "Backup created successfully"
        else
            log "ERROR: Backup creation failed"
            exit 1
        fi
    fi
}

# Function to create destination directory structure
create_dest_structure() {
    log "Creating destination directory structure"
    mkdir -p "$DEST_DIR"
    
    # Create necessary subdirectories
    for dir in alertmanager grafana prometheus reports scripts shared agent; do
        mkdir -p "$DEST_DIR/$dir"
    done
    
    # Create Grafana subdirectories
    mkdir -p "$DEST_DIR/grafana/provisioning/dashboards"
    mkdir -p "$DEST_DIR/grafana/provisioning/datasources"
    
    # Create agent subdirectories
    mkdir -p "$DEST_DIR/agent/analytics"
    mkdir -p "$DEST_DIR/agent/coordinator"
    mkdir -p "$DEST_DIR/agent/log-analytics"
    mkdir -p "$DEST_DIR/agent/monitoring"
    mkdir -p "$DEST_DIR/agent/reporting"
    mkdir -p "$DEST_DIR/agent/logs"
    mkdir -p "$DEST_DIR/agent/reports"
    mkdir -p "$DEST_DIR/agent/scripts"
}

# Function to copy files
copy_files() {
    log "Starting file copy process"
    
    # Copy main configuration files
    log "Copying main configuration files"
    cp -r "$SRC_DIR/docker-compose.yml" "$DEST_DIR/"
    cp -r "$SRC_DIR/Dockerfile" "$DEST_DIR/"
    cp -r "$SRC_DIR/.env.example" "$DEST_DIR/"
    
    # Copy service-specific configurations
    log "Copying service configurations"
    cp -r "$SRC_DIR/prometheus/"* "$DEST_DIR/prometheus/"
    cp -r "$SRC_DIR/alertmanager/"* "$DEST_DIR/alertmanager/"
    cp -r "$SRC_DIR/grafana/"* "$DEST_DIR/grafana/"
    
    # Copy agent files
    log "Copying agent files"
    cp -r "$SRC_DIR/agent/"* "$DEST_DIR/agent/"
    
    # Copy shared files
    log "Copying shared files"
    cp -r "$SRC_DIR/shared/"* "$DEST_DIR/shared/"
    
    # Copy scripts
    log "Copying scripts"
    cp -r "$SRC_DIR/scripts/"* "$DEST_DIR/scripts/"
    
    # Set appropriate permissions
    log "Setting permissions"
    find "$DEST_DIR" -type f -exec chmod 644 {} \;
    find "$DEST_DIR" -type d -exec chmod 755 {} \;
    
    # Make scripts executable
    find "$DEST_DIR/scripts" -type f -name "*.sh" -exec chmod +x {} \;
    find "$DEST_DIR/agent/scripts" -type f -name "*.sh" -exec chmod +x {} \;
}

# Function to verify the copy
verify_copy() {
    log "Verifying copy process"
    
    # Check essential files
    essential_files=(
        "docker-compose.yml"
        "Dockerfile"
        "prometheus/prometheus.yml"
        "alertmanager/alertmanager.yml"
        "grafana/provisioning/datasources/prometheus.yaml"
    )
    
    for file in "${essential_files[@]}"; do
        if [ ! -f "$DEST_DIR/$file" ]; then
            log "ERROR: Essential file $file is missing in production directory"
            exit 1
        fi
    done
    
    log "Copy verification completed successfully"
}

# Main execution
main() {
    log "Starting dev to prod copy process"
    
    # Check source directory
    check_source_dir
    
    # Create backup if prod exists
    create_backup
    
    # Create destination structure
    create_dest_structure
    
    # Copy files
    copy_files
    
    # Verify copy
    verify_copy
    
    log "Copy process completed successfully"
}

# Execute main function
main

# Exit successfully
exit 0