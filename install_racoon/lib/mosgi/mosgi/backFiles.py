from stat import S_ISREG
import paramiko as ssh
import zlib
import time

TIMEOUT = 5


def run_remote_shell_command(ssh_client, command_string):
    stdin, stdout, stderr = ssh_client.exec_command(command_string)
    return stdin, stdout, stderr


def get_folder_content_files(ssh_client, folder_path):
    assert folder_path[-1] is "/", "path '%s' needs to be absolute" % (folder_path)
    with ssh_client.open_sftp() as sftp:
        return ["{}{}".format(folder_path, content.filename) for content
                in sftp.listdir_attr(folder_path)
                if S_ISREG(content.st_mode)]


def check_if_file_exists(ssh_client, folder_path, file_name):
    assert folder_path[-1] is "/", "path '%s' needs to be absolute" % (folder_path)
    return check_if_file_exists_fp(ssh_client, "{}{}".format(folder_path, file_name))


def check_if_file_exists_fp(ssh_client, file_path):
    with ssh_client.open_sftp() as sftp:
        try:
            sftp.stat(file_path)
            return True
        except IOError:
            return False


def create_ssh_client(host, user, password):
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    client.connect(host, username=user, password=password, look_for_keys=False, allow_agent=False, timeout=TIMEOUT)
    return client


def backup_all_files_in_folder(ssh_client, source_folder, target_folder, logger=None):
    assert(source_folder[-1] == "/")
    assert(target_folder[-1] == "/")
    if logger is not None:
        logger.debug("bckp sessions {}".format(get_folder_content_files(ssh_client, source_folder)))
    run_remote_shell_command(ssh_client, "sudo mkdir {}".format(target_folder))
    for source_file in get_folder_content_files(ssh_client, source_folder):
        if logger is not None:
            logger.debug("bckp {} to {}".format(source_file, target_folder))
        run_remote_shell_command(ssh_client, "sudo cp {} {}".format(source_file,
                                                                    target_folder))
    cmd = "sudo chmod 777 {}*".format(target_folder)
    if logger is not None:
        logger.debug("running {}".format(cmd))
    time.sleep(1)
    run_remote_shell_command(ssh_client, cmd)


def backup_file(ssh_client, file_path, target_folder, logger=None):
    assert(target_folder[-1] == "/")
    run_remote_shell_command(ssh_client, "sudo mkdir {}".format(target_folder))
    run_remote_shell_command(ssh_client, "sudo cp {} {}".format(file_path, target_folder))
    # print("running sudo chmod 777 {}/*".format(target_folder))
    if logger is not None:
        logger.debug("running sudo chmod 777 {}*".format(target_folder))
    run_remote_shell_command(ssh_client, "sudo chmod 777 {}*".format(target_folder))


def delete_folder(ssh_client, target_folder):
    assert(target_folder[-1] == "/")
    run_remote_shell_command(ssh_client, "sudo rm -rf {}".format(target_folder))


def delete_file(ssh_client, target_file):
    run_remote_shell_command(ssh_client, "sudo rm -f {}".format(target_file))


def get_file_as_string(ssh_client, file_path, usezlib=False):
    with ssh_client.open_sftp() as sftp:
        remote_file = sftp.open(file_path)
        data = remote_file.read()

        if usezlib:
            data = zlib.compress(data, 9)

        return data
