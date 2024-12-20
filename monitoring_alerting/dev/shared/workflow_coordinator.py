import os
import logging
from typing import Dict, Any, Sequence, Union
from datetime import datetime
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway

from .workflows.states import WorkflowState, create_initial_state, update_state_metadata
from .agent_tools import (
    LogAnalyticsAgentTool,
    MonitoringAgentTool,
    AnalyticsAgentTool,
    ReportingAgentTool,
    MetricArchivalAgentTool
)

logger = logging.getLogger(__name__)

class WorkflowCoordinator:
    def __init__(self):
        # Initialize configuration
        self.reports_dir = os.getenv("REPORTS_DIR", "/app/reports")
        self.log_directory = "/app/logs"
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        self.pushgateway_url = os.getenv("PUSHGATEWAY_URL", "http://pushgateway:9091")
        
        # Initialize tools
        self.tools = {
            "log_analytics": LogAnalyticsAgentTool(self.log_directory),
            "monitoring": MonitoringAgentTool(self.prometheus_url),
            "analytics": AnalyticsAgentTool(),
            "reporting": ReportingAgentTool(self.reports_dir),
            "metric_archival": MetricArchivalAgentTool()
        }
        
        # Initialize workflow graph
        self.workflow = self._create_workflow_graph()
        
        # Initialize metrics
        self.registry = CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self):
        """Setup Prometheus metrics"""
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
        self.step_duration = Gauge(
            'workflow_step_duration_seconds',
            'Time spent in each workflow step',
            ['step'],
            registry=self.registry
        )

    def _create_workflow_graph(self) -> StateGraph:
        """Create the workflow graph using LangGraph"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("process_logs", self._process_logs)
        workflow.add_node("collect_metrics", self._collect_metrics)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_report", self._generate_report)
        workflow.add_node("archive_metrics", self._archive_metrics)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "",
            self._should_continue,
            {
                "process_logs": "process_logs",
                "collect_metrics": "collect_metrics",
                "analyze_data": "analyze_data",
                "generate_report": "generate_report",
                "archive_metrics": "archive_metrics",
                "end": None
            }
        )
        
        return workflow.compile()

    async def _process_logs(self, state: WorkflowState) -> WorkflowState:
        """Process logs using Log Analytics Agent"""
        try:
            tool = self.tools["log_analytics"]
            result = await tool.arun(self.log_directory)
            state["agent_status"]["log_analytics"] = result["status"]
            state["analysis"]["logs"] = result["results"]
            return update_state_metadata(state)
        except Exception as e:
            state["errors"].append({"agent": "log_analytics", "error": str(e)})
            return update_state_metadata(state)

    def _should_continue(self, state: WorkflowState) -> Union[Sequence[str], str]:
        """Determine next steps based on state"""
        # Check for critical errors
        if any(e.get("critical", False) for e in state["errors"]):
            return "end"

        # Check workflow completion
        all_completed = all(
            status == "completed" 
            for status in state["agent_status"].values()
        )
        if all_completed:
            return "end"

        # Determine next steps
        next_steps = []
        status = state["agent_status"]
        
        if status["log_analytics"] != "completed":
            next_steps.append("process_logs")
        if status["monitoring"] != "completed":
            next_steps.append("collect_metrics")
        if status["analytics"] != "completed" and state["metrics"]:
            next_steps.append("analyze_data")
        if status["reporting"] != "completed" and state["analysis"]:
            next_steps.append("generate_report")
        if status["metric_archival"] != "completed" and state["metrics"]:
            next_steps.append("archive_metrics")
        
        return next_steps if next_steps else "end"

    async def run_workflow(self) -> Dict[str, Any]:
        """Execute the workflow"""
        try:
            self.workflow_executions.inc()
            
            # Create initial state
            initial_state = create_initial_state()
            
            # Execute workflow
            async for state in self.workflow.astream(initial_state):
                # Update metrics
                for step, status in state["agent_status"].items():
                    if status == "completed":
                        self.step_duration.labels(step=step).set(
                            (datetime.now() - datetime.fromisoformat(state["metadata"]["start_time"])).total_seconds()
                        )
                
                # Push metrics
                push_to_gateway(
                    self.pushgateway_url,
                    job='workflow_coordinator',
                    registry=self.registry
                )
            
            return state
            
        except Exception as e:
            self.workflow_failures.inc()
            logger.error(f"Workflow execution failed: {str(e)}")
            raise