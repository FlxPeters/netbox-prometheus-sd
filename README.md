## Netbox Prometheus SD

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/FlxPeters/netbox-prometheus-sd/workflows/CI/badge.svg?event=push)](https://github.com/FlxPeters/netbox-prometheus-sd/actions?query=workflow%3ACI)
[![Dockerhub](https://img.shields.io/docker/pulls/flxpeters/prometheus-netbox-sd.svg)](https://hub.docker.com/r/flxpeters/prometheus-netbox-sd)

File based service discovery script for [Prometheus](https://prometheus.io/).
Make virtual machines and devices managed in [Netbox](https://github.com/digitalocean/netbox) as Prometheus targets with labels.

## Roadmap to 0.1

- [x] Add build process for tagged Docker builds
- [ ] Add better unit tests

## Requirement

- Python >= 3.7
- [Pynetbox](https://github.com/digitalocean/pynetbox/).

## Config

The app is configured with env variables.

```yaml
    NETBOX_SD_URL: https://netboxdemo.com
    NETBOX_SD_TOKEN:  72830d67beff4ae178b94d8f781842408df8069d
    NETBOX_FILTER: "{\"status\":\"active\",\"site\":\"ds9\"}"
    NETBOX_SD_FILE_PATH: /data/netbox/netbox.json
    NETBOX_SD_LOG_LEVEL: "DEBUG"
    NETBOX_SD_VERIFY_SSL: "FALSE"
    NETBOX_THREADING: "True"
    NETBOX_SD_LOOP_DELAY: "60"
    NETBOX_SD_METRICS_PORT: "8000"
    NETBOX_OBJECTS: "vm device" # space separated list of netbox objects to discover. Currently supported: vm, device and ip_address
```

Filters are applied as JSON which is mapped to Netbox filter criterias.  
See the Netbox for more Details: https://netbox.readthedocs.io/en/stable/rest-api/filtering/

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

## Thanks & Credits

This project is based on a Script from ENIX SAS:
* https://github.com/enix/netbox-prometheus-sd
* https://enix.io/fr/blog/service-discovery-avec-netbox-et-prometheus/
