#!/usr/bin/env python3

import logging
import sys
import os
import time

from environs import Env
from netbox_sd.inventory import NetboxInventory
from netbox_sd.writer import PrometheusSDWriter

import pynetbox
import requests
import urllib3

from prometheus_client import start_http_server, Summary

env = Env()
env.read_env()


class Config(object):

    netbox_url = env("NETBOX_SD_URL")
    netbox_token = env("NETBOX_SD_TOKEN")
    netbox_verify_ssl = env.bool("NETBOX_SD_VERIFY_SSL", True)
    file_path = env.path("NETBOX_SD_FILE_PATH")
    loop_delay = env.int("NETBOX_SD_LOOP_DELAY", 10)
    log_level = env.log_level("NETBOX_SD_LOG_LEVEL", logging.INFO)
    metrics_port = env.int("NETBOX_SD_METRICS_PORT", 8000)


def setup_logging(config: Config):
    logging.basicConfig(
        stream=sys.stdout,
        level=config.log_level,
        format="%(asctime)s %(levelname)s:%(message)s",
    )


def create_netbox_client(config: Config):
    netbox = pynetbox.api(config.netbox_url, config.netbox_token, threading=True)

    session = requests.Session()

    # disable ssl verify and warnings
    session.verify = config.netbox_verify_ssl
    if config.netbox_verify_ssl == False:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    netbox.http_session = session
    return netbox


def main():

    config = Config()
    setup_logging(config)

    logging.info(f"Start Netbox service discovery on url: {config.netbox_url}")
    logging.info(f"Output file is: {config.file_path}")
    logging.info(f"Loop delay is: {config.loop_delay} sec")

    inventory = NetboxInventory(netbox=create_netbox_client(config))

    logging.debug(f"Validate netbox connection")
    inventory.netbox.virtualization.virtual_machines.all()

    logging.info(f"Starting metrics http endpoint on port :{config.metrics_port}")
    start_http_server(config.metrics_port)

    logging.info(f"And ... every day i'm discovering! ")

    while True:

        logging.debug(f"Populate from netbox")
        inventory.populate()
        logging.debug(f"Found {len(inventory.host_list.hosts)} targets")

        logging.debug(f"Write targest to {config.file_path}")
        writer = PrometheusSDWriter(config.file_path)
        writer.write(inventory.host_list)

        logging.debug(f"Waiting {config.loop_delay} seconds for next loop")
        time.sleep(config.loop_delay)


if __name__ == "__main__":
    main()
