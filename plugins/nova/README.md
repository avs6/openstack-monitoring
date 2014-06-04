# Check Nova

## Links

* CloudWatt [monitoring documentation](https://projetx.enovance.com/index.php/Op%C3%A9rations/Monitoring_Openstack)

## Requirements

* python
* python-novaclient

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
* `--image_name`: Image name to use (cirros-0.3.0-x86_64-disk by defalut)
* `--flavor_name`: Flavor name to use (m1.tiny by default)
* `--instance_name`: Instance name to use (monitoring_test by default)
* `--force_delete`: If matching instances are found delete them and add a notification in the message instead of getting out in critical state
* `--api_version`: Version of the API to use. 2 by default. (1.1 supported, and 3 not tested)
* `--timeout`: Max number of second to create/destroy a instance (120 by default).
* `--verbose`: Print requests on stderr

## Usage

* `check_nova-instance.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --api_version '2' --instance_name 'test_from_api' --endpoint_url http://localhost`

For a asynchronous usage relative to a nagios check, one can use [cache_check.py](https://github.com/gaelL/nagios-cache-check)

* `cache_check.py -c "check_nova-instance.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --api_version '2' --instance_name 'test_from_api3' --endpoint_url http://localhost" -e 150 -d -t 130 -i 180`
