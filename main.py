"""
Entry point — starts the autonomous social media agent system.

Usage:
  python main.py                  # Start 24/7 scheduler
  python main.py --task content   # Run a single task now
  python main.py --task leads
  python main.py --task followups
  python main.py --task learn
  python main.py --task engage --context "someone asked about pricing on LinkedIn"
"""
import argparse
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_once(task: str, **kwargs):
    from agents.orchestrator import build_orchestrator
    orch = build_orchestrator()
    task_map = {
        "content":  f"run_content_creation for all platforms",
        "leads":    "run_lead_generation",
        "followups":"run_followups",
        "learn":    "run_learning",
        "engage":   f"run_engagement — context: {kwargs.get('context', 'check all platforms')}",
    }
    prompt = task_map.get(task, task)
    logger.info(f"Running task: {prompt}")
    result = orch(prompt)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Social Media Agent System")
    parser.add_argument("--task", type=str, default=None,
                        help="Run a single task: content|leads|followups|learn|engage")
    parser.add_argument("--context", type=str, default="",
                        help="Extra context for the engage task")
    args = parser.parse_args()

    if args.task:
        run_once(args.task, context=args.context)
    else:
        logger.info(f"Starting 24/7 autonomous agent system...")
        from core.scheduler import start
        start()


if __name__ == "__main__":
    main()
