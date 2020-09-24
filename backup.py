from router_backup import RtrBackup
from router_backup import logger_setup
import yaml
import time
from operator import itemgetter
import sys

logger = logger_setup('router_backup.log', '%(asctime)s: %(name)s: %(levelname)s: %(message)s', name="backuplog")
topo_file = sys.argv[1]
backup_path = sys.argv[2]

with RtrBackup(testbed_yaml=topo_file) as backup:
    testbed = yaml.safe_load(open(topo_file))
    host_list = testbed['all']['sites'][0]['hosts']
    device_list = list(map(itemgetter('hostname'), host_list))
    # device_list = ['N9k-Mgmt-SE-2']
    for dev in device_list:
        connected = backup.login(dev)
        if connected:
            # show_platform = backup.run('show platform')
            config_command = backup.get_command()
            show_run = backup.run(config_command)
            calender = time.strftime("%Y-%m-%d")  # Year Month Date
            if show_run:
                backup.writer(show_run, calender, backup_path)
            logger.info(f'Recent Backup for {dev} at {calender}')
