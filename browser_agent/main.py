import sys
import os

# Ensure the package is in part
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_agent.core.agent import Agent
from browser_agent.utils.logger import setup_logger

logger = setup_logger("main")

def main():
    agent = Agent()
    try:
        # Simple test task
        agent.run("Go to google")
    except Exception as e:
        logger.error(f"Error running agent: {e}")
    finally:
        agent.stop()

if __name__ == "__main__":
    main()
