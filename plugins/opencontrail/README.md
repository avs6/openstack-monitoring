# Check Contrail

## Links

* Upstream [github](https://github.com/sbadia/contrail-nagios/) URL.
* CloudWatt [related US](https://jira.corp.cloudwatt.com/browse/INGPRD-1100).
* CloudWatt [monitoring documentation](https://wiki.corp.cloudwatt.com/wiki/Op%C3%A9rations/Monitoring_Openstack)

## Requirements

* ruby
* ruby-nokogiri

## Check\_vrouter\_xmpp

Check vrouter's xmpp connection with controller peers

### Arguments

* `-H, --host`: Hostname to run on (default: localhost)
* `-p, --port`: Vrouter API port (default: 8085)
* `-c, --cfg-ctrl`: Check only cfg-controller (default: false)
* `-m, --mcast-ctrl`: Check only mcast-controller (default: false)
* `-i, --ip-ctrl(s)`: Check this controller IPs (default: false)
* `-h, --help`: Display this help message

### Usage

* Check localhost vrouter on port 8085 (default)
>     check_vrouter_xmpp
>     UNKNOWN: Could not connect to localhost:8085 (please check)

* Check only the xmpp connection with `10.10.0.58` and `10.10.0.57` peer controller IP
>     check_vrouter_xmpp -H i-ocnclc-0000.adm.int4.aub.cloudwatt.net -i 10.10.0.58,10.10.0.57
>     OK: Peer with 10.10.0.58 is Established (last state OpenSent at 2014-Jun-22 08:10:48.772736)
>     OK: Peer with 10.10.0.57 is Established (last state OpenSent at 2014-Jun-25 20:08:29.642435)

* Check only the xmpp connection with the config controller peer
>     check_vrouter_xmpp -H i-ocnclc-0000.adm.int4.aub.cloudwatt.net -c
>     OK: Peer with 10.10.0.57 is Established (last state OpenSent at 2014-Jun-22 08:09:30.065507)

* Check only the xmpp connection with the multicast controller peer
>     check_vrouter_xmpp -H i-ocnclc-0000.adm.int4.aub.cloudwatt.net -m
>     OK: Peer with 10.10.0.57 is Established (last state OpenSent at 2014-Jun-22 08:09:30.065507)

* Check all xmpp connection peers (warning if one session is down, and critical if all are down)
>     check_vrouter_xmpp -H i-ocnclc-0000.adm.int4.aub.cloudwatt.net
>     OK: Peer with 10.10.0.57 is Established (last state OpenSent at 2014-Jun-22 08:09:30.065507)
>     OK: Peer with 10.10.0.58 is Established (last state OpenSent at 2014-Jun-22 08:10:48.772736)

## Check\_vrouter\_agent

Check vrouter's agent state

### Arguments

* `-H, --host`: Hostname to run on (default: localhost)
* `-p, --port`: Vrouter API port (default: 8085)
* `-h, --help`: Display this help message

### Usage

* Check the state of the vrouter agent

>     check_vrouter_agent -H i-ocnclc-0000.adm.int4.aub.cloudwatt.net
>     OK: i-ocnclc-0000.adm.int4.aub.cloudwatt.net in «InitDone» state

# Check\_bgp\_neighbor

Check controller's BGP neighbor

### Arguments

* `-H, --host`: Hostname to run on (default: localhost)
* `-p, --port`: Controller API port (default: 8083)
* `-a, --peer-asn(s)`: Check only this peer ASN (default: false)
* `-i, --peer-ip(s)`: Check only this peer IP (default: false)
* `-h, --help`: Display this help message

### Usage

* Check a specific ASN
>     check_bgp_neighbor -H i-octclc-0000.adm.int4.aub.cloudwatt.net -a 60940
>     OK: Peer with 10.5.250.9 AS60940 (BGP) is Established (last state OpenConfirm at 2014-Jun-23 07:13:17.284153)

* Check two specific ASN
>     check_bgp_neighbor -H i-octclc-0000.adm.int4.aub.cloudwatt.net -a 60940,64516
>     OK: Peer with 10.5.250.9 AS60940 (BGP) is Established (last state OpenConfirm at 2014-Jun-25 18:59:37.250093)
>     OK: Peer with 10.10.0.58 AS64516 (BGP) is Established (last state OpenConfirm at 2014-Jun-25 19:02:47.358415)

* Check a specific peer
>     check_bgp_neighbor -H i-octclc-0000.adm.int4.aub.cloudwatt.net -i 10.5.250.9
>     OK: Peer with 10.5.250.9 AS60940 (BGP) is Established (last state OpenConfirm at 2014-Jun-23 07:13:17.284153)

* Check a list of specific peer
>     check_bgp_neighbor -H i-octclc-0000.adm.int4.aub.cloudwatt.net -i 10.5.250.9,10.10.0.58
>     OK: Peer with 10.5.250.9 AS60940 (BGP) is Established (last state OpenConfirm at 2014-Jun-23 07:13:17.284153)
>     OK: Peer with 10.10.0.58 AS64516 (BGP) is Established (last state OpenConfirm at 2014-Jun-25 19:02:47.358415)

* Check all controller sessions (warning if one session is down, and critical if all are down)
>     check_bgp_neighbor -H i-octclc-0000.adm.int4.aub.cloudwatt.net
>     OK: Peer with 10.5.250.9 AS60940 (BGP) is Established (last state OpenConfirm at 2014-Jun-23 07:13:17.284153)
>     OK: Peer with 10.10.0.58 AS64516 (BGP) is Established (last state OpenConfirm at 2014-Jun-23 07:12:17.260555)
>     OK: Peer with 10.10.1.57 AS0 (XMPP) is Established (last state Active at 2014-Jun-23 07:11:12.342093)
>     OK: Peer with 10.10.1.55 AS0 (XMPP) is Established (last state Active at 2014-Jun-23 07:11:10.433553)
>     OK: Peer with 10.10.1.56 AS0 (XMPP) is Established (last state Active at 2014-Jun-23 07:11:13.863633)

* Check localhost on port 8083
>     check_bgp_neighbor
>     UNKNOWN: Could not connect to localhost:8083 (please check)
