import threading
import sys
import postgresqlinterface as db_interface
import backFiles as ssh_interface
import log
import time
import StringIO
from Queue import Queue


_RETRY_DELAY = 5
_RETRY_COUNT = 5
_APACHE_UNIQUE_LOG = "/opt/bitnami/apache2/logs/unique_log"


def threaded(fn):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thr.start()
        return thr
    return wrapper


class Httprequestident:
    internalid = -1
    experimentid = -1
    selenesecommandctr = -1
    httprequestid = -1
    req = None

    def __init__(self, internalid, experimentid, selenesecommandctr, httprequestid, req):
        self.internalid = internalid
        self.experimentid = experimentid
        self.selenesecommandctr = selenesecommandctr
        self.httprequestid = httprequestid
        self.req = req


class XdebugNameOracle():

    def __init__(self, ssh_client, path=_APACHE_UNIQUE_LOG, logger=None):
        if logger is not None:
            logger.info("downloading apache file")

        self._dict = dict()
        self._logger = logger
        data = ssh_interface.get_file_as_string(ssh_client, path)

        if logger is not None:
            logger.info("download success - creating oracle")

        for line in StringIO.StringIO(data):
            try:
                split = line.split("\"")
                paqu = split[1]
                id = split[3]
                if logger is not None:
                    logger.debug("unique ID {} -> {}".format(paqu.split(" ")[1], id))

                if paqu.split(" ")[1] in self._dict:
                    self._dict[paqu.split(" ")[1]].append(id)
                else:
                    nl = list()
                    nl.append(id)
                    self._dict[paqu.split(" ")[1]] = nl
            except:
                if logger is not None:
                    logger.info("encountered error whiole processing {}".format(line))
                    logger.error(sys.exc_info()[1])
                else:
                    raise

    def oracle(self, request_url, logger=None):
        if logger is not None:
            logger.debug("oracle forseeth {}".format(request_url))
        if request_url not in self._dict:
            if self._logger is not None:
                self._logger("unknown request url {}".format(request_url))
                raise Exception("unknown request url {}".format(request_url))
        else:
            elem = self._dict[request_url]
            logger.debug("oracle forsaw {}".format(elem))
            return elem


