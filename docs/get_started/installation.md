---
title: Installation
layout: default
nav_enabled: true
nav_order: 2
parent: Get started
---

## Installation

Start by cloning `wg-Qrotator` repository:

```bash
git clone https://github.com/Quantum-Communication-Group/wg-Qrotator
```

From the repository's root directory install `wg-Qrotator` using the `pip` command:

```bash
pip install .
```

If the installation finishes with success, the `wg-qrotator` command should now be available.

{: .warning }
The usage of `sudo` is not mandatory in the `pip install .` as long the user performing the installation has enough permissions to monitor WireGuard. If you're not sure, check if you have permissions to perform `wg show` on the given interface.

If the `pip install .` fails, try updating `pip`:

```bash
pip install --upgrade pip
```
