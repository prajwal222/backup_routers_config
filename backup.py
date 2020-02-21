from router_backup import RtrBackup
from router_backup import logger_setup
import yaml
import time
from operator import itemgetter

logger = logger_setup('sample_backup.log', '%(asctime)s: %(name)s: %(levelname)s: %(message)s', name="backuplog")
with RtrBackup(testbed_yaml="testbed/sample_topo.yaml") as backup:
    testbed = yaml.safe_load(open("testbed/sample_topo.yaml"))
    host_list = testbed['all']['sites'][0]['hosts']
    device_list = list(map(itemgetter('hostname'), host_list))
    # device_list = ['N9k-Mgmt-SE-2']
    for dev in device_list:
        connected = backup.login(dev)
        if connected:
            # show_platform = backup.run('show platform')
            show_run = backup.run('show run')
            calender = time.strftime("%Y-%m-%d")  # Year Month Date
            if show_run:
                backup.writer(show_run, calender, "backups")
            logger.info(f'Recent Backup for {dev} at {calender}')