class MosgiRunner:
    internalidcounter = 0
    logger = None
    xdebug_folder = None
    session_folder_path = None
    host = None
    root = None
    pwd = None
    back_up_xdebug_folder = "/tmp/xdebug"
    back_up_sess_folder = "/tmp/sess"
    backup_thread = None
    work_queue = Queue()
    db_host = None
    db_user = None
    db_pwd = None
    db_name = None

    def __init__(self, host, root, pwd, session_folder, xdebug_folder, db_host, db_user, db_pwd, db_name, logger=None):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_name = db_name
        self.xdebug_folder = xdebug_folder
        self.session_folder_path = session_folder
        self.host = host
        self.root = root
        self.pwd = pwd
        if logger:
            self.logger = logger
        else:
            self.logger = log.getdebuglogger("mosgi")
        with ssh_interface.create_ssh_client(self.host, self.root, self.pwd) as client:
            for file in ssh_interface.get_folder_content_files(client, xdebug_folder):
                self.logger.info("residual xdebug file found {}".format(file))
                ssh_interface.delete_file(client, file)
                self.logger.info("residual xdebug file deleted")
        self.logger.info("mosgi initialisation finished successfully")

    def start(self):
        if self.backup_thread:
            self.logger.warning("There is already a backup thread running. Ignoring start().")
            return
        # self.backup_thread = self.download_files()
        self.logger.info("Started download thread")

    def stop(self):
        # if self.backup_thread is None:
        #    self.logger.warning("There is no backup thread running. Ignoring stop().")
        #    return
        self.work_queue.put(Httprequestident(-1, -1, -1, -1, "NONE"))  # the stop request to trigger save shutdown of thread when reached
        self.logger.info("started download thread")
        self.download_files()
        self.logger.info("Stopped download thread")

    def download_files(self):
        try:
            with ssh_interface.create_ssh_client(self.host, self.root, self.pwd) as client:
                self.logger.info("Download Thread connected to host")
                oracle = XdebugNameOracle(client, logger=self.logger)

                with db_interface.get_postgres_connection(self.db_host, self.db_user, self.db_pwd, self.db_name) as dbconnection:
                    self.logger.info("Download Thread connected to the database")

                    for referenceStruct in iter(self.work_queue.get, None):
                        try:
                            if referenceStruct.httprequestid == -1:
                                return

                            self.logger.info("Downloading files for {}.{}.{} on request {}".format(referenceStruct.experimentid,
                                                                                                   referenceStruct.selenesecommandctr,
                                                                                                   referenceStruct.httprequestid,
                                                                                                   referenceStruct.req))
                            for session in ssh_interface.get_folder_content_files(client,
                                                                                  "{}{}/".format(self.back_up_sess_folder, referenceStruct.internalid)):
                                self.logger.info("Saving session {}".format(session))
                                session_content = ssh_interface.get_file_as_string(client, session)
                                db_interface.save_session(dbconnection,
                                                          referenceStruct.experimentid,
                                                          referenceStruct.selenesecommandctr,
                                                          referenceStruct.httprequestid,
                                                          session,
                                                          session_content)

                            folder = "{}{}/".format(self.back_up_xdebug_folder, referenceStruct.internalid)
                            files = ssh_interface.get_folder_content_files(client, folder)
                            # files = [file for file in files if file[-2:] == "xt"]
                            # to counter those weird subfiles I cannot fathom
                            # https://serverfault.com/questions/957803/multiple-xdebug-dumps-for-single-request
                            self.logger.debug("found files {}".format(files))
                            files = [file for file in files if file[-2:] == "xt" and file.count(".") == 3]
                            if len(files) != 1:
                                self.logger.info("there should actually only be exactly one file here for retrieval\n {}".format(files))
                            self.logger.debug("found files {}".format(files))
                            # if len(files) == 1:
                            #    f_path = files[0]
                            if len(files) >= 1:
                                ids = oracle.oracle(referenceStruct.req, logger=self.logger)
                                f_path = None
                                for f in files:
                                    for id in ids:
                                        if id in f:
                                            f_path = f
                                if f_path is None:
                                    self.logger("No proper Xdebug file found in {} among {} for {}".format(folder, files, referenceStruct.req))
                            self.logger.info("Saving xdebug file {}".format(f_path))
                            db_interface.save_xdebug(dbconnection,
                                                     referenceStruct.experimentid,
                                                     referenceStruct.selenesecommandctr,
                                                     referenceStruct.httprequestid,
                                                     f_path.split("/")[-1],
                                                     ssh_interface.get_file_as_string(client,
                                                                                      f_path,
                                                                                      usezlib=True))

                            ssh_interface.delete_folder(client, "{}{}/".format(self.back_up_xdebug_folder, referenceStruct.internalid))
                            ssh_interface.delete_folder(client, "{}{}/".format(self.back_up_sess_folder, referenceStruct.internalid))
                            self.logger.info("Saving process completed")
                        except:
                            self.logger.exception("Encountered error {}".format(str(sys.exc_info()[0])))  # TODO: printing does not work (no msg only type)
        except:
            self.logger.fatal("Download has unexpectedly ended. Error {}".format(str(sys.exc_info()[0])))
            raise

        self.logger.info("Disconnected and stopped download thread")

    def backup_files(self, experimentid, selenesecommandctr, httprequestid, req):
        if httprequestid < 0 or experimentid < 0 or selenesecommandctr < 0:
            raise Exception("ID must be non negative")

        with ssh_interface.create_ssh_client(self.host, self.root, self.pwd) as client:
            _id = self.internalidcounter
            self.logger.info("doing a 2 sec sleep for the webapp to finish xdebug dumping")
            time.sleep(2)
            self.logger.info("Back up sessions")
            ssh_interface.backup_all_files_in_folder(client,
                                                     self.session_folder_path,
                                                     "{}{}/".format(self.back_up_sess_folder, _id),
                                                     logger=self.logger)

            self.logger.info("Back up xdebug file at {}".format(self.xdebug_folder))
            files = ssh_interface.get_folder_content_files(client, self.xdebug_folder)
            xfiles = [file for file in files if file[-2:] == "xt"]
            self.logger.debug("ecountered xdebug files {}".format(xfiles))

            # sometimes the xdebug is not successfully moved and I suspect it is due
            # to a still open lock on the file by the server, consequently just wait
            # and retry in hopes of success
            for xdebug_file in xfiles:
                self.logger.debug("trying to move encountered xdebug {}".format(xdebug_file))
                for counter in range(_RETRY_COUNT):
                    ssh_interface.backup_file(client,
                                              xdebug_file,
                                              "{}{}/".format(self.back_up_xdebug_folder, _id),
                                              logger=self.logger)

                    bckp_file = "{}{}/{}".format(self.back_up_xdebug_folder, _id, xdebug_file.split("/")[-1])

                    if ssh_interface.check_if_file_exists_fp(client, bckp_file):
                        self.logger.info("xdebug {} successfully moved".format(bckp_file))
                        ssh_interface.delete_file(client, xdebug_file)
                        self.logger.info("old xdebug file successfully deleted")
                        break
                    else:
                        self.logger.info("file {} does not exist".format(bckp_file))
                        self.logger.info("xdebug moving failed, trying again after {} sec...".format(_RETRY_DELAY))
                        time.sleep(_RETRY_DELAY)
                        continue

            self.work_queue.put(Httprequestident(_id, experimentid, selenesecommandctr, httprequestid, req))
            self.internalidcounter = self.internalidcounter + 1
            self.logger.info("Finished back up process")
