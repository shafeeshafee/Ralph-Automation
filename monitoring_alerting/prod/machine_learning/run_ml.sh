#!/usr/bin/env bash
while true; do
    # Run anomaly detection
    python anomaly_detection.py
    python anomaly_detection_cadvisor.py
    
    # Run forecasting
    python forecasting.py
    python forecasting_cadvisor.py

    sleep 300  # run every 5 minutes
done