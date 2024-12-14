# forecasting.py
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

# List of Metrics for Forecasting
FORECAST_METRICS = [
    # CPU Metrics
    'node_cpu_seconds_total',               # Total CPU time
    'node_cpu_utilization_ratio',           # CPU utilization ratio (if derived from Prometheus)

    # Memory Metrics
    'node_memory_MemAvailable_bytes',       # Available memory
    'node_memory_Cached_bytes',             # Cached memory
    'node_memory_Buffers_bytes',            # Memory used for buffers

    # Disk I/O Metrics
    'node_disk_read_bytes_total',           # Total bytes read from disk
    'node_disk_written_bytes_total',        # Total bytes written to disk
    'node_disk_io_time_seconds_total',      # Time spent on disk I/O

    # Network Metrics
    'node_network_receive_bytes_total',     # Total bytes received
    'node_network_transmit_bytes_total',    # Total bytes transmitted
    'node_network_receive_errs_total',      # Total receive errors
    'node_network_transmit_errs_total',     # Total transmit errors
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
    Returns both the last actual value and the predicted value.
    """
    if df.empty or df.shape[0] < min_rows:
        logging.warning(f"Dataframe has {df.shape[0]} rows, which is less than the required {min_rows}")
        return None, None

    try:
        # Get the last actual value
        last_actual = df['y'].iloc[-1]

        # Fit Prophet model and make prediction
        m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon_minutes, freq='T')
        forecast = m.predict(future)
        predicted = forecast.iloc[-1]['yhat']

        return last_actual, predicted

    except Exception as e:
        logging.exception("Error during forecasting with Prophet")
        return None, None

def push_metrics(metric_name, actual_value, predicted_value, labels):
    """
    Push both actual and predicted metrics to Pushgateway with appropriate labels.
    """
    try:
        registry = CollectorRegistry()

        # Create gauges for actual and predicted values
        actual_gauge = Gauge(f'{metric_name}_actual', 
                           f'Actual value for {metric_name}',
                           labelnames=labels.keys(),
                           registry=registry)
        
        predicted_gauge = Gauge(f'{metric_name}_predicted', 
                              f'Predicted value for {metric_name}',
                              labelnames=labels.keys(),
                              registry=registry)

        # Push both metrics with their labels
        if actual_value is not None:
            actual_gauge.labels(**labels).set(actual_value)
        if predicted_value is not None:
            predicted_gauge.labels(**labels).set(predicted_value)

        # Push to gateway with a unique job name for each metric
        push_to_gateway(PUSHGATEWAY_URL, 
                       job=f'ml_forecast_{metric_name}',
                       registry=registry)

        logging.info(f"Pushed metrics for {metric_name}: actual={actual_value}, predicted={predicted_value}")

    except Exception as e:
        logging.exception(f"Error pushing metrics to Pushgateway for {metric_name}")

def process_metric(metric_name, metric_data):
    """
    Process a single metric's data and push results to Prometheus.
    """
    values = metric_data['values']
    metric_labels = metric_data.get('metric', {})
    
    # Convert timestamps to datetime
    df = pd.DataFrame(values, columns=['ds', 'y'])
    df['ds'] = pd.to_datetime(df['ds'], unit='s')
    df['y'] = pd.to_numeric(df['y'], errors='coerce').fillna(0)

    # Get actual and predicted values
    actual, predicted = forecast_timeseries(df, 
                                          horizon_minutes=HORIZON, 
                                          min_rows=MIN_FORECAST_ROWS)

    # Prepare labels
    labels = {k: v for k, v in metric_labels.items() if k != '__name__'}
    labels['metric'] = metric_name

    # Push metrics
    push_metrics(metric_name, actual, predicted, labels)

def main():
    """
    Main function to process metrics and push both actual and predicted values.
    """
    end_time = int(time.time())
    start_time = end_time - LOOKBACK_SECONDS

    for metric in FORECAST_METRICS:
        logging.info(f"Processing metric: {metric}")
        results = fetch_prometheus_data(metric, start_time, end_time, STEP)

        if not results:
            logging.warning(f"No data found for metric: {metric}")
            continue

        for ts in results:
            process_metric(metric, ts)

        # Sleep briefly to avoid overwhelming the Pushgateway
        time.sleep(0.1)

if __name__ == "__main__":
    main()