---
title: genpubkey
layout: default
nav_enabled: true
nav_order: 6
parent: CLI
---

## `genpubkey` command

```bash
wg-qrotator genpubkey <kem>
```

Generate the public key respective to the private key imputed in the standard input. The key is outputted formatted in base64 to the standard output.  

### Positional arguments

- `kem` - KEM to be used. Options: ['ML_KEM_512', 'ML_KEM_768', 'ML_KEM_1024']

### Options

- `-h`, `--help` -  show help message

### Examples

Generate the public key for the ML-KEM-1024 private key in "priv.key" and store it in a file named "pub.key": 
```bash
cat priv.key | wg-qrotator genprivkey ML_KEM_1024 > pub.key
```
