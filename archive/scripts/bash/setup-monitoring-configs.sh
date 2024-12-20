#!/bin/bash
# 1. setup_monitoring_configs.sh
# Creates necessary directories and configurations
setup_monitoring_configs() {
    echo "Setting up monitoring configurations..."
    
    # Create directories
    sudo mkdir -p /etc/prometheus/rules
    sudo mkdir -p /opt/monitoring/scripts
    sudo mkdir -p /opt/monitoring/configs
    
    # Create Prometheus config
    cat << 'EOF' | sudo tee /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - 'rules/alert_rules.yml'
  - 'rules/recording_rules.yml'

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'node_.*'
        action: keep

  - job_name: 'ralph'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
EOF

    # Create alert rules
    cat << 'EOF' | sudo tee /etc/prometheus/rules/alert_rules.yml
groups:
  - name: ralph_alerts
    rules:
    - alert: HighCPUUsage
      expr: rate(node_cpu_seconds_total{mode="system"}[5m]) * 100 > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: High CPU usage detected
        description: CPU usage is above 80% for 5 minutes

    - alert: HighMemoryUsage
      expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: High memory usage detected
        description: Memory usage is above 85% for 5 minutes

    - alert: DiskSpaceRunningLow
      expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100 < 15
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: Low disk space
        description: Less than 15% disk space remaining
EOF

    # Create recording rules
    cat << 'EOF' | sudo tee /etc/prometheus/rules/recording_rules.yml
groups:
  - name: ralph_recording_rules
    rules:
    - record: job:node_cpu_usage:rate5m
      expr: rate(node_cpu_seconds_total{mode!="idle"}[5m])
    
    - record: job:node_memory_usage:percentage
      expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
EOF

    echo "Monitoring configurations created successfully!"
}





