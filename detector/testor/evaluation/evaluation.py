from xdebug_fingerprinting import xdebug_fingerprints_equalp, xdebug_fingerprint_has_query
import zlib
import StringIO
import sys
import paramiko as ssh
from stat import S_ISREG
from os.path import expanduser


_TIMEOUT = 5
_ASSOC_LOG_PATH = "/opt/bitnami/apache2/logs/assoc_log"
# TODO: do not like this hard coding - should be a parameter or global config file
_APACHE_LOG_1_PATH = expanduser("~") + "/.racoon/data/data_gathering/logs/apache_log_1"
_APACHE_LOG_2_PATH = expanduser("~") + "/.racoon/data/data_gathering/logs/apache_log_2"


class LogBasedParameterOracle():

    def __init__(self, log1, log2, logger=None):
        #if logger is not None:
        #    logger.info("creating deep model parameter oracle for {},{},{}".format(projname, session, user))
        self._oracle = {}

        results1 = self.cut_logs(log1)
        results2 = self.cut_logs(log2)

        log1 = []
        log2 = []

        #Seperate names and values and put them in arrays
        for line in results1:
            transferList = []
            for string in line:
                transfer = string.split(",")
                for attributes in transfer:
                    if len(attributes.split("=")) == 2:
                        transferList.append(attributes.split("=")[0])
                        transferList.append(attributes.split("=")[1])
            log1.append(transferList)

        for line in results2:
            transferList = []
            for string in line:
                transfer = string.split(",")
                for attributes in transfer:
                    if len(attributes.split("=")) == 2:
                        transferList.append(attributes.split("=")[0])
                        transferList.append(attributes.split("=")[1])
            log2.append(transferList)

        #compare arrays and create list of semtypes
        semtypes = []

        #counts index of first log
        for i in range(len(log1)):
            #counts index of second log
            for x in range(len(log2)):
                #compares number of variables in log-lines
                if len(log1[i]) == len(log2[x]):
                    #goes through variable names...
                    count_equal_names = 0
                    for y in range(0, len(log1[i]), 2):
                        #and compares them
                        if log1[i][y] == log2[x][y]:
                            count_equal_names+=1
                    #if all variable names are equal --> actual determination of semtypes
                    if count_equal_names == (y+2)/2:
                        transferList = []
                        #if values are the same as well, semtype is constant
                        if log1[i][y+1] == log2[x][y+1]:
                            transferList.append(log1[i][y])
                            transferList.append("constant")
                        #otherwise semtype is dynamic
                        else:
                            transferList.append(log1[i][y])
                            transferList.append("dynamic")
                        semtypes.append(transferList)
                        log2[x] = []
                        break

        #if there're multiple semtypes with the same name the weakest type is used as general type
        results = []
        for semtype in semtypes:
            if semtype not in results:
                results.append(semtype)

        for element in results:
            for element2 in results:
                if element[0] == element2[0] and results.count(element > 1):
                    if element[1] == "constant":
                        results.remove(element)
                    elif element2[1] == "constant":
                        results.remove(element2)

        for element in results:
            self._oracle[element[0]] = element[1]

    def cut_logs(self, log):
        logfile = open(log,"r")
        log = logfile.readlines()
        logfile.close

        results = []
        lines = []
        for line in log:
            #Cutting loglines again
            if line.find(".php", 0, len(line)-1) == -1 and line.find(" / ", 0, len(line)-1) == -1:
                line = ""
            if line[0:3] == "GET":
                line = line[4:len(line)-1]
                line = line[0:len(line)-9]
            elif line[0:4] == "POST":
                line = line[5:len(line)-1]
                line = line[0:len(line)-9]
            if line != "" and line != "/ ":
                lines.append(line)

        for line in lines:
            #Getting query seperator
            query_separator = "&"
            if line.count(";") >= line.count("&"):
                query_separator = ";"
            #Splitting queries
            queryStartIndex = line.find(".php")
            queryStartIndex+=5
            line = line[queryStartIndex:len(line)]
            if line != "":
                queries = line.split(query_separator)
                results.append(queries)
        
        return results

    def constant_oracle_func(self):
        return lambda name: self._oracle[name] == 'constant' if name in self._oracle else False


