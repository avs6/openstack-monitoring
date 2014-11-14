# Check Nova

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


## Example.

I want to check every 30 minutes that the vm creation is working.  I
estimate that about 3 minutes for the creation of a vm is too long.  I
want to override the endpoint url return by the catalog to be able to
specify one a the api server behind the load balancer.

So every 30 minutes nagios trigger this check:

* `cache_check.py -c "check_nova-instance.py --auth_url $OS_AUTH_URL --username $OS_USERNAME --tenant $OS_TENANT_NAME --password $OS_PASSWORD --api_version '2' --instance_name 'test_from_api3' --timeout 180 --endpoint_url http://localhost" -e 1920 -t 185 -i 1680`

* -e 1920 -t  185 -i 1680:
    * the cache is expired when older than 32 minutes;
    * command timeout about 3 minutes 5 secondes;
    * the command won't be run more that once every 28 minutes (-i 1680);
