# Check Floating IP

## Links

* CloudWatt [monitoring documentation](https://projetx.enovance.com/index.php/Op%C3%A9rations/Monitoring_Openstack)

## Requirements

* python
* python-neutronclient
* python-keystoneclient

## Arguments

### Required arguments
* `--auth_url`: Keystone URL
* `--username`: Username to use for authentication
* `--password`: Password to use for authentication
* `--tenant`: Tenant name to use for authentication

### Optional arguments

* `-h`: Show the help message and exit
* `--endpoint_url`: Override the catalog endpoint
* `--endpoint_type`: When not overriding, which type to use in the catalog.  plublicURL by default.
* `--force_delete`: If matching volumes are found, delete them and add a notification in the message instead of getting out in critical state.
* `--timeout`: Max number of second to create/destroy a volume (120 by default).
* `--floating_ip`: Regex of IP(s) to check for existance. This value can be "all" for conveniance (match all ip). This permit to avoid certain floating ip to be kept. Its default value prevents the removal of any existing floating ip.
* `--ext_router_name`: Name of the "public" router (`public` by default)
* `--verbose`: Print requests on stderr

## Usage

Create a test floatig and delete it, only if no floating ip match
`floating_ip` (here it matches everything).  If there is any floating
ip it assumes that it's some leftover and exit in CRITICAL state,
notifying the rogue ips.  Good for testing that everything works
properly in your environment.

* `./check_floating-ip.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --floating_ip=all`


Create a test floating ip and delete it.  Assumes that the account is
dedicated for test and remove *any* floating ip found under the
account.

* `./check_floating-ip.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --floating_ip=all --force_delete`


Create a test floating ip and delete it, but keep all ips from
172.16.18.1 to 172.16.18.99 intact.  It should be noted, that if the
created floating ip is 172.16.18.73 for instance, it *will* be
removed.  Only existing floating ips are preserved.

* `./check_floating-ip.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --floating_ip='172\.16\.18\.[12][0-9][0-9]' --force_delete`
