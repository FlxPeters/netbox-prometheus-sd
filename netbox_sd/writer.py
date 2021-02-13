from .model import HostList, Host
import json
import os
import shutil


class PrometheusSDWriter:
    def __init__(self, file_path):
        self.file_path = file_path

    def write(self, host_list: HostList):
        output = []
        for host in host_list.hosts:
            output.append(host.to_sd_json())

        # Write to tmp file and move after write
        temp_file = "{}.tmp".format(self.file_path)
        with open(temp_file, "w") as temp_file_handle:
            json.dump(output, temp_file_handle, indent=4)

        shutil.move(temp_file, self.file_path)
