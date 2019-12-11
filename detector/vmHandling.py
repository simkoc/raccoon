import paramiko as ssh
import time
import stat
import posixpath
import sys
from subprocess import call


class RunningVirtualMachine:
    def __init__(self, vm_name, vm_state, vm_ip, vm_root, vm_pwd,
                 clearCaches=[], startup_delay=10, logger=None):
        try:
            logger.debug("setting up context handler for vm {} at snapshot {}".format(vm_name,
                                                                                      vm_state))
            self._running = False
            self._name = vm_name
            self._state = vm_state
            self._ip = vm_ip
            self._root = vm_root
            self._pwd = vm_pwd
            self.start()
            time.sleep(startup_delay)
            self.clear_caches(clearCaches, logger=logger)
        except:
            logger.error("Encountered error {}".format(sys.exc_info()[0]))
            if self._running:
                self.stop(logger=logger)
            raise
            
    def start(self, logger=None):
        ret = call(["vboxmanage",
                    "snapshot", self._name,
                    "restore", self._state])
        if logger is not None:
            if ret == 0:
                logger.debug("successfully restored snapshot {} of".format(self._state, self._name))
            else:
                logger.error("unable to restore snapshot {} of ".format(self._state, self._name))
                
        ret = call(["vboxmanage",
                    "startvm", self._name, "--type", "headless"])
        if logger is not None:
            if ret == 0:
                logger.debug("successfully started {}".format(self._name))
            else:
                logger.error("unable to start {}".format(self._name))
        if ret == 0:
            self._running = True

        if logger is not None:
            logger.info("VM started waiting for network connection cron job 70s")
        time.sleep(70)

    def stop(self, logger=None):
        ret = call(["vboxmanage",
                    "controlvm", self._name, "poweroff"])
        if logger is not None:
            if ret == 0:
                logger.debug("successfully stopped {}".format(self._name))
            else:
                logger.error("unable to stopped {}".format(self._name))
        if ret == 0:
            self._running = False

    def run_remote_shell_command(self, ssh_client, command_string):
        stdin, stdout, stderr = ssh_client.exec_command(command_string)
        return stdin, stdout, stderr

    def clear_caches(self, caches, logger=None):
        logger.info("clearing caches {} on {}@{}".format(caches, self._root, self._ip))
        client = ssh.SSHClient()
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        try:
            client.connect(self._ip, username=self._root, password=self._pwd,
                           look_for_keys=False, allow_agent=False, timeout=5)
            for folder in caches:
                logger.info("deleting cache content {}/*".format(folder))
                self.run_remote_shell_command(client, "sudo rm -f {}/*".format(folder))
            # with client.open_sftp() as sftp:
                # for folder in caches:
                #     for f in sftp.listdir_attr(folder):
                #         if not stat.S_ISDIR(f.st_mode):
                #             rpath = posixpath.join(folder, f.filename)
                #             logger.info("delete cache content {}".format(rpath))
                #             sftp.remove(rpath)
        finally:
            client.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.stop()
        return False
