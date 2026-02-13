from finopsguard.env import load_runtime_env
from finopsguard.graph import FinOpsGraph


def main() -> None:
    load_runtime_env()
    graph = FinOpsGraph(config_path="config.yaml")
    report = graph.run_weekly()
    print(report)


if __name__ == "__main__":
    main()
