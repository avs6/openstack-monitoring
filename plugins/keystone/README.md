# Check Keystone

## Links

* Upstream [Nagios forge](http://exchange.nagios.org/directory/Plugins/Software/check_keystone/details) URL.

## Requirements

* python
* python-keystoneclient

### Tested on dev33 with this versions

* python → 2.7.3-0ubuntu2.2
* python-keystoneclient → 1:0.4.1-2~bpo2012.04+1

## Arguments

### Optional arguments

* `-h`: Show the help message and exit
* `--auth_url`: Keystone URL
* `--username`: Username to use for authentication
* `--password`: Password to use for authentication
* `--tenant`: Tenant name to use for authentication
* `--region_name`: Region to select for authentication
* `--no-admin`: Don't perform admin tests, useful if user is not admin
* `--revoke-token`: Revoke created token after usage

### Positional arguments

* `service`: Keystone services to check for

## Usage

* `check_keystone --auth_url http://id.provider.net:5000/v2.0 --username admin --password zMuIPMVfiRY --tenant openstack identity`

* `check_keystone --auth_url http://id.provider.net:5000/v2.0 --username admin --password zMuIPMVfiRY --tenant openstack metering --revoke-token`
