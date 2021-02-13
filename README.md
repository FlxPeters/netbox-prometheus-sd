## Netbox Prometheus SD

File based service discovery script for [Prometheus](https://prometheus.io/).
Make virtual machines and devices managed in [Netbox](https://github.com/digitalocean/netbox) as Prometheus targets with labels.

## Requirement

- Python >= 3.7
- [Pynetbox](https://github.com/digitalocean/pynetbox/).

## Config

The app is configured with env variables.

    NETBOX_SD_URL=https://netbox.dev.oct.ads.eb.intern
    NETBOX_SD_TOKEN=
    NETBOX_SD_FILE_PATH=/tmp/data.json
    NETBOX_SD_LOG_LEVEL=INFO
    NETBOX_SD_VERIFY_SSL=TRUE

Note: This may change to a Tol file in the future, depending on how complex filter options are implemented.

# Usage

```
python3 netbox-prometheus-sd.py
```

The service discovery script requires the URL to the Netbox instance, an
API token that can be generated into the user profile page of Netbox and a path
to an output file.

In the Prometheus configuration, declare a new scrape job using the `file_sd_configs`
service discovery:

```
- job_name: 'netbox'
  file_sd_configs:
  - files:
    - '/path/to/my/output.json'
```

## Example

See `example` directory for an example on how this service discovery.
Currently we use netboxdemo.com for this. This should be changed to a local Docker based Netbox stack.

# Thanks & Credits

This project is based on a Script from ENIX SAS: https://github.com/enix/netbox-prometheus-sd / https://enix.io/fr/blog/service-discovery-avec-netbox-et-prometheus/
