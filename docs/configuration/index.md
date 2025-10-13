---
title: Configuration
layout: default
nav_enabled: true
nav_order: 3
---

# Configuration

`wg-Qrotator` key rotators are configured via a YAML configuration file. This file is divided into three configurations categories:
- [general](/configuration/general.html) (`interface`, `debug`, `ip`, `port`)
- [qkd](/configuration/qkd.html) (`kms`)
- [peers](/configuration/peers.html) (`peers`)


```yml
interface: <wireguard_network_interface>
ip: <rotator_ip_address>
port: <rotator_port_number>
debug: [true|false]

kms: 
    uri: <kms_location>
    interface: <interface_identifier>
    sae: <SAE_ID>
    certificate: <SAE_certificate_file>
    secret_key: <SAE_secret_key_file>
    root_certificate: <root_CA_certificate_file>

peers:
    - <peer_wireguard_public_key>:
        ip: <peer_rotator_ip>
        port: <peer_rotator_port_number>
        sae: <peer_SAE_ID>
        mode: <local_role>
        extra_handshakes:
        - <KEM_id>:  
            secret_key: <secret_key_file>
            public_key: <peer_public_key_file>
    - ...
```
