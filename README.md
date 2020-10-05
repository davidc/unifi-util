# unifi-util
Utilities for a Unifi SDN controller.

## .unifirc

You need a configuration file, either specified by -c on the command line, or found
in the default location of .unifirc in your home directory

Section DEFAULT, values:

| Key | Purpose |
| --- | ------- |
| controller | Hostname of the controller (not URL) |
| user       | Username to login to the controller  |
| password   | Password to login to the controller  |
| ssl_verify | Set it to 'false' to disable verification of the server's SSL certificate |

Example:
```
[DEFAULT]
controller = 10.41.37.11
user = apiuser
password = Drowssap1
ssl_verify = false
```

## unifi-run

Runs a command on all or a subset of devices.

### Exit status

| Status | Meaning |
| ------ | ------- |
| 0 | Successfully ran commands on all requested APs (at least one). |
| 1 | Argument error |
| 2 | No matching APs found |
| 101 | Error returned when executing on at least one matching AP, but at least one succeeded. |
| 102 | Error returned when executing on ALL matching APs. |

### Example

Run the command ```uptime``` on all sites matching ```*office*```:

```
$ ./unifi-run.py -s office uptime
```