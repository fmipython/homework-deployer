"""
Command-line interface
"""

import argparse
import json

from homework_deployer.deploy import prod, stage


def main() -> None:
    parser = argparse.ArgumentParser(prog="homework-deployer")
    parser.add_argument("action", choices=["stage", "prod"])
    parser.add_argument("--commit", default=None, help="Git commit SHA to check out instead of the latest commit")
    args = parser.parse_args()

    actions = {"stage": stage, "prod": prod}
    print(json.dumps(actions[args.action](args.commit)))
