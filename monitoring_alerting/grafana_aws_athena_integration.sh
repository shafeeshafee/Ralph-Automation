#!/bin/bash

# Variables
S3_BUCKET="your-bucket-name"
FINDINGS_FILE="findings_report.json"
ATHENA_DATABASE="findings_database"
QUERY_OUTPUT="s3://your-query-results/"

# Step 1: Upload Findings to S3
aws s3 cp $FINDINGS_FILE s3://$S3_BUCKET/

# Step 2: Start Glue Crawler
aws glue start-crawler --name findings-crawler

# Wait for crawler to complete
while [[ "$(aws glue get-crawler --name findings-crawler --query 'Crawler.State' --output text)" != "READY" ]]; do
    echo "Waiting for crawler to complete..."
    sleep 10
done

# Step 3: Run Athena Query
QUERY_ID=$(aws athena start-query-execution \
    --query-string "SELECT metric_name, anomaly_score, timestamp FROM findings_table WHERE anomaly_score > 0.8 ORDER BY anomaly_score DESC;" \
    --query-execution-context "Database=$ATHENA_DATABASE" \
    --result-configuration "OutputLocation=$QUERY_OUTPUT" \
    --query QueryExecutionId --output text)

# Step 4: Retrieve Query Results
aws athena get-query-results --query-execution-id $QUERY_ID

# Step 5: Integrate with Grafana
curl -X POST http://admin:admin@<grafana-ip>:3000/api/dashboards/db \
-H "Content-Type: application/json" \
-d '{
  "dashboard": {
    "id": null,
    "title": "Findings Dashboard",
    "panels": [
      {
        "type": "table",
        "title": "High Anomaly Scores",
        "targets": [
          {
            "refId": "A",
            "datasource": "Athena",
            "format": "table",
            "rawSql": "SELECT metric_name, anomaly_score, timestamp FROM findings_table WHERE anomaly_score > 0.8 ORDER BY anomaly_score DESC;",
            "timeColumn": "timestamp"
          }
        ]
      }
    ]
  },
  "overwrite": true
}'