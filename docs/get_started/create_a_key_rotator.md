---
title: Create a key rotator
layout: default
nav_enabled: true
nav_order: 3
parent: Get started
---

## Create a key rotator

Each key rotator is attached to one WireGuard network interface. Multiple rotators can be running at the same time. Since each WireGuard interface has one or more peers (i.e. the hosts on the other side of the tunnels), each key rotator can handle one or more tunnels through the same network interface. 

Each key rotator is configured via a YAML file, as described in [Configuration](/wg-Qrotator/configuration). 

A rotator can then be started by performing the following command:
```bash
wg-qrotator up <path_to_config_file>
```

Its creation can be checked by performing:
```bash
wg-qrotator ls
```

Initially the rotator will be the "hold" state, after completing the bootstrap process with at least one of its peers, the state changes to "up". 

There's various methods that can be used to check if the rotator is working correctly or it encountered an error:
- check if in the output of `wg-qrotator` the "last key rotation" timestamp is being updated periodically;
- call `wg show wg0 preshared-keys` to check if the PSKs are being changed; 
- check the rotator's logs at `/var/log/wg_qrotatir_<interface_name>`.

{: .tip }
The key rotator only rotates keys if the tunnel is being actively used. Keys are rotated within the first 30 seconds after WireGuard performs an handshake. Under normal continuous usage of a tunnel, consecutive rotations occur about every 2 minutes.

{: .warning }
`wg-Qrotator` relies on the system's time for synchronization purposes. Make sure that peer rotators have their clocks synchronized (they should need to be in the same timezone).

   
