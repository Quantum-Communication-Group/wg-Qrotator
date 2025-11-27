---
title: genauthkeys
layout: default
nav_enabled: true
nav_order: 6
parent: CLI
---

## `down` command

```bash
wg-qrotator genauthkeys <private_file_path> <public_file_path>
```

Generate ML-DSA key-pair.

### Positional arguments

- `private_filename` - path to the file where the private key will be stored
- `public_filename` - path to the file where the public key will be stored

### Options

- `-h`, `--help` - show help message

### Examples

Stop a rotator for the interface `wg0` that was previously started:

```bash
wg-qrotator genauthkeys priv.key pub.key
```