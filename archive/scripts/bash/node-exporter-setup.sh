# Save as node_exporter_install.sh
#!/bin/bash
# install_node_exporter.sh

echo "Starting Node Exporter installation..."

# Create node_exporter user
sudo useradd --no-create-home --shell /bin/false node_exporter

# Download and install Node Exporter
NODE_EXPORTER_VERSION="1.7.0"
wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
tar xvf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz

# Copy binary
sudo cp node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create systemd service
cat << EOF | sudo tee /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start node_exporter
sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter

# Cleanup
rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*

echo "Node Exporter installation setup completed!"
echo "Please check the service status:"
echo "Node Exporter: sudo systemctl status node_exporter"
echo ""
echo "Node Exporter metrics available at: http://localhost:9100/metrics"