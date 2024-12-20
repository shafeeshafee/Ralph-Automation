# agent/analytics/main.py
import os
import json
import logging
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_analysis():
    reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
    script_path = "/app/scripts/analyze_findings.sh"

    try:
        # Ensure script is executable
        subprocess.run(["chmod", "+x", script_path], check=True)

        # Execute analysis script
        result = subprocess.run([script_path], 
                              capture_output=True, 
                              text=True,
                              check=True)
        
        logging.info("Analysis completed: %s", result.stdout)
        
    except subprocess.CalledProcessError as e:
        logging.error("Analysis script failed: %s", e.stderr)
    except Exception as e:
        logging.error("Error in analysis: %s", str(e))

def main():
    while True:
        logging.info("Starting analytics process...")
        run_analysis()
        time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    main()