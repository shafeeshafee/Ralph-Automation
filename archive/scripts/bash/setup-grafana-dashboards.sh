#!/bin/bash
# setup_grafana_dashboards.sh
# Configures Grafana dashboards
setup_grafana_dashboards() {
    echo "Setting up Grafana dashboards..."
    
    # Create dashboard configuration
    cat << 'EOF' | sudo tee /opt/monitoring/configs/ralph_dashboard.json
{
  "dashboard": {
    "id": null,
    "title": "Ralph DCIM Monitoring",
    "tags": ["ralph", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(node_cpu_seconds_total{mode=\"system\"}[5m]) * 100",
            "legendFormat": "CPU Usage %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "100 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"} * 100)",
            "legendFormat": "Disk Usage %"
          }
        ]
      },
      {
        "title": "Forecasted CPU Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "ml_forecast_cpu_usage",
            "legendFormat": "Forecasted CPU"
          }
        ]
      },
      {
        "title": "Anomaly Detection",
        "type": "stat",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "ml_anomaly_detection_status",
            "legendFormat": "Anomaly Status"
          }
        ]
      }
    ]
  }
}
EOF

    echo "Grafana dashboard configuration completed!"
}