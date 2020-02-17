#!/usr/bin/env python3

import sys
import argparse
from pyunifi.controller import Controller
from pssh.clients import ParallelSSHClient
from pssh.utils import enable_host_logger
import unifiutil
from termcolor import cprint


parser = argparse.ArgumentParser(description='Run command in parallel on Unifi APs.')
parser.add_argument('command', nargs=argparse.REMAINDER,
                    help='the command to run.')

unifiutil.add_default_args(parser)

args = parser.parse_args()
config = unifiutil.handle_args(args)

command = ' '.join(args.command)

if not command:
    print("No command specified")
    sys.exit(1)


c = unifiutil.get_controller(config)

sites = c.get_sites()

for site in sites:
    print("\n\n=== SITE: " + site['desc'] + "===\n")

    if site['role'] != 'admin':
        print("User does not have admin role on site %s" % (site['desc']), file=sys.stderr)
        sys.exit(1)

    c.switch_site(site['desc'])

    site_mgmt_settings = c.get_setting('mgmt')['mgmt']

    if not 'x_ssh_enabled' in site_mgmt_settings or site_mgmt_settings['x_ssh_enabled'] != True:
        print("SSH not enabled on site", file=sys.stderr)
        sys.exit(1)

    if not 'x_ssh_auth_password_enabled' in site_mgmt_settings or site_mgmt_settings['x_ssh_auth_password_enabled'] != True:
        print("SSH password auth not enabled on site", file=sys.stderr)
        sys.exit(1)

    ssh_username = site_mgmt_settings['x_ssh_username']
    ssh_password = site_mgmt_settings['x_ssh_password']

    hosts = []
    names = {}

    for ap in c.get_aps():
        if 'disabled' in ap and ap['disabled']:
            print("(skipping disabled AP %s)" % (ap['name']))
        else:
            hosts.append(ap['ip'])
            names[ap['ip']] = ap['name']

    client = ParallelSSHClient(hosts, user=ssh_username, password=ssh_password)

    output = client.run_command(command, stop_on_errors=False)

    client.join(output)
    
    for host, host_output in output.items():
        out = "%s (%s) exit code: %s\n" % (names[host], host, host_output.exit_code)
        if host_output.exception:
            out += "Exception: %s\n" % (str(host_output.exception))

        if sys.stdout.isatty() and (host_output.exception or host_output.exit_code != 0):
            cprint(out, color='red', attrs=['bold'], end='')
        else:
            print(out, end='')

        if not host_output.exception:
            for line in host_output.stdout:
                print(line)
                        

