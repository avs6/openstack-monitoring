#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Heat monitoring script for Nagios
#
# Copyright © 2012-2014 eNovance <licensing@enovance.com>
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
# Requirements: python-heatclient, python-argparse, python

import sys
import argparse
import yaml
import uuid
import time

from datetime import datetime
from heatclient import client as heat
from glanceclient import client as glance
from heatclient.common import template_utils
from keystoneclient.v2_0 import client as keystone

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

def script_critical(msg):
    sys.stderr.write("CRITICAL - %s (UTC: %s)\n" % (msg, datetime.utcnow()))
    sys.exit(STATE_CRITICAL)


def parse_properties(properties):
    props = {}
    for prop in properties: 
        try:
            name, value = prop.split('=')
        except:
            raise Exception("Property %s must be in format key=value" % prop)
        props[name.lower()] = value
    return props


def wait_for_completion(heat_client, stack_id, timeout):
    spent_time = 0

    while spent_time < timeout:
        stack = heat_client.stacks.get(stack_id)

        if stack.status == 'COMPLETE':
            break
        elif stack.status != 'IN_PROGRESS':
            raise Exception('Stack is in %s state' % stack.status)

        time.sleep(5)
        spent_time += 5

    return spent_time


def get_image(glance_client, image_name, properties):
    try:
        images = list(
                     glance_client.images.list(
                         filters={'properties': properties,
                                  'member_status': 'all',
                                  'name': image_name}
                     )
                 )

        if len(images) > 1:
            raise Exception("Image must be unique")

        return images[0]

    except Exception as e:
        raise Exception("Cannot find the image %s (%s)"
                        % (image_name, e))

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

parser.add_argument('--image_name', metavar='image_name', type=str, 
                    help="Image name to use")

parser.add_argument('--image_property', metavar='property', type=str,
                    default=[], action="append",
                    help='Image property to search')

parser.add_argument('--flavor_name', metavar='flavor_name', type=str,
                    default='m1.small',
                    help="Flavor name to use")

parser.add_argument('--template', metavar='template', type=str,
                    required=True,
                    help="Heat template to create")

parser.add_argument('--timeout', metavar='timeout', type=int,
                    default=120,
                    help='Max number of second to create a instance ')

parser.add_argument('--timeout_delete', metavar='timeout_delete', type=int,
                    default=45,
                    help='Max number of second to delete an existing instance')

parser.add_argument('--verbose', action='count',
                    help='Print requests on stderr.')

parser.add_argument('--property', metavar='property', type=str,
                    default=[], action="append",
                    help='Property for the Heat template')

args = parser.parse_args()

image_props = parse_properties(args.image_property)
props = parse_properties(args.property)

# Authenticate to Keystone and get the Heat endpoint
try:
    ksclient = keystone.Client(username=args.username,
                               tenant_name=args.tenant,
                               password=args.password,
                               auth_url=args.auth_url)

    heat_endpoint = ksclient.service_catalog.url_for(
                         service_type='orchestration',
                         endpoint_type=args.endpoint_type
                    )

    heat_client = heat.Client('1',
                              endpoint=heat_endpoint,
                              token=ksclient.auth_token)

    glance_endpoint = ksclient.service_catalog.url_for(
                          service_type='image',
                          endpoint_type=args.endpoint_type
                      )

    glance_client = glance.Client('1',
                                  endpoint=glance_endpoint,
                                  token=ksclient.auth_token)

except Exception as e:
    script_critical("Error while connecting to Heat: %s\n" % e)


if args.image_name:
    try:
        props['image_id'] = get_image(glance_client, args.image_name, image_props).id
    except Exception as e:
        script_critical("Error while connecting to Heat: %s\n" % e)
    

# Create the stack and wait for its creation
try:
    files, template = template_utils.get_template_contents(
                          template_file=args.template)

    stack_name = "check_heat-stack-" + str(uuid.uuid4())

    fields = {
        'stack_name': stack_name,
        'parameters': props,
        'template': template,
        'files': files,
        'environment': {},
        'timeout_mins': args.timeout
    }

    start_time = time.time()
    stack_id = heat_client.stacks.create(**fields)['stack']['id']

    spent_time = wait_for_completion(heat_client, stack_id, args.timeout)
    if spent_time >= args.timeout:
        script_critical("Stack creation took too long")

except Exception as e:
    script_critical("Error while creating the Heat stack: %s\n" % e)

# Wait a bit
time.sleep(5)

# Now delete the stack and wait for its deletion
try:
    heat_client.stacks.delete(stack_id)
    
    spent_time = wait_for_completion(heat_client, stack_id, args.timeout_delete)
    if spent_time >= args.timeout_delete:
        script_critical("Stack deletion took too long")

except Exception as e:
    script_critical("Error while deleting the Heat stack: %s\n" % e)


end_time = time.time()
print "OK - Stack creation and deletion took %d seconds" % int(end_time - start_time)
sys.exit(STATE_OK)
