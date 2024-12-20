from typing import TypedDict, List, Dict, Any
from datetime import datetime

class WorkflowState(TypedDict):
    """Definition of workflow state"""
    agent_status: Dict[str, str]  # Status of each agent
    metrics: Dict[str, Any]       # Collected metrics
    analysis: Dict[str, Any]      # Analysis results
    errors: List[Dict[str, str]]  # Error tracking
    metadata: Dict[str, Any]      # Workflow metadata

def create_initial_state() -> WorkflowState:
    """Create initial workflow state"""
    return WorkflowState(
        agent_status={
            "log_analytics": "pending",
            "monitoring": "pending",
            "analytics": "pending",
            "reporting": "pending",
            "metric_archival": "pending"
        },
        metrics={},
        analysis={},
        errors=[],
        metadata={
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    )

def update_state_metadata(state: WorkflowState) -> WorkflowState:
    """Update state metadata with current timestamp"""
    state["metadata"]["last_update"] = datetime.now().isoformat()
    return state