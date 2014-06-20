# Check Cinder

## Links

* CloudWatt [monitoring documentation](https://projetx.enovance.com/index.php/Op%C3%A9rations/Monitoring_Openstack)

## Requirements

* python
* python-cinderclient

## Arguments

### Required arguments
* `--auth_url`: Keystone URL
* `--username`: Username to use for authentication
* `--password`: Password to use for authentication
* `--tenant`: Tenant name to use for authentication

### Optional arguments

* `-h`: Show the help message and exit
* `--region_name`: Region to select for authentication
* `--endpoint_url`: Override the catalog endpoint
* `--endpoint_type`: When not overriding, which type to use in the catalog.  Public by default.
* `--volume_name`: Name of the volume to create (monitoring_test by default)
* `--volume_size`: Size of the volume to create (1 GB by default)
* `--volume_type`: With multiple backends, choose the volume type.
* `--availability_zone`: Specify availability zone.
* `--force_delete`: If matching volumes are found, delete them and add a notification in the message instead of getting out in critical state.
* `--api_version`: Version of the API to use. 1 by default.
* `--timeout`: Max number of second to create/destroy a volume (120 by default).
* `--verbose`: Print requests on stderr

## Usage

Create a test volume and delete it, only if no volume match
`volume_name` (here `monitoring_test` by default).  If there is any
volume it assumes that it's some leftover and exit in CRITICAL state,
notifying the rogue volumes.  Good for testing that everything works
properly in your environment.

* `check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD`

Here we mangle the endpoint url to override the one returned by the
catalog.  If we assume that the url returned by the catalog is behind
a load balancer, this enable the user to easely choose which API
server it's going to query.

* `check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --endpoint_url http://localhost`

Here we force de deletion of any volume found with the matching name.
The number of found volume is returned in the output of the plugin.

* `check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --force_delete`

For a asynchronous usage relative to a nagios check, one can use
[cache_check.py](https://github.com/gaelL/nagios-cache-check)

* `cache_check.py -c "check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD"`
