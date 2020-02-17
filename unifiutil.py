#!/usr/bin/env python3

import os
import configparser
import sys
from pyunifi.controller import Controller

def add_default_args(parser):
    parser.add_argument('-c', '--conf', nargs=1,
                        help='A file containing the connection configuration.')
    
#    parser.add_argument('-u', '--url', nargs=1,
#                        help='The URL of the Netbox API.')


def handle_args(args):
    if args.conf:
        if not os.path.isfile(args.conf[0]):
            print("Specified configuration file %s is not a file." % args.conf[0], file=sys.stderr)
            sys.exit(1)
        conffile = args.conf[0]
    else:
        conffile = os.path.join(os.path.expanduser('~'), '.unifirc')

    config = configparser.ConfigParser()
    config.read(conffile)

    # if section specified, use it, else use DEFAULT
    # for now, use DEFAULT

    return config['DEFAULT']


def get_controller(config):
    c = Controller(config['controller'],
                   config['user'],
                   config['password'],
                   ssl_verify=config.getboolean('ssl_verify') if 'ssl_verify' in config else True
                   )

    return c
