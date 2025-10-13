---
title: Example deploy
layout: default
nav_enabled: true
nav_order: 4
parent: Get started
---

## Example deploy

![Example network](/assets/example_network.png)

An **example on how to setup the key rotator of Node A** in the network above to support the links with Node B and Node C is provided here. Each node has only one network interface managed by WireGuard, `wg0`, and each node is publicly identified by its IP within the VPN, its WireGuard public key, and its Secure Application Entity (SAE) ID within the QKD network. Since, ML-KEM PQ-KE is going to be enabled, each node has also a ML-KEM public key.

```yml
# rotator.yml
interface: wg0
kms: 
  uri: https://192.168.1.252/api/v1/keys
  certificate: sae_001.crt
  root_certificate: root.crt
  secret_key: sae_001.key
  sae: sae_001
  interface: 14
ip: 10.0.0.1
port: 2345
peers:
  - IXqrmMgraj1Dn4LNKVL1zx4yDsroGNXRWy+yGYshfhY=: 
      ip: 10.0.0.2
      port: 2345
      sae: sae_002
      mode: server
  - l0Oxjz2L9iJVAWeL/6HcwCWOdMsFQFuln08VKoxayjU=: 
      ip: 10.0.0.3
      port: 2345
      sae: sae_003
      mode: server
      extra_handshakes:
      - ML_KEM_1024:  
          secret_key: nodeA_priv.key
          public_key: nodeB_pub.key
```

The configuration above says the following:
- WireGuard network interface to manage is `wg0`;
- the KMS to get quantum-generated keys is accessible via the `https://192.168.1.252/api/v1/keys`;
- use the certificates in the files `sae_001.crt`, `root.crt`, and the key in `sae_001.key` to establish a connection with the KMS;
- the rotator has the `sae_001` SAE ID;
- the standard interface to be used to interact with the KMS is the ETSI GS QKD 014;
- the rotator is exposed on `10.0.0.1:2345` (10.0.0.1 must be the IP assigned to `wg0`);
- the rotator is applied for the tunnel with the peer identified by the WireGuard public key `IXqrmMgraj1Dn4LNKVL1zx4yDsroGNXRWy+yGYshfhY=`. The peer's rotator is accessible at `10.0.0.2:2345` within the QKD network is identified by the `sae_002` SAE ID and Node's A rotator acts as the server.
- the rotator is also applied for the tunnel with the peer identified by the WireGuard public key `l0Oxjz2L9iJVAWeL/6HcwCWOdMsFQFuln08VKoxayjU=`. The peer's rotator is accessible at `10.0.0.3:2345` within the QKD network is identified by the `sae_003` SAE ID and Node's A rotator acts as the server. Also, an extra key exchange with ML-KEM 1024 is activated using the private key in `nodeA_priv.key` and the public key in `nodeB_pub.key`. Key generation for any supported KEM can done by using the [`wg-qrotator gen_priv_key`](/cli/gen_priv_key) and [`wg-qrotator gen_pub_key`](/cli/gen_pub_key) commands.

The rotator can be started by performing the following command:
```bash
wg-qrotator up rotator.yml
```

The same configuration concepts apply to the other nodes.

