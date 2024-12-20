import os
import json
import logging
import datetime
from shared.tools import AWSResourceTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")
    bucket_name = os.getenv("S3_BUCKET_NAME", "monitoring-logs-bucket-12122024")
    reports_dir = os.getenv("REPORTS_DIR", "/app/reports")

    # Ensure required environment variables are set
    if not all([aws_access_key, aws_secret_key, bucket_name]):
        logging.error("Missing required AWS credentials or bucket configuration")
        return

    aws_tool = AWSResourceTool(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )

    logging.info("Starting reporting agent...")

    try:
        # Create timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load analytics report
        analytics_path = os.path.join(reports_dir, "analytics_report.json")
        monitoring_path = os.path.join(reports_dir, "monitoring_report.json")

        analytics_report = {}
        monitoring_report = {}

        if os.path.exists(analytics_path):
            with open(analytics_path, "r") as f:
                analytics_report = json.load(f)
                logging.info("Loaded analytics report")

        if os.path.exists(monitoring_path):
            with open(monitoring_path, "r") as f:
                monitoring_report = json.load(f)
                logging.info("Loaded monitoring report")

        # Combine reports with metadata
        findings = {
            "timestamp": timestamp,
            "analytics": analytics_report,
            "monitoring": monitoring_report
        }

        # Generate unique filename with timestamp
        output_file = f"findings_report_{timestamp}.json"
        
        # Save findings locally
        findings_path = os.path.join(reports_dir, output_file)
        os.makedirs(reports_dir, exist_ok=True)
        
        with open(findings_path, "w") as f:
            json.dump(findings, f, indent=2)
        logging.info("Findings saved locally to %s", findings_path)

        # Upload to S3
        upload_command = json.dumps({
            "action": "upload_to_s3",
            "params": {
                "bucket_name": bucket_name,
                "file_name": f"logs/{output_file}",
                "content": json.dumps(findings)
            }
        })
        result = aws_tool._run(upload_command)
        logging.info("Findings uploaded to S3: %s/logs/%s", bucket_name, output_file)

    except Exception as e:
        logging.error("Error in reporting: %s", str(e))

if __name__ == "__main__":
    main()