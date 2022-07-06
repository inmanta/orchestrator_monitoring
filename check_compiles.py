#!/usr/bin/env python3

import argparse
import datetime
import sys
from datetime import timedelta

import requests


class Status:
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3
    NOARGS = 4


nagios_codes = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]


def failed_exporting_compiles(base_url, env):
    min24h = (datetime.datetime.utcnow() - timedelta(days=1)).isoformat()
    response = requests.get(
        base_url
        + f"api/v2/compilereport?filter.success=False&filter.requested=ge:{min24h}",
        headers={"X-Inmanta-tid": env},
    )

    if response.status_code != 200:
        _exit(
            Status.CRITICAL,
            f"Received HTTP code {response.status_code} while connecting to {base_url}",
        )

    data = response.json()["data"]
    failed = [x["id"] for x in data if x["do_export"]]

    if failed:
        for cid in failed:
            _exit(
                Status.CRITICAL,
                f"Compile failed: {base_url}console/compilereports/{cid}?env={env}",
            )
    _exit(Status.OK, f"All compiles are succeeding")


def _exit(code=Status.OK, msg="No errors"):
    print(f"{nagios_codes[code]} - {msg}")
    sys.exit(code)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base_url",
        help="Base URL of Inmanta server. e.g. http://172.30.0.3:8888/",
        required=True,
    )
    parser.add_argument("--env_id", help="Environment ID to check", required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    base_url = args.base_url
    env_id = args.env_id

    failed_exporting_compiles(base_url, env_id)


if __name__ == "__main__":
    main()
