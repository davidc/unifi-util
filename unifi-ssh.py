#!/usr/bin/env python3

import sys
import argparse
from pyunifi.controller import Controller
import unifiutil
from termcolor import cprint
from pprint import pprint
import shutil
import os
import subprocess


parser = argparse.ArgumentParser(description='Login interactively to a Unifi device via SSH.')

parser.add_argument('device', nargs=1,
                    help='The device name, enough to uniquely identify it.')

parser.add_argument('-s', '--site', nargs=1,
                    default=['ALL'],
                    help='The site to use. Performed as a substring search. Use ALL (or skip this argument) to search all sites for the device.')


unifiutil.add_default_args(parser)

args = parser.parse_args()
config = unifiutil.handle_args(args)

search_device = args.device[0].lower()
search_site = args.site[0]


sshpass = shutil.which('sshpass')

if sshpass is None:
    print("sshpass executable not found on path.", file=sys.stderr)
    sys.exit(1)


c = unifiutil.get_controller(config)

sites = c.get_sites()
found_devices = []

for site in sites:
    if search_site != 'ALL' and search_site not in site['desc']:
        continue
    
    c.switch_site(site['desc'])

    for ap in c.get_aps():
        if search_device in ap['name'].lower():
            found_devices.append((ap, site))


if len(found_devices) == 0:
    print("No device found matching the requested name.")
    sys.exit(1)
elif len(found_devices) > 1:
    print("Multiple devices found matching the requested name, please be more specific:")
    for (ap, site) in found_devices:
        print(" " + ap['name'])
    sys.exit(1)

found_device = found_devices[0][0]
found_site = found_devices[0][1]
    
if found_site['role'] != 'admin':
    print("User does not have admin role on site %s" % (site['desc']), file=sys.stderr)
    sys.exit(1)

c.switch_site(found_site['desc'])

site_mgmt_settings = c.get_setting('mgmt')['mgmt']

if not 'x_ssh_enabled' in site_mgmt_settings or site_mgmt_settings['x_ssh_enabled'] != True:
    print("SSH not enabled on site", file=sys.stderr)
    sys.exit(1)

if not 'x_ssh_auth_password_enabled' in site_mgmt_settings or site_mgmt_settings['x_ssh_auth_password_enabled'] != True:
    print("SSH password auth not enabled on site", file=sys.stderr)
    sys.exit(1)

ssh_username = site_mgmt_settings['x_ssh_username']
ssh_password = site_mgmt_settings['x_ssh_password']
ssh_host = found_device['ip']


# set up a pipe to pass password to child

r,w = os.pipe()

args = [sshpass, '-d', str(r), '-v', 'ssh', '-l', ssh_username, ssh_host]

proc = subprocess.Popen(args, pass_fds=[r])

try:
    os.close(r)
    with os.fdopen(w, 'w') as wf:
        wf.write(ssh_password)

finally:
    proc.wait()
