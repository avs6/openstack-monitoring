#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Keystone monitoring script for Nagios
#
# Copyright © 2012-2014 eNovance <licensing@enovance.com>
#
# Authors:
#   Sofer Athlan-Guyot <sofer.athlan@enovance.com>
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
# Requirments: python-neutronclient, python-argparse, python

import sys
import argparse
from keystoneclient.v2_0 import client
from neutronclient.neutron import client as neutron 
#from neutronclient import exceptions
import time
import logging
import urlparse
from datetime import datetime

DAEMON_DEFAULT_PORT = 9696

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3


def script_unknown(msg):
    sys.stderr.write("UNKNOWN - %s\n" % msg)
    sys.exit(STATE_UNKNOWN)


def script_critical(msg):
    sys.stderr.write("CRITICAL - %s\n" % msg)
    sys.exit(STATE_CRITICAL)


# python has no "toepoch" method: http://bugs.python.org/issue2736
# now, after checking http://stackoverflow.com/a/16307378,
# and http://stackoverflow.com/a/8778548 made my mind to this approach
def totimestamp(dt=None, epoch=datetime(1970, 1, 1)):
    if not dt:
        dt = datetime.utcnow()
    td = dt - epoch
    # return td.total_seconds()
    return int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)
               / 1e6)

def mangle_url(orig_url, url):
    try:
        endpoint_url = urlparse.urlparse(url)
    except Exception as e:
        script_unknown("you must provide an endpoint_url in the form"
                       + "<scheme>://<url>/ (%s)\n" % e)
    scheme = endpoint_url.scheme
    if scheme is None:
        script_unknown("you must provide an endpoint_url in the form"
                       + "<scheme>://<url>/ (%s)\n" % e)
    catalog_url = urlparse.urlparse(orig_url)

    port = endpoint_url.port
    if port is None:
        if catalog_url.port is None:
            port = DAEMON_DEFAULT_PORT
        else:
            port = catalog_url.port

    netloc = "%s:%i" % (endpoint_url.hostname, port)
    url = urlparse.urlunparse([scheme,
                               netloc,
                               catalog_url.path,
                               catalog_url.params,
                               catalog_url.query,
                               catalog_url.fragment])
    return url

class Novautils:
    def __init__(self, nova_client):
        self.nova_client = nova_client
        self.msgs = []
        self.start = totimestamp()
        self.notifications = ["floatingip_creation_time=%s" % self.start]
        self.connection_done = False
        self.all_floating_ips = []
        self.fip = None

    def check_connection(self, force=False):
        if not self.connection_done or force:
            try:
                # force a connection to the server
                self.connection_done = self.nova_client.list_ports()
            except Exception as e:
                script_critical("Cannot connect to neutron: %s\n" % e)

    def get_duration(self):
        return totimestamp() - self.start

    def list_floating_ips(self):
        if not self.all_floating_ips:
            # TODO: my setup does not have pagination enable, so I didn't
            # took this into account.
            for floating_ip in self.nova_client.list_floatingips(fields=['floating_ip_address', 'id'])['floatingips']:
                self.all_floating_ips.append(floating_ip)
        return self.all_floating_ips
                
    def check_existing_floatingip(self, floating_ip=None, delete=False):
        count = 0
        found_ips = []
        for ip in self.list_floating_ips():
            if floating_ip == 'all' or ip['floating_ip_address'] == floating_ip:
                if delete:
                    # asynchronous call, we do not check that it worked
                    self.nova_client.delete_floatingip(ip['id'])
                found_ips.append(ip['floating_ip_address'])
                count += 1
        if count > 0:
            if delete:
                self.notifications.append("Found %d ip(s) :%s"
                                          % (count, ', '.join(found_ips)))
            else:
                self.msgs.append("Found %d ip(s): %s. "
                                 % (count,  ', '.join(found_ips))
                                 + "Won't create test floating ip. "
                                 + "Please check and delete.")

    def create_floating_ip(self, router_name):
        if not self.msgs:
            try:
                network_id = self.nova_client.list_networks(name=router_name,fields='id')['networks'][0]['id']
                body={'floatingip': {'floating_network_id': network_id}}
                self.fip = self.nova_client.create_floatingip(body=body)
                self.notifications.append("fip=%s" % self.fip['floatingip']['floating_ip_address'])
            except Exception as e:
                self.msgs.append("Cannot create a floating ip: %s" % e)

    def delete_floating_ip(self):
        if not self.msgs:
            try:
                self.nova_client.delete_floatingip(self.fip['floatingip']['id'])
            except Exception as e:
                self.msgs.append("Cannot remove floating ip %s" % self.fip['floatingip']['id'])



parser = argparse.ArgumentParser(
    description='Check an Floaiting ip creation. Note that\'s it\'s able to delete *all* floating ips from a account, so ensure that nothing important is running on the specified account.')
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
                    help='Endpoint type in the catalog request. '
                    + 'Public by default.')

parser.add_argument('--force_delete', action='store_true',
                    help='If matching floating ip are found, delete them and add '
                    + 'a notification in the message instead of getting out '
                    + 'in critical state.')

parser.add_argument('--timeout', metavar='timeout', type=int,
                    default=120,
                    help='Max number of second to create/delete a floating ip '
                    + '(120 by default).')

parser.add_argument('--floating_ip', metavar='floating_ip', type=str,
                    default=None,
                    help='IP to check for existance.  This value should be "all" '
                    + 'as it\'s not possible to create a specific ip. '
                    + 'It is not by default, to avoid catastrophes ...')

parser.add_argument('--ext_router_name', metavar='ext_router_name', type=str,
                    default='public',
                    help='Name of the "public" router (public by default)')

parser.add_argument('--verbose', action='count',
                    help='Print requests on stderr.')

args = parser.parse_args()

# this shouldn't raise any exception as no connection is done when
# creating the object.  But It may change, so I catch everything.
try:
    nova_client = client.Client(
        username=args.username,
        tenant_name=args.tenant,
        password=args.password,
        auth_url=args.auth_url,
    )
    nova_client.authenticate()
except Exception as e:
    script_critical("Authentication error: %s\n" % e)

try:
    endpoint = nova_client.service_catalog.get_endpoints('network')['network'][0][args.endpoint_type]
    if args.endpoint_url:
        endpoint = mangle_url(endpoint, args.endpoint_url)

    token = nova_client.service_catalog.get_token()['id']
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    neutron_client = neutron.Client('2.0', endpoint_url=endpoint, token=token)

except Exception as e:
    script_critical("Error creating neutron object: %s\n" % e)

util = Novautils(neutron_client)

# Initiate the first connection and catch error.
util.check_connection()

util.check_existing_floatingip(args.floating_ip, args.force_delete)
util.create_floating_ip(args.ext_router_name)
util.delete_floating_ip()

if util.msgs:
    script_critical(", ".join(util.msgs))

duration = util.get_duration()
notification = ""

if util.notifications:
    notification = "(" + ", ".join(util.notifications) + ")"

print("OK - Floating ip created and deleted %s| time=%d"
      % (notification, duration))
sys.exit(STATE_OK)
