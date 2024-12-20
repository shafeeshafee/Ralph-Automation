#!/bin/bash
# 2. setup_ml_components.sh
# Sets up Python environment and ML scripts
setup_ml_components() {
    echo "Setting up ML components..."
    
    # Install Python and required packages
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-dev
    
    # Install required Python packages
    pip3 install prometheus-api-client pandas numpy fbprophet scikit-learn
    
    # Create ML script
    cat << 'EOF' | sudo tee /opt/monitoring/scripts/ml_forecasting.py
import pandas as pd
import numpy as np
from prometheus_api_client import PrometheusConnect
from prophet import Prophet
from sklearn.ensemble import IsolationForest
import json
import time

class MetricsForecasting:
    def __init__(self, prom_url='http://localhost:9090'):
        self.prom = PrometheusConnect(url=prom_url)
        self.prophet_models = {}
        self.isolation_forest = IsolationForest(contamination=0.1)

    def fetch_metric_data(self, query, days=7):
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        
        result = self.prom.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step='5m'
        )
        return self._process_data(result)

    def _process_data(self, result):
        df = pd.DataFrame(columns=['ds', 'y'])
        for data in result:
            timestamps = [pd.to_datetime(t * 1e9) for t in data['values'][0]]
            values = [float(v) for v in data['values'][1]]
            temp_df = pd.DataFrame({'ds': timestamps, 'y': values})
            df = pd.concat([df, temp_df])
        return df

    def train_forecast_model(self, metric_name, df):
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df)
        self.prophet_models[metric_name] = model

    def detect_anomalies(self, df):
        X = df['y'].values.reshape(-1, 1)
        anomalies = self.isolation_forest.fit_predict(X)
        return anomalies == -1

    def generate_forecast(self, metric_name, days_ahead=7):
        if metric_name not in self.prophet_models:
            raise KeyError(f"No model trained for metric: {metric_name}")
        
        model = self.prophet_models[metric_name]
        future = model.make_future_dataframe(periods=days_ahead * 24 * 12, freq='5min')
        forecast = model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

if __name__ == "__main__":
    forecaster = MetricsForecasting()
    # Add your metric queries and training here
EOF

    # Create service file for ML component
    cat << 'EOF' | sudo tee /etc/systemd/system/ml-forecasting.service
[Unit]
Description=ML Forecasting Service
After=prometheus.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/monitoring/scripts/ml_forecasting.py
Restart=always
User=prometheus

[Install]
WantedBy=multi-user.target
EOF

    # Set proper permissions
    sudo chown -R prometheus:prometheus /opt/monitoring
    sudo chmod +x /opt/monitoring/scripts/ml_forecasting.py
    
    echo "ML components setup completed!"
}