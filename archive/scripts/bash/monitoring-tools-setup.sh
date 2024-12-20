#!/bin/bash
# install_prometheus_grafana.sh
setup_prometheus() {
    echo "Setting up Prometheus..."
    # Create prometheus user
    sudo useradd --no-create-home --shell /bin/false prometheus

    # Create directories
    sudo mkdir /etc/prometheus
    sudo mkdir /var/lib/prometheus
    sudo chown prometheus:prometheus /var/lib/prometheus

    # Download and install Prometheus
    PROMETHEUS_VERSION="2.49.1"
    wget https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
    tar xvf prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz

    # Copy binaries
    sudo cp prometheus-${PROMETHEUS_VERSION}.linux-amd64/prometheus /usr/local/bin/
    sudo cp prometheus-${PROMETHEUS_VERSION}.linux-amd64/promtool /usr/local/bin/
    sudo chown prometheus:prometheus /usr/local/bin/prometheus
    sudo chown prometheus:prometheus /usr/local/bin/promtool

    # Copy config files
    sudo cp -r prometheus-${PROMETHEUS_VERSION}.linux-amd64/consoles /etc/prometheus
    sudo cp -r prometheus-${PROMETHEUS_VERSION}.linux-amd64/console_libraries /etc/prometheus
    sudo chown -R prometheus:prometheus /etc/prometheus

    # Create prometheus config
    cat << EOF | sudo tee /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'ralph'
    static_configs:
      - targets: ['localhost:8000']
EOF

    sudo chown prometheus:prometheus /etc/prometheus/prometheus.yml

    # Create systemd service
    cat << EOF | sudo tee /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

    # Start prometheus
    sudo systemctl daemon-reload
    sudo systemctl start prometheus
    sudo systemctl enable prometheus

    # Cleanup
    rm -rf prometheus-${PROMETHEUS_VERSION}.linux-amd64*
    
    echo "Prometheus setup completed!"
}

setup_grafana() {
    echo "Setting up Grafana..."
    # Install Grafana
    sudo apt-get install -y software-properties-common
    wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
    
    sudo apt-get update
    sudo apt-get install -y grafana

    # Start Grafana
    sudo systemctl start grafana-server
    sudo systemctl enable grafana-server
    
    echo "Grafana setup completed!"
}

# Main installation
echo "Starting Prometheus and Grafana installation..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y wget curl apt-transport-https software-properties-common

setup_prometheus
setup_grafana

echo "Installation setup completed!"
echo "Please check the services status:"
echo "Prometheus: sudo systemctl status prometheus"
echo "Grafana: sudo systemctl status grafana-server"
echo ""
echo "Access your services at:"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (default credentials: admin/admin)"

