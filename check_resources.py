#!/usr/bin/env python3

import argparse
import sys
from urllib.parse import quote

import requests


class Status:
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3
    NOARGS = 4


nagios_codes = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]


def get_failed_resource(base_url, env):
    response = requests.get(
        base_url
        + f"api/v2/resource?limit=20&filter.status=failed&sort=resource_type.asc",
        headers={"X-Inmanta-tid": env},
    )

    if response.status_code != 200:
        _exit(
            Status.CRITICAL,
            f"Received HTTP code {response.status_code} while connecting to {base_url}",
        )

    data = response.json()["data"]

    if data:
        for resource in data:
            rid = resource["resource_id"]
            rid = quote(rid)
            resource_url = f"{base_url}console/resources/{rid}?env={env}"
            _exit(Status.CRITICAL, f"Failed deployment on {resource_url}")

    _exit(Status.OK, f"All deployments are successful")


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

    get_failed_resource(base_url, env_id)


if __name__ == "__main__":
    main()
