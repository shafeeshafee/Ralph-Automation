#!/bin/bash
# main_setup.sh
# Main setup script that runs all components
echo "Starting complete monitoring setup..."

# Source the component scripts
source setup_monitoring_configs.sh
source setup_ml_components.sh
source setup_grafana_dashboards.sh

# Run all setups
setup_monitoring_configs
setup_ml_components
setup_grafana_dashboards

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart prometheus
sudo systemctl restart grafana-server
sudo systemctl start ml-forecasting
sudo systemctl enable ml-forecasting

echo "Complete monitoring setup finished!"
echo "Access your services at:"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000"
echo ""
echo "Don't forget to:"
echo "1. Import the dashboard in Grafana using /opt/monitoring/configs/ralph_dashboard.json"
echo "2. Configure Prometheus as a data source in Grafana"
echo "3. Check the ML forecasting service status with: sudo systemctl status ml-forecasting"