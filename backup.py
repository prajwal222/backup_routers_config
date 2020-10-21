from router_backup import RtrBackup
from router_backup import backup_logger
import yaml
import time
from operator import itemgetter
import sys
import argparse

time_stamp = time.strftime("%Y-%m-%d")

parser = argparse.ArgumentParser(description='Save the current running config of the device in a file.\n'
                                             'Use a YAML file for host information')
parser.add_argument("-t", "--topo", type=str, metavar="", help='Location of the topology YAML file', required=True)
parser.add_argument("-l", "--loc", type=str, metavar="", help='Location of the backup folder', required=True)
parser.add_argument("-H", "--host", type=str, nargs='+', metavar="", help='Hostnames, if backing up a '
                                                                          'particular list of hosts')
parser.add_argument("-s", "--site", type=str, nargs='+', metavar="", help='Site names, if backing up a '
                                                                          'particular list of sites')
args = parser.parse_args()
topo_file = args.topo
backup_path = args.loc
backup_host = args.host
backup_site = args.site

with RtrBackup(testbed_yaml=topo_file) as backup:
    backup_logger.info(
        f'\n\n**************************Script execution started at {time_stamp}**************************')
    testbed = yaml.safe_load(open(topo_file))
    host_list = []
    if backup_site:
        try:
            sites = [item for item in testbed['all']['sites'] if item.get('name') in backup_site]
            if not sites:
                raise StopIteration
            for site in sites:
                host_list.extend(site['hosts'])
        except StopIteration as e:
            log_str = f"Exception occurred. Please check site name \"{backup_site}\". Skipping back up {e}"
            backup_logger.exception(log_str)
            backup.notify(log_str)
            sys.exit()
    else:
        host_list = testbed['all']['sites'][0]['hosts'] if not backup_host else None

    if host_list:
        device_list = list(map(itemgetter('hostname'), host_list))
    else:
        device_list = backup_host
    for dev in device_list:
        connected = backup.login(dev)
        if connected:
            # show_platform = backup.run('show platform')
            config_command = backup.get_command()
            show_run = backup.run(config_command)
            calender = time.strftime("%Y-%m-%d")  # Year Month Date
            if show_run:
                backup.writer(show_run, calender, backup_path)
        if backup.err_str:
            backup.notify(backup.err_str)

time_stamp = time.strftime("%Y-%m-%d")
backup_logger.info(f'**************************Script execution completed at {time_stamp}**************************'
                   f'\n\n')
