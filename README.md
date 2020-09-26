# Backup Router Config
Netmiko project to backup router running config

Back up running config with a yaml file with the list of device and login info

usage: backup.py [-h] [-t] [-l] [-H  [...]] [-s  [...]]

Save the current running config of the device in a file. Use a YAML file for host information

optional arguments:
  -h, --help            show this help message and exit
  -t , --topo           Location of the topology YAML file
  -l , --loc            Location of the backup folder
  -H  [ ...], --host  [ ...]
                        Hostnames, if backing up a particular list of hosts
  -s  [ ...], --site  [ ...]
                        Site names, if backing up a particular list of sites
                        
Sample Topology file:

all:
  vars:
    username: admin
    password: cisco.123
  sites:
    - name: site1
      hosts:
        - hostname: D9
          host: 10.225.252.232
          device_type: cisco_xr
          username: nso
          password: Testify@123!
        - hostname: D1
          host: 10.225.252.235
          device_type: cisco_nxos
        - hostname: D7
          host: 10.225.252.228
          device_type: cisco_xe
    - name: site2
      hosts:
        - hostname: D9
          host: 10.225.254.232
          device_type: cisco_xr
          username: nso
          password: Testify@123!
        - hostname: D1
          host: 10.225.254.235
          device_type: cisco_nxos
        - hostname: D7
          host: 10.225.254.228
          device_type: cisco_xe
          secret: jnpr16