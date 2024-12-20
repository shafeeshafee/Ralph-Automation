# /opt/monitoring/python/models/lstm_model.py
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
import logging

logger = logging.getLogger(__name__)

class LSTMForecaster:
    def __init__(self):
        self.models = {}
        self.scalers = {}

    def prepare_sequences(self, data, sequence_length=24):
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:i + sequence_length])
            y.append(data[i + sequence_length])
        return np.array(X), np.array(y)

    def train(self, metric_name, df, sequence_length=24):
        try:
            values = df['y'].values
            scaled_values = (values - values.mean()) / values.std()
            
            X, y = self.prepare_sequences(scaled_values, sequence_length)
            
            model = Sequential([
                LSTM(50, activation='relu', input_shape=(sequence_length, 1)),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            
            model.fit(
                X.reshape(-1, sequence_length, 1),
                y,
                epochs=50,
                batch_size=32,
                verbose=0
            )
            
            self.models[metric_name] = model
            self.scalers[metric_name] = {'mean': values.mean(), 'std': values.std()}
            
            logger.info(f"Trained LSTM model for {metric_name}")
            return model
        except Exception as e:
            logger.error(f"Error training LSTM model: {str(e)}")
            raise