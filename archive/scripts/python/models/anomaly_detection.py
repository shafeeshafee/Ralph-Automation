# /opt/monitoring/python/models/anomaly_detection.py
from sklearn.ensemble import IsolationForest
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            max_samples='auto',
            random_state=42
        )

    def detect(self, df, sensitivity=1.5):
        try:
            X = df['y'].values.reshape(-1, 1)
            anomalies = self.model.fit_predict(X)
            
            # Statistical approach
            mean = df['y'].mean()
            std = df['y'].std()
            z_scores = np.abs((df['y'] - mean) / std)
            statistical_anomalies = z_scores > sensitivity
            
            # Combine approaches
            final_anomalies = (anomalies == -1) | statistical_anomalies
            
            return final_anomalies
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            raise