# log-analytics/main.py
import os
import json
import logging
from shared.tools import LogAnalyticsTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    log_directory = "/app/logs"
    reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
    analytics_tool = LogAnalyticsTool(log_directory=log_directory)

    logging.info("Starting log analytics...")
    try:
        command = "Analyze logs to generate analytics report"
        analytics_result = analytics_tool._run(command)
        logging.info("Log Analytics Result: %s", analytics_result)

        # Create reports directory if it doesn't exist
        os.makedirs(reports_dir, exist_ok=True)
        
        # Save analytics report to the reports directory
        report_path = os.path.join(reports_dir, "analytics_report.json")
        with open(report_path, "w") as f:
            json.dump(json.loads(analytics_result), f, indent=2)
        logging.info("Analytics report saved to %s", report_path)
    except Exception as e:
        logging.error("Error in log analytics: %s", str(e))

if __name__ == "__main__":
    main()