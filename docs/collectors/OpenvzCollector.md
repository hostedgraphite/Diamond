<!--This file was generated from the python source
Please edit the source to make changes
-->
OpenvzCollector
=====

OpenvzCollector grabs stats from Openvz and submits them the Graphite

#### Dependencies

 * /usr/sbin/vzlist


#### Options

| Setting                | Default          | Description                                                                   | Type     |
|------------------------|------------------|-------------------------------------------------------------------------------|----------|
| bin                    | /usr/sbin/vzlist | The path to the vzlist                                                        | str      |
| byte_unit              | byte             | Default numeric output(s)                                                     | str      |
| enabled                | False            | Enable collecting these metrics                                               | bool     |
| keyname                | hostname         | key name for hostname metric value (hostname)                                 | str      |
| measure_collector_time | False            | Collect the collector run time in ms                                          | bool     |
| metrics_blacklist      | None             | Regex to match metrics to block. Mutually exclusive with metrics_whitelist    | NoneType |
| metrics_whitelist      | None             | Regex to match metrics to transmit. Mutually exclusive with metrics_blacklist | NoneType |

#### Example Output

```
servers.hostname.openvz.dns_home_loc.kmemsize.held 5151725
servers.hostname.openvz.dns_home_loc.laverage.01 0.01
servers.hostname.openvz.dns_home_loc.laverage.05 0.05
servers.hostname.openvz.dns_home_loc.laverage.15 0.15
servers.hostname.openvz.dns_home_loc.uptime 1316250.125
servers.hostname.openvz.mqtt_home_loc.kmemsize.held 4930969
servers.hostname.openvz.mqtt_home_loc.laverage.01 0.1
servers.hostname.openvz.mqtt_home_loc.laverage.05 0.5
servers.hostname.openvz.mqtt_home_loc.laverage.15 1.5
servers.hostname.openvz.mqtt_home_loc.uptime 126481.188
```

