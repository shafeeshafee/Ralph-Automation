# /opt/monitoring/python/utils/data_processing.py
import pandas as pd
import numpy as np
from prometheus_api_client import PrometheusConnect
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, prom_url='http://localhost:9090'):
        self.prom = PrometheusConnect(url=prom_url)

    def fetch_metric_data(self, query, days=7):
        try:
            end_time = time.time()
            start_time = end_time - (days * 24 * 60 * 60)
            
            result = self.prom.custom_query_range(
                query=query,
                start_time=start_time,
                end_time=end_time,
                step='5m'
            )
            return self._process_data(result)
        except Exception as e:
            logger.error(f"Error fetching metric data: {str(e)}")
            raise

    def _process_data(self, result):
        df = pd.DataFrame(columns=['ds', 'y'])
        for data in result:
            timestamps = [pd.to_datetime(t * 1e9) for t in data['values'][0]]
            values = [float(v) for v in data['values'][1]]
            temp_df = pd.DataFrame({'ds': timestamps, 'y': values})
            df = pd.concat([df, temp_df])
        return df.sort_values('ds').reset_index(drop=True)