---
title: genprivkey
layout: default
nav_enabled: true
nav_order: 5
parent: CLI
---

## `genprivkey` command

```bash
wg-qrotator genprivkey <kem>
```

Generate a new private key for the indicated KEM and output it formatted in base64 to the standard output.  

### Positional arguments

- `kem` - KEM to be used. Options: ['ML_KEM_512', 'ML_KEM_768', 'ML_KEM_1024']

### Options

- `-h`, `--help` -  show help message

### Examples

Generate a private key for ML-KEM-1024 and store it in a file named "priv.key": 
```bash
wg-qrotator genprivkey ML_KEM_1024 > priv.key
```
