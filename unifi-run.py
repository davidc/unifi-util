#!/usr/bin/env python3

import sys
import argparse
from pyunifi.controller import Controller
from pssh.clients import ParallelSSHClient
from pssh.utils import enable_host_logger
import unifiutil
from termcolor import cprint


parser = argparse.ArgumentParser(description='Run command in parallel on Unifi devices.')

parser.add_argument('command', nargs=argparse.REMAINDER,
                    help='the command to run.')

parser.add_argument('-n', '--dry-run',
                    default=False,
                    action='store_const', const=True,
                    help='Dry run (do not actually connect to devices, just show what would be done).')

parser.add_argument('-s', '--site', nargs=1,
                    default=['ALL'],
                    help='The site to use. Performed as a substring search. Use ALL (or skip this argument) for all sites.')

parser.add_argument('-d', '--disabled',
                    default=False,
                    action='store_const', const=True,
                    help='Run command on disabled APs (by default they are skipped)')


unifiutil.add_default_args(parser)

args = parser.parse_args()
config = unifiutil.handle_args(args)

command = ' '.join(args.command)
dry_run = args.dry_run
search_site = args.site[0]
run_disabled = args.disabled


if not command:
    print("No command specified")
    sys.exit(1)


c = unifiutil.get_controller(config)

sites = c.get_sites()
found_ap = False
num_successes = 0
num_failures = 0

for site in sites:
    if search_site != 'ALL' and search_site not in site['desc']:
        continue
    
    print("\n\n=== SITE: %s ===\n" % (site['desc']))

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
        if 'disabled' in ap and ap['disabled'] and not run_disabled:
            print("(skipping disabled AP %s)" % (ap['name']))
        else:
            hosts.append(ap['ip'])
            names[ap['ip']] = ap['name']
            found_ap = True

    if dry_run:
        for host in hosts:
            print("Would connect to %s (%s) and run: %s" % (host, names[host], command))
            num_successes += 1
    else:
        client = ParallelSSHClient(hosts, user=ssh_username, password=ssh_password)

        output = client.run_command(command, stop_on_errors=False)

        client.join(output)
    
        for host, host_output in output.items():

            success = host_output.exit_code == 0 and host_output.exception is None
            if success:
                num_successes += 1
            else:
                num_failures += 1
                
            out = "%s (%s) exit code: %s\n" % (names[host], host, host_output.exit_code)
            if host_output.exception:
                out += "Exception: %s\n" % (str(host_output.exception))

            if sys.stdout.isatty() and not success:
                cprint(out, color='red', attrs=['bold'], end='')
            else:
                print(out, end='')

            try:
                if not host_output.exception:
                    for line in host_output.stdout:
                        print(line)
            except Exception as e:
                cprint("Exception reading output: %s\n" % (str(host_output.exception)), color='red', attrs=['bold'])
                                
if not found_ap:
    print("No matching APs found!", file=sys.stderr)
    sys.exit(2)

print("\nExecution summary: %d success%s, %d failure%s" % (num_successes, '' if num_successes == 1 else 'es', num_failures, '' if num_failures == 1 else 's'))

if num_failures > 0:
    if num_successes == 0:
        sys.exit(102)
    else:
        sys.exit(101)
sys.exit(0)
