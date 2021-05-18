from enum import Enum
from typing import List
import logging


class HostType(Enum):
    VIRTUAL_MACHINE = "vm"
    DEVICE = "device"
    IP_ADDRESS = "ip_address"


class Host:
    """ Represents a virtual machine or device in netbox """

    def __init__(self, id, hostname, ip_address, host_type: HostType):
        self.hostname = hostname
        self.ip_address = ip_address
        self.id = id
        self.host_type = host_type
        self.labels = {}
        self.labels["__meta_netbox_ip"] = ip_address
        self.labels["__meta_netbox_name"] = hostname
        self.labels["__meta_netbox_type"] = host_type.value
        self.labels["__meta_netbox_id"] = str(id)

    def add_label(self, key, value):
        """ Add a netbox prefixed meta label to the host """
        key = key.replace("-", "_").replace(" ", "_")
        logging.debug(f"Add label '{key}' with value '{value}'")
        self.labels[f"%s_%s" % ("__meta_netbox", key)] = str(value)

    def to_sd_json(self):
        return {"targets": [self.ip_address], "labels": self.labels}


class HostList:
    """ Collection of host objects """

    def __init__(self):
        self.hosts = []

    def clear(self):
        self.hosts = []

    def add_host(self, host: Host):
        if not self.host_exists(host):
            self.hosts.append(host)

    def host_exists(self, host: Host):
        """ Check if a host is already in the list by id and type """
        for current in self.hosts:
            if current.host_type == host.host_type and current.id == host.id:
                return True
        return False
