# dev/coordinator/main.py
import time
import logging
from shared.workflow_coordinator import WorkflowCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger('WorkflowMain')

def main():
    coordinator = WorkflowCoordinator()
    
    while True:
        try:
            logger.info("Starting workflow coordination cycle...")
            result = coordinator.run_workflow()
            
            if result.get("status") == "failed":
                logger.error("Workflow failed: %s", result.get("error"))
            else:
                logger.info("Workflow cycle completed successfully")
                
        except Exception as e:
            logger.error("Unexpected error in workflow coordination: %s", str(e))
            
        time.sleep(300)  # Run every 5 minutes

if __name__ == "__main__":
    main()