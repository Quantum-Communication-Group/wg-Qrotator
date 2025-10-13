---
title: Security considerations
layout: default
nav_enabled: true
nav_order: 6
---

# Security Consideration

{: .disclaimer }
No security guarantees are provided by the creators, maintainers, contributors, and respective organizations. Perform an always advised risk assessment before deploying it in a production environment. `wg-Qrotator` is distributed under the AGPLv3 license.

## Communication security between rotators

As mentioned multiple times within this documentation, peer rotators must communicate through an already established secure communication channel. For a lot of solutions this would be a serious deployment headache, but in our scenario is not since `wg-Qrotator` only makes sense to be deployed if a tunnel established WireGuard exists. So, a rotator should be exposed on the host IP inside the respective WireGuard VPN. If a PSK is set during the setup of the tunnel, the risk imposed by the quantum threat is mitigated from the beginning. Nonetheless, this approach only provides guarantees against a third-party (Eve) but not against malware installed in the same host where the rotator is deployed. This is due to the fact that any program inside the host in most scenarios will be able to communicate through the network interfaces managed by WireGuard. Consequently, an athentication mechanism based on 32 byte cookie stored in an encrypted file at each host was introduced. This protects against replay and impersonation attacks from a different user in the rotator's host. Each tunnel rotated by `wg_Qrotator` has its cookie own cookie that is shared with the respective peer. Cookies are generated from the generated keys and are used to generate an authenticated NONCE (i.e. more similar actually to a MAC) that is introduced in every message sent and verified by the peer. This introduces the need for a password to encrypt the file where the keys are stored. Cookies are kept even when the rotator is restarted even though some entropy is introduced at the beginning to prevent message replay attacks. This protection is limited during the first key establishment of a never seen before tunnel, since no key was yet established in order to create the first cookie. Nonetheless, at the user's risk, the cookie storage can be populated beforehand, check [keyring](https://pypi.org/project/keyring/) and [keyring](https://pypi.org/project/keyrings.alt/). As an example, the cookie for `wg0` peer at `10.0.0.2` is stored in the keyring with `service_name = "wg-qrotator"` and `user = "wg0_10.0.0.2"`.

## Logs

Currently, by setting the `debug` parameter in the configuration file to `true` will trigger each generated key to be logged in plaintext, use this only for testing. Also, there's no mechanism in place to limit the size of the log files. 


