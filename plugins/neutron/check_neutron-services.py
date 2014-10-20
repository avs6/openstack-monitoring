#!/usr/bin/python

import sys
from optparse import OptionParser
import neutronclient
from neutronclient.v2_0 import client as neutron

OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

parser = OptionParser()
parser.add_option("--host", dest="host", default="localhost",
                  help="host to check", metavar="HOST")
parser.add_option("--binary", dest="binary", default="neutron-metadata-agent",
                  help="agent to check", metavar="AGENT")
parser.add_option("--auth_url", dest="auth_url", default="http://localhost:35357/v2.0",
                  help="authentication URL", metavar="AUTHURL")
parser.add_option("--user", dest="username", default="admin",
                  help="username", metavar="USERNAME")
parser.add_option("--password", dest="password", default="password",
                  help="password", metavar="PASSWORD")
parser.add_option("--tenant", dest="tenant", default="admin",
                  help="tenant", metavar="TENANT")

(options, args) = parser.parse_args()

client = neutron.Client(username = options.username,
                        password = options.password,
                        tenant_name = options.tenant,
                        auth_url = options.auth_url,
                        insecure = True,
                        service_type = 'network')

try:
    agents = client.list_agents()
except Exception: # neutronclient.exceptions.Unauthorized:
    print "Failed to authenticate to Keystone"
    sys.exit(-1)
except:
    print "Failed to query service"
    sys.exit(-1)

agents = filter(lambda agent: agent["host"] == options.host and agent["binary"] == options.binary,
                agents["agents"])

if not agents:
    print "Agent %s on host %s could not be found" \
           % (options.binary, options.host)
    sys.exit(UNKNOWN)

else:
    agent = agents[0]

    if agent["admin_state_up"] and agent["alive"]:
        print "Agent %s on host %s is operational" % \
              (options.binary, options.host)
        sys.exit(OK)

    elif not agent["admin_state_up"]:
        print "Agent %s on host %s is disabled" \
              % (options.binary, options.host)
        print sys.exit(WARNING)

    elif not agent["alive"]:
        print "Agent %s on host %s is down" \
              % (options.binary, options.host)
        sys.exit(CRITICAL)        

    else:
        print "Agent %s on host %s is in an unknown state" \
              % (options.binary, options.host)
        sys.exit(UNKNOWN)
