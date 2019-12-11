from postgres import get_connection, store_experiments, store_http_requests, store_sel_commands

class experiments:
    def __init__(self, projname, session, operation, username, ts, success):
        self._projname = projname
        self._session = session
        self._operation = operation
        self._username = username
        self._ts = ts
        self._success = success

class requests:
    def __init__(self, expid, selcmdctr, ts, url, method):
        self._expid = expid
        self._selcmdctr = selcmdctr
        self._ts = ts
        self._url = url
        self._method = method

class commands:
    def __init__(self, expid, tcname, command, target, value):
        self._expid = expid
        self._tcname = tcname
        self._command = command
        self._target = target
        self._value = value

con = get_connection("localhost", "trueschottsman", "woulddothat", "secsac")

experiment = experiments("test_proj", "S1", "login-fail", "testuser", "today", True)

#store_experiments(con, experiment)

request = requests("1", "2", "today", "www.hab-kein-bock.de", "POST")

#store_http_requests(con, request)

command = commands("1", "login-fail", "login", "example", "pwd")

#store_sel_commands(con, command)

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