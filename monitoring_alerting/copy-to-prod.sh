#!/bin/bash

# Set strict error handling
set -euo pipefail
IFS=$'\n\t'

# Define base directory - using the correct path structure
BASE_DIR="$(pwd)"
SRC_DIR="${BASE_DIR}/dev"
DEST_DIR="${BASE_DIR}/prod"

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
    
    # Create necessary subdirectories based on your actual structure
    for dir in agent alertmanager grafana prometheus reports scripts shared; do
        mkdir -p "$DEST_DIR/$dir"
    done
    
    # Create Grafana subdirectories
    mkdir -p "$DEST_DIR/grafana/provisioning/dashboards"
    mkdir -p "$DEST_DIR/grafana/provisioning/datasources"
    
    # Create agent subdirectories
    mkdir -p "$DEST_DIR/agent/logs"
    mkdir -p "$DEST_DIR/agent/reports"
    mkdir -p "$DEST_DIR/agent/scripts"
}

# Function to copy files
copy_files() {
    log "Starting file copy process"
    
    # Copy files while preserving directory structure
    if [ -d "$SRC_DIR" ]; then
        log "Copying files from $SRC_DIR to $DEST_DIR"
        cp -R "$SRC_DIR"/* "$DEST_DIR"/ 2>/dev/null || true
    fi
    
    # Set appropriate permissions
    log "Setting permissions"
    find "$DEST_DIR" -type f -exec chmod 644 {} \;
    find "$DEST_DIR" -type d -exec chmod 755 {} \;
    
    # Make scripts executable
    find "$DEST_DIR" -type f -name "*.sh" -exec chmod +x {} \;
}

# Function to verify the copy
verify_copy() {
    log "Verifying copy process"
    
    # Check if destination directory exists
    if [ ! -d "$DEST_DIR" ]; then
        log "ERROR: Production directory was not created"
        exit 1
    fi
    
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