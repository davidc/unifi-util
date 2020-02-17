# unifi-util
Utilities for a Unifi SDN contorller

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