class XdebugPaQuOracle():

    def __init__(self, ssh_client, path=_ASSOC_LOG_PATH, logger=None):
        if logger is not None:
            logger.info("downloading apache file and creating PaQu oracle")
        self._dict = {}
        self._logger = logger
        data, garbage = get_file_as_string(ssh_client, path)
        if logger is not None:
            logger.debug("downloaded the apache log file and about to parse it")
        for line in StringIO.StringIO(data):
            try:
                split = line.split("\"")
                paqu = split[1]
                id = split[3]
                if logger is not None:
                    logger.debug("unique id {} -> {}".format(id, paqu.split(" ")[1]))

                self._dict[id] = paqu.split(" ")[1]
            except:
                logger.info("encountered error while processing {}".format(line))
                logger.error(sys.exc_info()[1])

    def oracle(self, id):
        if id not in self._dict:
            if self._logger is not None:
                self._logger.error("oracle request for unknown id {}".format(id))
                self._logger.info(self._dict)
                # return "unknown"
                raise Exception("oracle request for unknown id {}".format(id))
        return self._dict[id]


def create_ssh_client(host, user, password):
    client = ssh.SSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    client.connect(host, username=user, password=password,
                   look_for_keys=False, allow_agent=False,
                   timeout=_TIMEOUT)
    return client


def get_folder_content_files(ssh_client, folder_path):
    assert folder_path[-1] is "/", "path '%s' needs to be absolute" % (folder_path)
    with ssh_client.open_sftp() as sftp:
        return ["{}{}".format(folder_path, content.filename) for content
                in sftp.listdir_attr(folder_path)
                if S_ISREG(content.st_mode)]


def get_file_as_string(ssh_client, file_path, usezlib=False, logger=None):
    with ssh_client.open_sftp() as sftp:
        if logger is not None:
            logger.debug("created sftp connection")
        remote_file = sftp.open(file_path)
        if logger is not None:
            logger.debug("opened remote file")
        data = remote_file.read()
        if logger is not None:
            logger.debug("read in file content")

        if usezlib:
            data = zlib.compress(data, 9)

        return data, file_path.split("/")[-1]


def run_remote_shell_command(ssh_client, command_string):
        stdin, stdout, stderr = ssh_client.exec_command(command_string)
        return stdin, stdout, stderr


def remove_remote_file(ssh_client, file_path):
    run_remote_shell_command(ssh_client, "sudo rm -f {}".format(file_path))


def get_available_xdebugs(ssh_client, path):
    folder_content = get_folder_content_files(ssh_client, path)
    return [fp for fp in folder_content if fp.split(".")[-1] == "xt"]


def get_xdebug_stream(ssh_client, path, oracle):
    file_content, name = get_file_as_string(ssh_client, path)
    stream = StringIO.StringIO(file_content)
    zip = zlib.compress(file_content)
    return stream, zip, oracle.oracle(name.split(".")[2])


def get_xdebugs(root, target, pwd, path, logger=None):
    zips = []
    with create_ssh_client(target, root, pwd) as ssh_client:
        oracle = XdebugPaQuOracle(ssh_client, logger=logger)
        for xdebug_path in get_available_xdebugs(ssh_client, path):
            logger.debug("downloading xdebug file {}".format(xdebug_path))
            xstream, zip, paqu = get_xdebug_stream(ssh_client,
                                                   xdebug_path,
                                                   oracle)
            remove_remote_file(ssh_client, xdebug_path)
            zips.append((zip, paqu, xstream))
    return zips


def count_equalp_fingerprints(fingerprint, refFingerprints,
                              projname, session, user, logger=None):
    count = 0
    dmoracle = LogBasedParameterOracle(_APACHE_LOG_1_PATH, _APACHE_LOG_2_PATH, logger=logger)
    for refPrint in refFingerprints:
        fittage, checkResult = xdebug_fingerprints_equalp(refPrint,
                                                          fingerprint,
                                                          constant_oracle=dmoracle.constant_oracle_func(),
                                                          logger=logger)
        if fittage:
            if logger is not None:
                logger.info("HIT!".format(
                    fittage))
                count = count + 1
        else:
            if logger is not None:
                logger.info("MISSMATCH!".format(
                    fittage))
    return count


def count_equalp_fingerprints_relaxed(refFingerprint, refQuery, fingerprints,
                                      projname, session, user, logger=None):
    count = 0
    dmoracle = LogBasedParameterOracle(_APACHE_LOG_1_PATH, _APACHE_LOG_2_PATH, logger=logger)
    for fprint in fingerprints:
        fittage, checkResult = xdebug_fingerprint_has_query(refFingerprint._url,
                                                            refQuery,
                                                            fprint,
                                                            constant_oracle=dmoracle.constant_oracle_func(),
                                                            logger=logger)
        if fittage:
            if logger is not None:
                logger.info("HIT!".format(
                    fittage))
                count = count + 1
        else:
            if logger is not None:
                logger.info("MISSMATCH!".format(
                    fittage))
    return count
