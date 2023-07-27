<!--This file was generated from the python source
Please edit the source to make changes
-->
KafkaConsumerLagCollector
=====

The KafkaConsumerLagCollector collects consumer lag metrics
using ConsumerOffsetChecker.

#### Dependencies

 * bin/kafka-run-class.sh kafka.tools.ConsumerOffsetChecker


#### Options

| Setting                | Default                           | Description                                                                   | Type     |
|------------------------|-----------------------------------|-------------------------------------------------------------------------------|----------|
| bin                    | /opt/kafka/bin/kafka-run-class.sh | The path to kafka-run-class.sh binary                                         | str      |
| byte_unit              | byte                              | Default numeric output(s)                                                     | str      |
| consumer_groups        |                                   | Consumer groups                                                               |          |
| enabled                | False                             | Enable collecting these metrics                                               | bool     |
| measure_collector_time | False                             | Collect the collector run time in ms                                          | bool     |
| metrics_blacklist      | None                              | Regex to match metrics to block. Mutually exclusive with metrics_whitelist    | NoneType |
| metrics_whitelist      | None                              | Regex to match metrics to transmit. Mutually exclusive with metrics_blacklist | NoneType |
| sudo_cmd               | /usr/bin/sudo                     | Path to sudo                                                                  | str      |
| topic                  |                                   | Comma-separated list of consumer topics.                                      |          |
| use_sudo               | False                             | Use sudo?                                                                     | bool     |
| zookeeper              | localhost:2181                    | ZooKeeper connect string.                                                     | str      |

#### Example Output

```
__EXAMPLESHERE__
```

