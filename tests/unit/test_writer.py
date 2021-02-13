from netbox_sd.writer import PrometheusSDWriter
from netbox_sd.model import HostList, Host, HostType
import json


def test_writer(tmpdir):

    path = tmpdir.join("test.json")
    writer = PrometheusSDWriter(path)

    host_list = HostList()
    host_list.add_host(Host(1, "foo.example.com", "10.10.10.10", HostType.DEVICE))
    host_list.add_host(
        Host(2, "bar.example.com", "10.10.10.11", HostType.VIRTUAL_MACHINE)
    )
    writer.write(host_list)

    # Assert file exists and has prometheus json
    assert path.exists
    file_content = json.loads(path.read())
    assert file_content[0]["targets"] == ["10.10.10.10"]
    assert file_content[1]["targets"] == ["10.10.10.11"]
