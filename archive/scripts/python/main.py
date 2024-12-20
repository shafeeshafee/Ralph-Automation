# /opt/monitoring/python/main.py
import logging
from utils.data_processing import DataProcessor
from models.prophet_model import ProphetForecaster
from models.lstm_model import LSTMForecaster
from models.anomaly_detection import AnomalyDetector
import json
import os

logging.basicConfig(
    filename='/var/log/monitoring/ml_forecasting.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MLPipeline:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.prophet_forecaster = ProphetForecaster()
        self.lstm_forecaster = LSTMForecaster()
        self.anomaly_detector = AnomalyDetector()

    def run_pipeline(self, metric_names):
        for metric_name in metric_names:
            try:
                # Fetch and process data
                df = self.data_processor.fetch_metric_data(
                    f'rate({metric_name}[5m])'
                )
                
                # Train models
                prophet_model = self.prophet_forecaster.train(metric_name, df)
                lstm_model = self.lstm_forecaster.train(metric_name, df)
                
                # Detect anomalies
                anomalies = self.anomaly_detector.detect(df)
                
                # Save results
                self.save_results(metric_name, df, anomalies)
                
            except Exception as e:
                logger.error(f"Error in pipeline for {metric_name}: {str(e)}")

    def save_results(self, metric_name, df, anomalies):
        results = {
            'metric_name': metric_name,
            'timestamp': df['ds'].max().isoformat(),
            'anomalies_detected': int(anomalies.sum()),
            'total_points': len(df)
        }
        
        with open(f'/opt/monitoring/data/{metric_name}_results.json', 'w') as f:
            json.dump(results, f)

if __name__ == "__main__":
    metrics = [
        'node_cpu_seconds_total',
        'node_memory_MemAvailable_bytes',
        'ralph_http_request_duration_seconds'
    ]
    
    pipeline = MLPipeline()
    pipeline.run_pipeline(metrics)