# Check Cinder

## Links

* CloudWatt [monitoring documentation](https://projetx.enovance.com/index.php/Op%C3%A9rations/Monitoring_Openstack)

## Requirements

* python
* python-cinderclient

## Arguments

### Optional arguments

* `-h`: Show the help message and exit
* `--auth_url`: Keystone URL
* `--username`: Username to use for authentication
* `--password`: Password to use for authentication
* `--tenant`: Tenant name to use for authentication
* `--region_name`: Region to select for authentication
* `--endpoint_url`: Override the catalog endpoint
* `--endpoint_type`: When not overriding, which type to use in the catalog.  Public by default.
* `--volume_name`: Name of the volume to create (monitoring_test by default)
* `--volume_size`: Size of the volume to create (1 GB by default)
* `--force_delete`: If matching volumes are found, delete them and add a notification in the message instead of getting out in critical state.
* `--api_version`: Version of the API to use. 1 by default.
* `--timeout`: Max number of second to create/destroy a volume (120 by default).
* `--verbose`: Print requests on stderr

## Usage

* `check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --volume_name 'monitoring_test2 --endpoint_url http://localhost`

For a asynchronous usage relative to a nagios check, one can use [cache_check.py](https://github.com/gaelL/nagios-cache-check)

* `cache_check.py -c "check_cinder-volume.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --volume_name 'monitoring_test2 --endpoint_url http://localhost"`
