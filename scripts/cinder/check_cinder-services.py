#!/usr/bin/python

import sys
from optparse import OptionParser
import cinderclient
from cinderclient.v1 import client as cinder

OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

parser = OptionParser()
parser.add_option("--host", dest="host", default="localhost",
                  help="host to check", metavar="HOST")
parser.add_option("--binary", dest="binary", default="cinder-volume",
                  help="service to check", metavar="SERVICE")
parser.add_option("--auth_url", dest="auth_url", default="http://localhost:35357/v2.0",
                  help="authentication URL", metavar="AUTHURL")
parser.add_option("--user", dest="username", default="admin",
                  help="username", metavar="USERNAME")
parser.add_option("--password", dest="password", default="password",
                  help="password", metavar="PASSWORD")
parser.add_option("--tenant", dest="tenant", default="admin",
                  help="tenant", metavar="TENANT")

(options, args) = parser.parse_args()

client = cinder.Client(username = options.username,
                       api_key = options.password,
                       project_id = options.tenant,
                       auth_url = options.auth_url,
                       insecure = True,
                       service_type = 'volume')

try:
    services = client.services.list(host=options.host,
                                    binary=options.binary)
except cinderclient.exceptions.Unauthorized:
    print "Failed to authenticate to Keystone"
    raise
except:
    print "Failed to query service"
    raise

if not services:
    print "Service %s on host %s could not be found" \
           % (options.binary, options.host)
    sys.exit(UNKNOWN)

else:
    service = services[0]

    if service.status == "enabled" and service.state == "up":
        print "Service %s on host %s is operational" % \
              (options.binary, options.host)
        sys.exit(OK)

    elif service.status == "disabled":
        print "Service %s on host %s is disabled" \
              % (options.binary, options.host)
        print sys.exit(WARNING)

    elif service.state == "down":
        print "Service %s on host %s is down" \
              % (options.binary, options.host)
        sys.exit(CRITICAL)        

    else:
        print "Service %s on host %s is in an unknown state" \
              % (options.binary, options.host)
        sys.exit(UNKNOWN)
