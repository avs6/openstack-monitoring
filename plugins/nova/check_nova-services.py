#!/usr/bin/python

import argparse
import novaclient
from novaclient.v1_1 import client as nova
import sys

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

RESERVED = "RESERVED CAPACITY"

parser = argparse.ArgumentParser(
    description='Check an Openstack Nova service.')

parser.add_argument("--host", dest="host", default="localhost",
                    help="host to check", metavar="HOST")

parser.add_argument("--binary", dest="binary", default="nova-compute",
                    help="service to check", metavar="SERVICE")

parser.add_argument("--auth_url", dest="auth_url",
                    default="http://localhost:35357/v2.0",
                    help="authentication URL", metavar="AUTHURL")

parser.add_argument("--username", dest="username", default="admin",
                    help="username", metavar="USERNAME")

parser.add_argument("--password", dest="password", default="password",
                    help="password", metavar="PASSWORD")

parser.add_argument("--tenant", dest="tenant", default="admin",
                    help="tenant", metavar="TENANT")

parser.add_argument('--endpoint_type', metavar='endpoint_type', type=str,
                    default="publicURL",
                    help='Endpoint type in the catalog request.')

args = parser.parse_args()

client = nova.Client(username=args.username,
                     api_key=args.password,
                     project_id=args.tenant,
                     auth_url=args.auth_url,
                     endpoint_type=args.endpoint_type,
                     service_type='compute')

try:
    services = client.services.list(host=args.host,
                                    binary=args.binary)
except novaclient.exceptions.Unauthorized:
    print("Failed to authenticate to Keystone")
    sys.exit(-1)
except Exception:
    print("Failed to query service")
    sys.exit(-1)

if not services:
    print("Service %s on host %s could not be found" %
          (args.binary, args.host))
    sys.exit(UNKNOWN)

else:
    service = services[0]

    if service.status == "enabled" and service.state == "up":
        print("Service %s on host %s is operational" %
              (args.binary, args.host))
        sys.exit(OK)

    elif service.status == "disabled":
        if (service.binary == "nova-compute" and
            service.disabled_reason == RESERVED):
            print("Service %s on host %s is reserved" %
                  (args.binary, args.host))
            sys.exit(OK)

        print("Service %s on host %s is disabled" %
              (args.binary, args.host))
        sys.exit(WARNING)

    elif service.state == "down":
        print("Service %s on host %s is down" %
              (args.binary, args.host))
        sys.exit(CRITICAL)

    else:
        print("Service %s on host %s is in an unknown state" %
              (args.binary, args.host))
        sys.exit(UNKNOWN)
