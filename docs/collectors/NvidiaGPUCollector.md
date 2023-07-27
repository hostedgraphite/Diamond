<!--This file was generated from the python source
Please edit the source to make changes
-->
NvidiaGPUCollector
=====

The NvidiaGPUCollector collects GPU utilization metric using nvidia-smi.

See https://developer.nvidia.com/nvidia-system-management-interface

#### Dependencies

 * nvidia-smi
 * nvidia-ml-py (Optional)

#### Options

| Setting                | Default                                                                                              | Description                                                                                   | Type     |
|------------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|----------|
| bin                    | /usr/bin/nvidia-smi                                                                                  | The path to the nvidia-smi binary                                                             | str      |
| byte_unit              | byte                                                                                                 | Default numeric output(s)                                                                     | str      |
| enabled                | False                                                                                                | Enable collecting these metrics                                                               | bool     |
| measure_collector_time | False                                                                                                | Collect the collector run time in ms                                                          | bool     |
| metrics_blacklist      | None                                                                                                 | Regex to match metrics to block. Mutually exclusive with metrics_whitelist                    | NoneType |
| metrics_whitelist      | None                                                                                                 | Regex to match metrics to transmit. Mutually exclusive with metrics_blacklist                 | NoneType |
| stats                  | index, memory.total, memory.used, memory.free, utilization.gpu, utilization.memory, temperature.gpu, | A list of Nvidia GPU stats to collect. Use `nvidia-smi --help-query-gpu` for more information | list     |
| sudo_cmd               | /usr/bin/sudo                                                                                        | Path to sudo                                                                                  | str      |
| use_sudo               | False                                                                                                | Use sudo?                                                                                     | bool     |

#### Example Output

```
servers.hostname.nvidia.gpu_0.memory.free 1425
servers.hostname.nvidia.gpu_0.memory.total 4095
servers.hostname.nvidia.gpu_0.memory.used 2670
servers.hostname.nvidia.gpu_0.temperature.gpu 53
servers.hostname.nvidia.gpu_0.utilization.gpu 0
servers.hostname.nvidia.gpu_0.utilization.memory 0
servers.hostname.nvidia.gpu_1.memory.free 1425
servers.hostname.nvidia.gpu_1.memory.total 4095
servers.hostname.nvidia.gpu_1.memory.used 2670
servers.hostname.nvidia.gpu_1.temperature.gpu 44
servers.hostname.nvidia.gpu_1.utilization.gpu 0
servers.hostname.nvidia.gpu_1.utilization.memory 0
servers.hostname.nvidia.gpu_2.memory.free 2658
servers.hostname.nvidia.gpu_2.memory.total 4095
servers.hostname.nvidia.gpu_2.memory.used 1437
servers.hostname.nvidia.gpu_2.temperature.gpu 48
servers.hostname.nvidia.gpu_2.utilization.gpu 0
servers.hostname.nvidia.gpu_2.utilization.memory 0
servers.hostname.nvidia.gpu_3.memory.free 2658
servers.hostname.nvidia.gpu_3.memory.total 4095
servers.hostname.nvidia.gpu_3.memory.used 1437
servers.hostname.nvidia.gpu_3.temperature.gpu 44
servers.hostname.nvidia.gpu_3.utilization.gpu 0
servers.hostname.nvidia.gpu_3.utilization.memory 0
```

