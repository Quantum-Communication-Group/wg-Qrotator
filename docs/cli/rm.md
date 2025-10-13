---
title: rm
layout: default
nav_enabled: true
nav_order: 3
parent: CLI
---

## `rm` command

```bash
wg-qrotator rm <interface_name>
```

Removes the rotator attached to the indicated interface from the internal state storage.  

### Positional arguments

- `interface` - name of the WireGuard interface managed by the rotator to be removed

### Options

- `-h`, `--help` -  show help message

### Examples

Remove the rotator that managed `wg0`

```bash
wg-qrotator rm wg0
```


