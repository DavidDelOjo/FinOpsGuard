from finopsguard.graph import FinOpsGraph


def main() -> None:
    graph = FinOpsGraph(config_path="config.yaml")
    report = graph.run_weekly()
    print(report)


if __name__ == "__main__":
    main()
