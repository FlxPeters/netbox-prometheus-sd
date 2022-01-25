from netbox_sd.model import Host, HostList, HostType


def test_host_labels():
    h = Host(1, "foo.bar.example.com", "10.10.10.10", HostType.VIRTUAL_MACHINE)
    h.add_label("custom_field_foo", "bar")
    h.add_label("custom_field_foo/bar", "foobar")
    # h.add_label("tag_key", "value")
    # h.add_label("tag_complex", "tag:value")
    # h.add_label("tag_replaced-char", "dash")

    assert h.labels == {
        "__meta_netbox_ip": "10.10.10.10",
        "__meta_netbox_name": "foo.bar.example.com",
        "__meta_netbox_type": "vm",
        "__meta_netbox_id": "1",
        "__meta_netbox_custom_field_foo": "bar",
        "__meta_netbox_custom_field_foo_bar": "foobar",
        # "__meta_netbox_tag_complex": "tag:value",
        # "__meta_netbox_tag_replaced_char": "dash",
    }


def test_host_to_prometheus_format():
    """ Test host is serialized to prometheus sd json format """

    h = Host(1, "foo.bar.example.com", "10.10.10.10", HostType.VIRTUAL_MACHINE)
    h.add_label("tenant", "Acme")

    out = h.to_sd_json()
    assert out["targets"] == ["10.10.10.10"]
    assert out["labels"] == {
        "__meta_netbox_ip": "10.10.10.10",
        "__meta_netbox_name": "foo.bar.example.com",
        "__meta_netbox_type": "vm",
        "__meta_netbox_id": "1",
        "__meta_netbox_tenant": "Acme",
    }


def test_host_list_add_hosts():

    host_list = HostList()
    host_list.add_host(
        Host(1, "foo.bar.example.com", "10.10.10.10", HostType.VIRTUAL_MACHINE)
    )
    host_list.add_host(
        Host(2, "baz.bar.example.com", "10.10.10.11", HostType.VIRTUAL_MACHINE)
    )

    assert len(host_list.hosts) == 2


def test_host_list_add_duplicate_id_host():

    host_list = HostList()
    host_list.add_host(
        Host(1, "foo.bar.example.com", "10.10.10.10", HostType.VIRTUAL_MACHINE)
    )
    host_list.add_host(
        Host(2, "baz.bar.example.com", "10.10.10.11", HostType.VIRTUAL_MACHINE)
    )
    host_list.add_host(
        Host(2, "baz.bar.example.com", "10.10.10.11", HostType.VIRTUAL_MACHINE)
    )
    host_list.add_host(Host(2, "baz.bar.example.com", "10.10.10.11", HostType.DEVICE))

    assert len(host_list.hosts) == 3
