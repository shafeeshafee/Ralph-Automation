#!/bin/bash

# analyze_findings.sh
# This script analyzes findings from logs and monitoring data

set -e  # Exit on any error

# Configure logging
log_file="/app/logs/analysis.log"
reports_dir="${REPORTS_DIR:-/app/reports}"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$log_file"
    echo "[$timestamp] $1"
}

analyze_metrics() {
    local metrics_file="$1"
    local analysis_result={}
    
    if [ -f "$metrics_file" ]; then
        log "Analyzing metrics from $metrics_file"
        
        # Count total number of metrics
        metric_count=$(grep -c "metric" "$metrics_file" || echo "0")
        
        # Count warnings and errors
        warning_count=$(grep -c "warning" "$metrics_file" || echo "0")
        error_count=$(grep -c "error" "$metrics_file" || echo "0")
        
        # Create analysis summary
        analysis_result=$(cat <<EOF
{
    "analysis_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "metrics_analyzed": $metric_count,
    "warnings_found": $warning_count,
    "errors_found": $error_count,
    "status": "completed"
}
EOF
)
    else
        log "Warning: Metrics file $metrics_file not found"
        analysis_result='{
            "status": "error",
            "message": "Metrics file not found"
        }'
    fi
    
    echo "$analysis_result"
}

analyze_logs() {
    local log_file="$1"
    local analysis_result={}
    
    if [ -f "$log_file" ]; then
        log "Analyzing logs from $log_file"
        
        # Analyze log patterns
        total_lines=$(wc -l < "$log_file")
        error_lines=$(grep -c "ERROR" "$log_file" || echo "0")
        warning_lines=$(grep -c "WARNING" "$log_file" || echo "0")
        
        # Calculate error percentage
        error_percentage=$(awk "BEGIN {print ($error_lines/$total_lines)*100}")
        
        # Create analysis summary
        analysis_result=$(cat <<EOF
{
    "analysis_timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "total_log_entries": $total_lines,
    "error_entries": $error_lines,
    "warning_entries": $warning_lines,
    "error_percentage": $error_percentage,
    "status": "completed"
}
EOF
)
    else
        log "Warning: Log file $log_file not found"
        analysis_result='{
            "status": "error",
            "message": "Log file not found"
        }'
    fi
    
    echo "$analysis_result"
}

main() {
    log "Starting analysis process"
    
    # Create timestamp for unique filenames
    timestamp=$(date +%Y%m%d_%H%M%S)
    
    # Create reports directory if it doesn't exist
    mkdir -p "$reports_dir"
    
    # Analyze metrics and logs
    metrics_analysis=$(analyze_metrics "$reports_dir/monitoring_report.json")
    log_analysis=$(analyze_logs "/app/logs/app.log")
    
    # Combine analyses
    combined_analysis=$(cat <<EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "metrics_analysis": $metrics_analysis,
    "log_analysis": $log_analysis
}
EOF
)
    
    # Save combined analysis
    analysis_file="$reports_dir/analysis_${timestamp}.json"
    echo "$combined_analysis" > "$analysis_file"
    
    log "Analysis completed and saved to $analysis_file"
    
    # Return the latest analysis file path
    echo "$analysis_file"
}

# Execute main function
main "$@"