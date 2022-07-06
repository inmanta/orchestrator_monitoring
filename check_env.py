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


def get_environment(base_url: str, name: str):
    response = requests.get(base_url + "api/v1/environment")

    if response.status_code != 200:
        _exit(
            Status.CRITICAL,
            f"Received HTTP code {response.status_code} while connecting to {base_url}",
        )

    env = {
        r["id"]: r["name"] for r in response.json()["environments"] if r["name"] == name
    }

    if env is None:
        _exit(Status.CRITICAL, f"Environment {name} not found")

    return env


def get_settings(base_url: str, env: str):
    response = requests.get(
        base_url + "api/v2/environment_settings", headers={"X-Inmanta-tid": env}
    )
    response.raise_for_status()
    data = response.json()["data"]
    defaults = {v["name"]: v["default"] for v in data["definition"].values()}
    defaults.update(data["settings"])
    return defaults


def assert_setting(base_url: str, env: dict):
    env_name = next(iter(env.values()))
    env_id = next(iter(env.keys()))

    settings = get_settings(base_url, env_id)
    required = {
        "auto_deploy": True,
        "server_compile": True,
        "purge_on_delete": False,
        "push_on_auto_deploy": True,
        "protected_environment": True,
        "agent_trigger_method_on_auto_deploy": "push_incremental_deploy",
    }

    for k, v in required.items():
        if settings.get(k) != v:
            _exit(
                Status.WARNING,
                f"Environment {env_name}: Setting {k} should be {v} but is {settings.get(k)} | Environment ID: {env_id}",
            )


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
    parser.add_argument("--env", help="Environment name to check", required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    base_url = args.base_url

    env = get_environment(base_url, args.env)
    assert_setting(base_url, env)


if __name__ == "__main__":
    main()
