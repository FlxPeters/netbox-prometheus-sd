import logging
import sys
import os
import json
import argparse
import time

import netaddr

from pynetbox.core.api import Api
from pynetbox.core.response import Record
from pynetbox import RequestError
from requests.exceptions import ConnectionError

from prometheus_client import Summary, Gauge, Counter

from pprint import pprint

from .writer import PrometheusSDWriter
from .model import Host, HostType, HostList

POPULATION_TIME = Summary(
    "netbox_sd_populate_seconds", "Time spent populating the inventory from netbox"
)
HOST_GAUGE = Gauge("netbox_sd_hosts", "Number of hosts discovered by netbox-sd")
NETBOX_REQUEST_COUNT_TOTAL = Counter(
    "netbox_sd_requests_total", "Total count of requests to netbox API"
)
NETBOX_REQUEST_COUNT_ERROR_TOTAL = Counter(
    "netbox_sd_requests_error_total", "Total count of failed requests to netbox API"
)


class NetboxInventory:
    def __init__(self, netbox: Api):
        self.netbox = netbox
        self.host_list = HostList()

    @POPULATION_TIME.time()
    def populate(self, filter, netbox_objects):
        self.host_list.clear()
        # filter = {"status": "active"}
        logging.debug(f"Filter is :{filter}")
        try:
            if 'vm' in netbox_objects:
                NETBOX_REQUEST_COUNT_TOTAL.inc()
                vm_list = self.netbox.virtualization.virtual_machines.filter(**filter)
                logging.debug(f"Found {len(vm_list)} active virtual machines")

                for vm in vm_list:
                    # filter vms without primary ip
                    if not getattr(vm, "primary_ip4"):
                        logging.debug(f"Drop vm '{vm.name}' due to missing primary IPv4")
                        continue
                    host = self._populate_host_from_netbox(vm, HostType.VIRTUAL_MACHINE)
                    # Add services
                    self._get_service_list_for_host(host, virtual_machine_id=vm.id)
                    self.host_list.add_host(host)
            else:
                logging.debug(f"skip vm population")

            if 'device' in netbox_objects:
                # Get all active devices
                NETBOX_REQUEST_COUNT_TOTAL.inc()
                device_list = self.netbox.dcim.devices.filter(**filter)
                logging.debug(f"Found {len(device_list)} active devices")
                for device in device_list:
                    # filter devices without primary ip
                    if not getattr(device, "primary_ip4"):
                        logging.debug(
                            f"Drop device '{device.name}' due to missing primary IPv4"
                        )
                        continue
                    host = self._populate_host_from_netbox(device, HostType.DEVICE)
                    # Add services
                    self._get_service_list_for_host(host, device_id=device.id)
                    self.host_list.add_host(host)
            else:
                logging.debug(f"skip device population")

            if 'ip_address' in netbox_objects:
                if len(netbox_objects) > 1:
                    logging.warn(f"NETBOX_OBJECTS is set to {netbox_objects} which will lead to duplicated entries in the Prometheus servive discovery")
                # Get all active devices
                NETBOX_REQUEST_COUNT_TOTAL.inc()
                ip_addresses_list = self.netbox.ipam.ip_addresses.filter(**filter)
                logging.debug(f"Found {len(ip_addresses_list)} active ip addresses")
                for ip_address in ip_addresses_list:
                    host = self._populate_host_from_netbox(ip_address, HostType.IP_ADDRESS)
                    self.host_list.add_host(host)
            else:
                logging.debug(f"skip ip_addresses population")

            HOST_GAUGE.set(len(self.host_list.hosts))

        except (ConnectionError, RequestError) as e:
            NETBOX_REQUEST_COUNT_ERROR_TOTAL.inc()
            logging.error(f"Failed to add target: {e}")

    def _populate_host_from_netbox(self, data: Record, host_type: HostType):
        """
        Map values from netbox Records containing a virtual machine or device to a host object.
        See https://pynetbox.readthedocs.io/en/latest/response.html for more details on records.
        """

        ip = self._get_ip_from_record(data, host_type)
        name = self._get_name_from_record(data, host_type)
        host = Host(data.id, name, ip, host_type=host_type)

        # add labels if attribute is available
        if getattr(data, "tenant", None):
            host.add_label("tenant", data.tenant.name)
            host.add_label("tenant_slug", data.tenant.slug)
            if data.tenant.group:
                host.add_label("tenant_group", data.tenant.group.name)
                host.add_label("tenant_group_slug", data.tenant.group.slug)
        if getattr(data, "site", None):
            host.add_label("site", data.site.name)
            host.add_label("site_slug", data.site.slug)
        # Normalize VM role and device role
        if getattr(data, "device_role", None):
            host.add_label("role", data.device_role.name)
            host.add_label("role_slug", data.device_role.slug)
        if getattr(data, "role", None):
            host.add_label("role", data.role.name)
            host.add_label("role_slug", data.role.slug)
        if getattr(data, "cluster", None):
            host.add_label("cluster", data.cluster.name)
        if getattr(data, "device_type", None):
            host.add_label("device_type", data.device_type.model)
            host.add_label("device_type", data.device_type.slug)
        if getattr(data, "platform", None):
            host.add_label("platform", data.platform.name)
            host.add_label("platform_slug", data.platform.slug)

        # Add site drom cluster if type is a VM
        if host.host_type == HostType.VIRTUAL_MACHINE:
            if getattr(data, "cluster", None):
                if getattr(data.cluster, "site", None):
                    host.add_label("site", data.cluster.site.name)
                    host.add_label("site_slug", data.cluster.site.slug)

        # Add custom attributes
        if getattr(data, "custom_fields", None):
            for key, value in data["custom_fields"].items():
                host.add_label("custom_field_" + key, value)

        # Add Tags as comma separated list
        if getattr(data, "tags", None):
            host.add_label("tags", ",".join([t.name for t in data.tags]))
            host.add_label("tag_slugs", ",".join([t.slug for t in data.tags]))

        # Add dns_name if type is a IP_ADDRESS
        if host.host_type == HostType.IP_ADDRESS:
            if getattr(data, "dns_name", None):
                host.add_label("dns_name", data.dns_name)

        return host

    def _get_service_list_for_host(self, host, virtual_machine_id=None, device_id=None):
        NETBOX_REQUEST_COUNT_TOTAL.inc()
        service_list = self.netbox.ipam.services.filter(
            virtual_machine_id=virtual_machine_id, device_id=device_id
        )
        logging.debug(
            f"Found {len(service_list)} services for virtual_machine={virtual_machine_id} or device={device_id}"
        )
        for service in service_list:
            # netbox <= 2.9
            if getattr(service, "port", None):
                host.add_label("service_%s" % service.name, service.port)
            # netbox >= 2.10
            elif getattr(service, "ports", None):
                host.add_label(
                    "service_%s" % service.name, ",".join(str(x) for x in service.ports)
                )


    def _get_ip_from_record(self, data: Record, host_type: HostType):
        """
        Extract IP address from netbox Records containing a virtual machine, device or ip-address.
        See https://pynetbox.readthedocs.io/en/latest/response.html for more details on records.
        """

        if host_type == HostType.VIRTUAL_MACHINE or host_type == HostType.DEVICE:
            return str(netaddr.IPNetwork(data.primary_ip4.address).ip)

        if host_type == HostType.IP_ADDRESS:
            return str(netaddr.IPNetwork(data.address).ip)

    def _get_name_from_record(self, data: Record, host_type: HostType):
        """
        Extract name used as label __meta_netbox_name from netbox Records containing a virtual machine, device or ip-address.
        See https://pynetbox.readthedocs.io/en/latest/response.html for more details on records.
        """

        if host_type == HostType.VIRTUAL_MACHINE or host_type == HostType.DEVICE:
            return data.name

        if host_type == HostType.IP_ADDRESS:
            if getattr(data, "dns_name", None):
                return data.dns_name
            else:
                return self._get_ip_from_record(data, host_type)
