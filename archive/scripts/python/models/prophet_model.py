# /opt/monitoring/python/models/prophet_model.py
from fbprophet import Prophet
import logging

logger = logging.getLogger(__name__)

class ProphetForecaster:
    def __init__(self):
        self.models = {}

    def train(self, metric_name, df):
        try:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
                changepoint_range=0.9
            )
            model.add_country_holidays(country_name='US')
            model.fit(df)
            self.models[metric_name] = model
            logger.info(f"Trained Prophet model for {metric_name}")
            return model
        except Exception as e:
            logger.error(f"Error training Prophet model: {str(e)}")
            raise