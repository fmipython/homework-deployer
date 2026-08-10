"""
Command-line interface
"""

import argparse
import json

from homework_deployer.deploy import prod, stage


def main() -> None:
    parser = argparse.ArgumentParser(prog="homework-deployer")
    parser.add_argument("action", choices=["stage", "prod"])
    args = parser.parse_args()

    actions = {"stage": stage, "prod": prod}
    print(json.dumps(actions[args.action]()))
