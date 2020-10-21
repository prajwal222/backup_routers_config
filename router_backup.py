#   Base class for router backup
from netmiko import ConnectHandler
from copy import deepcopy
import yaml
import re
from paramiko.ssh_exception import SSHException
from netmiko.ssh_exception import AuthenticationException
import logging
from logging.handlers import RotatingFileHandler
import sys
from notify_email import failed_notify


def logger_setup(filename, formatting, name="__main__"):
    """
            Provides logger setup
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(formatting)
    file_handler = RotatingFileHandler(filename, maxBytes=2000, backupCount=10)
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
        self.err_str = ''

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
                    self.connected_devices.remove(host)
                except Exception as e:
                    backup_logger.exception(f"Exception '{e}' occurred. disconnect is unsuccessful for device {host}. "
                                            f"Skipping back up")

    @staticmethod
    def _read_testbed_yaml(path):
        with open(path) as f:
            yaml_content = yaml.safe_load(f.read())
        return yaml_content

    def notify(self, text):
        notification = f"{self.current_device} \n {text}"
        failed_notify(notification)

    def login(self, device_name):
        """
        Logs in to the network device
        :return: True or False
        """
        try:
            device = next((item for item in self.host_dict if item.get('hostname') == device_name))
        except StopIteration:
            self.err_str = f"Exception occurred. Please check hostname \"{device_name}\". Skipping back up"
            backup_logger.exception(self.err_str)
            return
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
            self.err_str = f"Exception '{e}' occurred. " \
                           f"SSH is unsuccessful for device {hostname}. Skipping back up"
            backup_logger.exception(self.err_str)
            # sys.exit()

        return logged_in
        # self.session = ConnectHandler(**device)

    def logout(self):
        """
        logs out of device
        """
        self.session.disconnect()

    def get_command(self):
        conf_dict = {'juniper_junos': 'show configuration | display set | no-more',
                     'alcatel_sros': 'admin display-config'}
        get_conf_command = conf_dict.get(self.session.device_type)
        return get_conf_command or "show running-config"

    def run(self, command):
        """
        Runs command and returns output as list
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
        """
                Get the hostname configured on device
        """
        prompt = self.session.find_prompt()
        backup_logger.info(f"Getting hostname configured for {self.current_device}:")
        hostname_configured = re.search(r'.*?[:@]?([\w\-_]*)[#>]', prompt, re.MULTILINE).group(1)
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
                backup_logger.info(f'Recent Backup for {self.hostname} at {date}')
            return True
        except FileNotFoundError:
            self.err_str = f'Backup directory not found. Please create the backup directory "{directory}". ' \
                      f'Exiting!!'
            backup_logger.error(self.err_str)
            self.__exit__(None, None, None)
        except PermissionError:
            self.err_str = f'User does not have permission to write on the directory "{directory}". ' \
                           f'Exiting!!'
            backup_logger.error(self.err_str)
            self.__exit__(None, None, None)


# main
if __name__ == "__main__":
    pass
