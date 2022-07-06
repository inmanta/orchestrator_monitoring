#!/usr/bin/env python3

import argparse
import sys

import requests


class Status:
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3
    NOARGS = 4


nagios_codes = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]


def get_all_services(base_url, env):
    response = requests.get(
        base_url + f"lsm/v1/service_catalog",
        headers={"X-Inmanta-tid": env},
    )

    if response.status_code != 200:
        _exit(
            Status.CRITICAL,
            f"Received HTTP code {response.status_code} while connecting to {base_url}",
        )

    data = response.json()["data"]

    def find_bad_states(states):
        return [state["name"] for state in states if state["label"] == "danger"]

    return {d["name"]: find_bad_states(d["lifecycle"]["states"]) for d in data}


def no_failed_services(base_url, env):
    services = get_all_services(base_url, env)
    for service, bad_states in services.items():
        filter = "&".join(f"filter.state={s}" for s in bad_states)
        response = requests.get(
            base_url + f"lsm/v1/service_inventory/{service}?{filter}",
            headers={"X-Inmanta-tid": env},
        )

        if response.status_code != 200:
            _exit(
                Status.CRITICAL,
                f"Received HTTP code {response.status_code} while connecting to {base_url}",
            )

        data = response.json()["data"]

        if data:
            for instance in data:
                diagnose_url = f"{base_url}console/lsm/catalog/{service}/inventory/{instance['id']}/diagnose?env={env}"
                text_id = instance["service_identity_attribute_value"] or instance["id"]
                _exit(
                    Status.CRITICAL,
                    f"Service failed for {service} {text_id}: {diagnose_url}",
                )
    _exit(Status.OK, f"All services are fine")


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

    no_failed_services(base_url, env_id)


if __name__ == "__main__":
    main()
