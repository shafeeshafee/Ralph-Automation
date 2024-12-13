FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y libprotobuf-dev build-essential python3-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY anomaly_detection.py .
COPY forecasting.py .
COPY run_ml.sh .
RUN chmod +x run_ml.sh

CMD ["/app/run_ml.sh"]