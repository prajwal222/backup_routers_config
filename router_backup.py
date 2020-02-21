from netmiko import ConnectHandler
from copy import deepcopy
import yaml
import re
from paramiko.ssh_exception import SSHException
from netmiko.ssh_exception import AuthenticationException
import logging
import sys


def logger_setup(filename, formatting, name="__main__"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(formatting)
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


backup_logger = logger_setup('backup.log', '%(asctime)s: %(name)s: %(levelname)s: %(message)s')
stream_handler = logging.StreamHandler(sys.stdout)
stream_formatting = '%(asctime)s: %(levelname)s: %(message)s'
stream_formatter = logging.Formatter(stream_formatting)
stream_handler.setFormatter(stream_formatter)
backup_logger.addHandler(stream_handler)


class RtrBackup:
    def __init__(self, testbed_yaml):
        """
        class initialization
        """
        backup_logger.info(f'Initializing testbed file {testbed_yaml}')
        self.testbed_yaml = testbed_yaml
        self.host_dict = []
        self.hostname = ''
        self.current_device = ''
        self.connected_devices = []
        self.session = None

    def __enter__(self):
        parsed_yaml = self._read_testbed_yaml(self.testbed_yaml)
        parsed_yaml = deepcopy(parsed_yaml)
        login_credentials = parsed_yaml["all"]["vars"]
        for site_dict in parsed_yaml["all"]["sites"]:
            for host in site_dict["hosts"]:
                host_dict = {}
                host_dict.update(login_credentials)
                host_dict.update(host)
                self.host_dict.append(host_dict)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for host in self.connected_devices:
            alive_session = ConnectHandler(**host)
            if alive_session.is_alive():
                backup_logger.info(f"disconnecting from {host['host']}")
                try:
                    alive_session.disconnect()
                except Exception as e:
                    backup_logger.exception(f"Exception '{e}' occurred. disconnect is unsuccessful for device {host}. "
                                            f"Skipping back up")

    @staticmethod
    def _read_testbed_yaml(path):
        with open(path) as f:
            yaml_content = yaml.safe_load(f.read())
        return yaml_content

    def login(self, device_name):
        """
        Logs in to the ios device; change device_type to 'cisco_nxos' if device is nexus. Refer netmiko git link above
        :return: True or False
        """
        device = next((item for item in self.host_dict if item.get('hostname') == device_name))
        backup_logger.info(f"Logging into {device['host']}")
        hostname = device.pop("hostname")
        logged_in = False
        try:
            self.session = ConnectHandler(**device)
            if 'secret' in device:
                self.session.enable()
            self.current_device = device_name
            self.connected_devices.append(device)
            logged_in = True
        except (AuthenticationException, SSHException) as e:
            backup_logger.exception(f"Exception '{e}' occurred. "
                                    f"SSH is unsuccessful for device {hostname}. Skipping back up")
            # sys.exit()
        return logged_in
        # self.session = ConnectHandler(**device)

    def logout(self):
        """
        logs out of device
        """
        self.session.disconnect()

    def run(self, command):
        """
        Runs show runn command and returns output as list
        """
        try:
            output = self.session.send_command(command)
            output = output.split('\n')
            return output
        except Exception as e:
            backup_logger.exception(f'Exception {e} occurred while running command. '
                                    f'Trying again with send_command_expect')
            try:
                output = self.session.send_command(command, expect_string='#')
                output = output.split('\n')
                return output
            except Exception as e:
                backup_logger.exception(f'Exception {e} occurred again while running command with expect.')
            return None

    def get_hostname(self):
        prompt = self.session.find_prompt()
        backup_logger.info(f"Getting hostname configured for {self.current_device}:")
        hostname_configured = re.search(r'.*?:?([\w\-_]*)#', prompt, re.MULTILINE).group(1)
        self.hostname = hostname_configured

    def writer(self, result, date, directory):
        """
        Write the show run outputs to a text file
        """
        self.get_hostname()
        file_name = '{}/{}-{}.txt'.format(directory, self.hostname, date)
        backup_logger.info(f'Writing running config to filename {file_name}')
        try:
            with open(
                    file_name,
                    'w') as the_file:
                for line in result:
                    the_file.write(line + '\n')
            return True
        except FileNotFoundError:
            backup_logger.error(f'Backup directory not found. Please create the backup directory "{directory}". '
                                f'Exiting!!')
            sys.exit()


# main
if __name__ == "__main__":
    pass
