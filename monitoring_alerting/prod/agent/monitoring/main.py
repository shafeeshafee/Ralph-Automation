import os
import json
import logging
from shared.tools import PrometheusQueryTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
    prometheus_tool = PrometheusQueryTool(prometheus_url=prometheus_url)

    logging.info("Starting Prometheus monitoring diagnostics...")
    try:
        # Test queries for different metric types
        test_queries = {
            "node_metrics": "node_memory_MemAvailable_bytes",
            "container_metrics": "container_memory_usage_bytes",
            "up_status": "up",
            "cadvisor_metrics": "container_cpu_usage_seconds_total",
            "anomaly_scores": 'anomaly_score{metric="container_cpu_usage_seconds_total"} > 0.8'
        }

        results = {}
        for name, query in test_queries.items():
            try:
                query_result = prometheus_tool._run(query)
                logging.info(f"Query Result for {name}: {query_result}")
                results[name] = json.loads(query_result)
            except Exception as e:
                logging.error(f"Error querying {name}: {str(e)}")
                results[name] = {"error": str(e)}

        # Save comprehensive report
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "monitoring_report.json")
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        logging.info("Monitoring report saved to %s", report_path)

    except Exception as e:
        logging.error("Error in monitoring: %s", str(e))

if __name__ == "__main__":
    main()