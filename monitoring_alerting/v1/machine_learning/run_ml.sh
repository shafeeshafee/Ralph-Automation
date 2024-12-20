#!/usr/bin/env bash
while true; do
    # Run anomaly detection
    python anomaly_detection.py
    # Run forecasting
    python forecasting.py
    sleep 300  # run every 5 minutes
done