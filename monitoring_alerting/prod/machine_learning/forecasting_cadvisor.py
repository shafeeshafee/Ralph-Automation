import os
import time
import logging
import requests
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prophet import Prophet

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Environment Variables
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://pushgateway:9091')

# Forecasting Parameters
LOOKBACK_SECONDS = int(os.getenv('FORECAST_LOOKBACK', '86400'))  # 24 hours
STEP = os.getenv('FORECAST_STEP', '60s')  # 1 minute
HORIZON = int(os.getenv('FORECAST_HORIZON', '60'))  # Forecast horizon in minutes
MIN_FORECAST_ROWS = int(os.getenv('MIN_FORECAST_ROWS', '2'))  # Minimum rows required for forecasting

# List of cAdvisor Metrics for Forecasting
CADVISOR_METRICS = [
    # CPU Metrics
    'container_cpu_usage_seconds_total',  # Total CPU time consumed
    'container_cpu_cfs_periods_total',  # Total CFS (Completely Fair Scheduler) periods
    'container_cpu_cfs_throttled_periods_total',  # CFS throttled periods

    # Memory Metrics
    'container_memory_usage_bytes',  # Memory usage by container
    'container_memory_working_set_bytes',  # Memory minus cache, used actively
    'container_memory_cache',  # Cache memory usage

    # Disk I/O Metrics
    'container_fs_reads_bytes_total',  # Total bytes read from filesystem
    'container_fs_writes_bytes_total',  # Total bytes written to filesystem
    'container_fs_usage_bytes',  # Total disk space used

    # Network Metrics
    'container_network_receive_bytes_total',  # Total bytes received
    'container_network_transmit_bytes_total',  # Total bytes transmitted
    'container_network_receive_packets_total',  # Total packets received
    'container_network_transmit_packets_total',  # Total packets transmitted

    # Additional Metrics
    'container_processes',  # Number of active processes in container
    'container_start_time_seconds',  # Start time of container
]

def fetch_prometheus_data(query, start_time, end_time, step):
    """
    Fetch time series data from Prometheus for a given query.
    """
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
            'query': query,
            'start': start_time,
            'end': end_time,
            'step': step
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] != 'success':
            logging.error(f"Prometheus query failed for {query}: {data}")
            return []
        return data['data']['result']
    except Exception as e:
        logging.exception(f"Error fetching data from Prometheus for {query}")
        return []

def forecast_timeseries(df, horizon_minutes=60, min_rows=2):
    """
    Use Prophet to forecast the next 'horizon_minutes' minutes.
    """
    if df.empty or df.shape[0] < min_rows:
        logging.warning(f"Dataframe has {df.shape[0]} rows, which is less than the required {min_rows}. Returning neutral prediction.")
        return 0.5
    try:
        m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon_minutes, freq='T')  # Minute-level forecast
        forecast = m.predict(future)
        return forecast.iloc[-1]['yhat']
    except Exception as e:
        logging.exception("Error during forecasting with Prophet")
        return 0.5

def push_forecast(predicted_usage, labels):
    """
    Push the forecasted usage to the Pushgateway with appropriate labels.
    """
    try:
        registry = CollectorRegistry()
        g = Gauge('predicted_usage', 'Forecasted usage by ML model', labelnames=labels.keys(), registry=registry)
        g.labels(**labels).set(predicted_usage)
        push_to_gateway(PUSHGATEWAY_URL, job='cadvisor_forecast', registry=registry)
        logging.info(f"Pushed predicted usage {predicted_usage} with labels {labels}")
    except Exception as e:
        logging.exception("Error pushing forecast to Pushgateway")

def main():
    """
    Main function to iterate over all cAdvisor metrics, perform forecasting, and push results.
    """
    end_time = int(time.time())
    start_time = end_time - LOOKBACK_SECONDS

    for metric in CADVISOR_METRICS:
        logging.info(f"Processing metric for forecasting: {metric}")
        results = fetch_prometheus_data(metric, start_time, end_time, STEP)

        if not results:
            push_forecast(0.5, {'metric': metric})
            continue

        for ts in results:
            values = ts['values']
            metric_labels = ts.get('metric', {})
            # Convert timestamps to datetime
            df = pd.DataFrame(values, columns=['ds', 'y'])
            df['ds'] = pd.to_datetime(df['ds'], unit='s')
            df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(0)

            predicted = forecast_timeseries(df, horizon_minutes=HORIZON, min_rows=MIN_FORECAST_ROWS)
            push_forecast(predicted, metric_labels)

if __name__ == "__main__":
    main()