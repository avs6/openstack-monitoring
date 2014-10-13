#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Nagios check to spot inconsistencies between
# the running VMs in libvirt and the one in Nova database
#
# Copyright © 2014 eNovance <licensing@enovance.com>
#
# Authors:
#   Sylvain Baubeau <sylvain.baubeau@enovance.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Requirements: python-novaclient, python-keystoneclient, python-argparse
#               python-libvirt

import sys
import argparse
from novaclient.client import Client
from novaclient import exceptions
from keystoneclient.v2_0 import client as keystone
import time
import logging
import libvirt
from datetime import datetime

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

NAGIOS_STATES = {
    STATE_OK : "OK",
    STATE_WARNING : "WARNING",
    STATE_CRITICAL : "CRITICAL",
    STATE_UNKNOWN : "UNKNOWN",
}

LIBVIRT_STATES = {
    libvirt.VIR_DOMAIN_NOSTATE:     'nostate',
    libvirt.VIR_DOMAIN_RUNNING:     'running',
    libvirt.VIR_DOMAIN_BLOCKED:     'blocked',
    libvirt.VIR_DOMAIN_PAUSED:      'paused',
    libvirt.VIR_DOMAIN_SHUTDOWN:    'shutdown',
    libvirt.VIR_DOMAIN_SHUTOFF:     'shutoff',
    libvirt.VIR_DOMAIN_CRASHED:     'crashed',
    libvirt.VIR_DOMAIN_PMSUSPENDED: 'suspended'
}


def check_status(state, msg, perf_data=""):
    sys.stderr.write("%s - %s (UTC: %s)" % \
                     (NAGIOS_STATES[state], msg, datetime.utcnow()))
    if perf_data:
        sys.stderr.write("|%s" % perf_data)

    sys.exit(state)


parser = argparse.ArgumentParser(
    description='Check an OpenStack Keystone server.')

parser.add_argument('--auth_url', metavar='URL', type=str,
                    required=True,
                    help='Keystone URL')

parser.add_argument('--username', metavar='username', type=str,
                    required=True,
                    help='username to use for authentication')

parser.add_argument('--password', metavar='password', type=str,
                    required=True,
                    help='password to use for authentication')

parser.add_argument('--tenant', metavar='tenant', type=str,
                    required=True,
                    help='tenant name to use for authentication')

parser.add_argument('--endpoint_url', metavar='endpoint_url', type=str,
                    help='Override the catalog endpoint.')

parser.add_argument('--endpoint_type', metavar='endpoint_type', type=str,
                    default="publicURL",
                    help='Endpoint type in the catalog request.'
                    + 'Public by default.')

parser.add_argument('--api_version', metavar='api_version', type=str,
                    default='2',
                    help='Version of the API to use. 2 by default.')

parser.add_argument('--protocol', metavar='protocol', type=str,
                    default='qemu+ssh', choices=['qemu+ssh', 'qemu+tcp'],
                    help='protocol to use to connect to libvirtd')

parser.add_argument('--remote_user', metavar='remote_user', type=str,
                    default='nova',
                    help='remote user to use to connect to libvirtd')

parser.add_argument('--host', metavar='host', type=str,
                    help='hypervisor hostname')

parser.add_argument('--timeout', metavar='timeout', type=int,
                    default=120,
                    help='Max number of second to create a instance'
                    + '(120 by default)')

parser.add_argument('--verbose', action='count',
                    help='Print requests on stderr.')

args = parser.parse_args()

# this shouldn't raise any exception as no connection is done when
# creating the object.  But It may change, so I catch everything.
try:
    ksclient = keystone.Client(username=args.username,
                               tenant_name=args.tenant,
                               password=args.password,
                               auth_url=args.auth_url)

    nova_endpoint = ksclient.service_catalog.url_for(
                        service_type='compute',
                        endpoint_type=args.endpoint_type
                    )

    nova_client = Client(args.api_version,
                         username=args.username,
                         api_key=ksclient.auth_token,
                         project_id=args.tenant,
                         auth_url=args.auth_url,
                         auth_token=ksclient.auth_token,
                         endpoint_type=args.endpoint_type,
                         bypass_url=nova_endpoint,
                         http_log_debug=args.verbose)

except Exception as e:
    check_status(STATE_CRITICAL,
                 "Error creating nova communication object: %s\n" % e)

if args.verbose:
    ch = logging.StreamHandler()
    nova_client.client._logger.setLevel(logging.DEBUG)
    nova_client.client._logger.addHandler(ch)


def get_virsh_vms(hostname):
    vms = {}
    if args.protocol == 'qemu+ssh':
        uri = "%s://%s@%s/system" % (args.protocol, args.remote_user, hostname)
    elif args.protocol == 'qemu+tcp':
        uri = "%s://%s/system" % (args.protocol, hostname)
    conn = libvirt.open(uri)
    domains = conn.listAllDomains()
    for domain in domains:
        vms[domain.name()] = LIBVIRT_STATES.get(domain.state()[0], 'unknown')
    return vms

def get_nova_vms(hostname):
    vms = {}
    for vm in nova_client.servers.list(search_opts={'host':hostname.split('.')[0],
                                                    'all_tenants':1}):
        instance_name = getattr(vm, "OS-EXT-SRV-ATTR:instance_name")
        if instance_name:
            vms[instance_name] = vm.status
    return vms

virsh_vms = get_virsh_vms(args.host)
nova_vms = get_nova_vms(args.host)

virsh_set = set(virsh_vms.keys())
nova_set = set(nova_vms.keys())

if virsh_set != nova_set:
    inconsistencies = []
    for diff in virsh_set.difference(nova_set):
        inconsistencies.append("%s is on the hypervisor in state %s " \
                               "and unknown to Nova" % (diff, virsh_vms[diff]))

    for diff in nova_set.difference(virsh_set):
        inconsistencies.append("%s is in the Nova database in state %s but " \
                               "not on the hypervisor" % (diff, nova_vms[diff]))

    check_status(STATE_WARNING, "Inconsistency detected",
                 '\n'.join(inconsistencies))

else:
    check_status(STATE_OK, "No inconsistency detected")
