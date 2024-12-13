# dev/shared/workflow_coordinator.py
from typing import Dict, Any
import os
import json
import time
import logging
from datetime import datetime
from prometheus_client import (
    CollectorRegistry, Counter, Histogram, Gauge, 
    push_to_gateway, REGISTRY
)
from shared.tools import LogAnalyticsTool, PrometheusQueryTool, AWSResourceTool

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger('WorkflowCoordinator')

class WorkflowMetrics:
    def __init__(self, pushgateway_url: str):
        self.pushgateway_url = pushgateway_url
        self.registry = CollectorRegistry()
        
        # Counters for workflow execution
        self.workflow_executions = Counter(
            'workflow_total_executions',
            'Total number of workflow executions',
            registry=self.registry
        )
        self.workflow_failures = Counter(
            'workflow_failures_total',
            'Total number of workflow failures',
            registry=self.registry
        )
        self.step_failures = Counter(
            'workflow_step_failures_total',
            'Step-specific failures',
            ['step'],
            registry=self.registry
        )
        
        # Histograms for timing
        self.step_duration = Histogram(
            'workflow_step_duration_seconds',
            'Time spent in each workflow step',
            ['step'],
            buckets=[1, 5, 10, 30, 60, 120, 300],
            registry=self.registry
        )
        
        # Gauges for current state
        self.last_success_timestamp = Gauge(
            'workflow_last_success_timestamp',
            'Timestamp of last successful workflow execution',
            registry=self.registry
        )
        self.last_failure_timestamp = Gauge(
            'workflow_last_failure_timestamp',
            'Timestamp of last workflow failure',
            registry=self.registry
        )

    def push_metrics(self):
        """Push all metrics to Pushgateway"""
        try:
            push_to_gateway(
                self.pushgateway_url,
                job='workflow_coordinator',
                registry=self.registry
            )
            logger.info("Successfully pushed metrics to Pushgateway")
        except Exception as e:
            logger.error(f"Failed to push metrics: {str(e)}")

class StepTimer:
    def __init__(self, metrics: WorkflowMetrics, step: str):
        self.metrics = metrics
        self.step = step
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics.step_duration.labels(step=self.step).observe(duration)
        if exc_type is not None:
            self.metrics.step_failures.labels(step=self.step).inc()

class WorkflowCoordinator:
    def __init__(self):
        self.reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
        self.log_directory = "/app/logs"
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        self.pushgateway_url = os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091")
        
        # Initialize tools
        self.log_tool = LogAnalyticsTool(log_directory=self.log_directory)
        self.prometheus_tool = PrometheusQueryTool(prometheus_url=self.prometheus_url)
        self.aws_tool = AWSResourceTool(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        # Initialize metrics
        self.metrics = WorkflowMetrics(self.pushgateway_url)

    def _time_step(self, step_name: str) -> StepTimer:
        """Context manager for timing workflow steps"""
        return StepTimer(self.metrics, step_name)

    def _coordinate_log_analysis(self) -> Dict[str, Any]:
        with self._time_step("log_analysis"):
            try:
                logger.info("Starting log analysis coordination")
                result = self.log_tool._run("Analyze logs to generate analytics report")
                result_data = json.loads(result)
                
                logger.info(f"Log analysis completed successfully. Found {len(result_data.get('summary', []))} entries")
                return {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "data": result_data
                }
            except Exception as e:
                logger.error(f"Log analysis failed: {str(e)}", exc_info=True)
                raise

    def _coordinate_monitoring(self) -> Dict[str, Any]:
        with self._time_step("monitoring"):
            try:
                logger.info("Starting monitoring coordination")
                queries = {
                    "node_metrics": "node_memory_MemAvailable_bytes",
                    "container_metrics": "container_memory_usage_bytes",
                    "up_status": "up",
                    "cadvisor_metrics": "container_cpu_usage_seconds_total",
                    "anomaly_scores": 'anomaly_score{metric="container_cpu_usage_seconds_total"} > 0.8'
                }
                
                monitoring_results = {}
                for name, query in queries.items():
                    logger.debug(f"Executing query: {name}")
                    result = self.prometheus_tool._run(query)
                    monitoring_results[name] = json.loads(result)
                
                logger.info(f"Monitoring completed successfully. Collected {len(monitoring_results)} metrics")
                return {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "data": monitoring_results
                }
            except Exception as e:
                logger.error(f"Monitoring failed: {str(e)}", exc_info=True)
                raise

    def _coordinate_analytics(self, log_data: Dict, monitoring_data: Dict) -> Dict[str, Any]:
        with self._time_step("analytics"):
            try:
                logger.info("Starting analytics coordination")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                analysis_data = {
                    "timestamp": timestamp,
                    "log_analysis": log_data,
                    "monitoring": monitoring_data
                }
                
                analysis_path = os.path.join(self.reports_dir, f"analysis_{timestamp}.json")
                os.makedirs(self.reports_dir, exist_ok=True)
                
                with open(analysis_path, "w") as f:
                    json.dump(analysis_data, f, indent=2)
                
                logger.info(f"Analytics data saved to {analysis_path}")
                return {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "file_path": analysis_path,
                    "data": analysis_data
                }
            except Exception as e:
                logger.error(f"Analytics failed: {str(e)}", exc_info=True)
                raise

    def _coordinate_reporting(self, analysis_data: Dict) -> Dict[str, Any]:
        with self._time_step("reporting"):
            try:
                logger.info("Starting reporting coordination")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"report_{timestamp}.json"
                
                upload_command = json.dumps({
                    "action": "upload_to_s3",
                    "params": {
                        "bucket_name": os.getenv("S3_BUCKET_NAME"),
                        "file_name": f"reports/{report_file}",
                        "content": json.dumps(analysis_data)
                    }
                })
                
                self.aws_tool._run(upload_command)
                
                logger.info(f"Report uploaded successfully to S3: reports/{report_file}")
                return {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "s3_path": f"reports/{report_file}"
                }
            except Exception as e:
                logger.error(f"Reporting failed: {str(e)}", exc_info=True)
                raise

    def run_workflow(self) -> Dict[str, Any]:
        """Executes the complete workflow sequentially"""
        start_time = time.time()
        self.metrics.workflow_executions.inc()
        
        try:
            logger.info("Starting workflow execution")
            workflow_state = {
                "start_time": datetime.now().isoformat(),
                "status": "started"
            }
            
            # Execute steps sequentially
            log_result = self._coordinate_log_analysis()
            workflow_state["log_analysis"] = log_result
            
            monitoring_result = self._coordinate_monitoring()
            workflow_state["monitoring"] = monitoring_result
            
            analytics_result = self._coordinate_analytics(
                log_result.get("data", {}),
                monitoring_result.get("data", {})
            )
            workflow_state["analytics"] = analytics_result
            
            reporting_result = self._coordinate_reporting(analytics_result.get("data", {}))
            workflow_state["reporting"] = reporting_result
            
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = datetime.now().isoformat()
            workflow_state["duration"] = time.time() - start_time
            
            # Update success metrics
            self.metrics.last_success_timestamp.set_to_current_time()
            logger.info(f"Workflow completed successfully in {workflow_state['duration']:.2f} seconds")
            
            return workflow_state
            
        except Exception as e:
            self.metrics.workflow_failures.inc()
            self.metrics.last_failure_timestamp.set_to_current_time()
            
            error_msg = str(e)
            logger.error(f"Workflow failed: {error_msg}", exc_info=True)
            
            return {
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - start_time
            }
        finally:
            # Push metrics in any case
            self.metrics.push_metrics()