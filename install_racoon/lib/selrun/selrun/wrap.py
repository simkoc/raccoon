import threading
import subprocess
import os
import signal
import time
import log

import selenese

# Install logger
s_logger = log.getdebuglogger("selrun")

# Handler Class


class SeleneseRunnerHandler:

    def handle_command(self, i, cmd, tc_fname):
        pass


# Decorator
def threaded(fn):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thr.start()
        return thr
    return wrapper


def _parse_selenese_fname(test_fname):
    out = []

    if selenese.is_suite(test_fname):
        ts = selenese.SeleneseTestSuite(test_fname)

        out = [tc for tc in ts]
    else:
        out = [selenese.SeleneseTestCase(test_fname)]

    return out


def _flatten(ts):
    out = []

    for tc in ts:
        for cmd in tc:
            tcname = tc.tc_fname
            out.append([cmd, tcname])

    return out


# That's our boy
class SeleneseRunner:

    test_fname = None
    commands = None
    conf = {}
    returncode = None
    proc = None
    handler = None

    _state = [-1, None, None]

    def __init__(self, test_fname, conf, cls=None):
        self.test_fname = test_fname
        self.commands = _flatten(_parse_selenese_fname(test_fname))
        self.conf = conf
        if cls:
            self.handler = cls()

    def _prepare_cmdline(self):
        cmdline = ["java"]
        cmdline.append("-jar")
        if "jar" in self.conf:
            cmdline.append(self.conf.jar)
        else:
            cmdline.append("../selenese-runner/selenese-runner.jar")

        if "driver" in self.conf:
            cmdline.append("--driver")
            cmdline.append(self.conf.driver)

        if "firefox" in self.conf:
            cmdline.append("--firefox")
            cmdline.append(self.conf.firefox)

        if "noproxy" in self.conf:
            cmdline.append("--no-proxy")
            cmdline.append(self.conf.noproxy)

        if "proxy" in self.conf:
            cmdline.append("--proxy")
            cmdline.append(self.conf.proxy)

        if "timeout" in self.conf:
            cmdline.append("-t")
            cmdline.append(self.conf.timeout)

        if "baseurl" in self.conf:
            cmdline.append("-b")
            cmdline.append(self.conf.baseurl)

        if "height" in self.conf:
            cmdline.append("--height")
            cmdline.append(self.conf.height)

        if "width" in self.conf:
            cmdline.append("--width")
            cmdline.append(self.conf.width)

        # If additional args are passed, we insert them
        # as last (before the TS/TC selenese file)
        if "selargs" in self.conf:
            for p in self.conf.selargs.split(" "):
                cmdline.append(p)  # insert at the last but one position

        cmdline.append("-i")

        # Last parameter is the testcase/testsuite filename
        cmdline.append("{}".format(self.test_fname))

        cmdline = map(str, cmdline)  # stringify everything

        return cmdline

    @threaded
    def run(self):
        cmdline = self._prepare_cmdline()
        s_logger.info("Command Line {}".format(" ".join(cmdline)))
        self.proc = subprocess.Popen(cmdline, bufsize=0, stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        time.sleep(self.conf.getfloat("wait"))

        # utility function to iterate over all commands
        def _state_gen():
            for i, e in enumerate(self.commands):
                cmd, tcname = e
                yield [i, cmd, tcname]

        # buffer to store the stdout of the subprocess
        stdout = []
        gen = _state_gen()
        with open(self.conf.log, "a") as f:
            """
            Read stdout
            """
            s_logger.info("Start running the show")

            for line in iter(self.proc.stdout.readline, b""):

                # s_logger.info("about to write to stoud")

                stdout.append(line)  # create a copy

                # s_logger.info("about to write to log file")

                f.write(line)

                # s_logger.info("executing command. Please wait for impending doom and destruction.")

                if self.proc.poll() is not None:
                    break

                if ">>> Press ENTER to continue <<<" in line:
                    """
                    Next command
                    """
                    # Let's sleep a bit to flush pending HTTPr requests
                    s_logger.info("Selenese ready for next command. Waiting for {}s...".format(self.conf.wait))
                    time.sleep(self.conf.getfloat("wait"))

                    # Update current state and passing command to the handler
                    self._state = gen.next()
                    if self.handler:
                        self.handler.handle_command(self._state[0], self._state[1], self._state[2])

                    # Next command
                    s_logger.info("Pressing ENTER")
                    self.proc.stdin.write("\n")
                    s_logger.info("Pressed  ENTER")

                # s_logger.info("past if block")

        time.sleep(self.conf.getfloat("wait"))

        self.returncode = self.proc.poll()

        s_logger.info("Process terminated with code {}.".format(self.returncode))

        return self.returncode

    def state(self):  # TODO: Is this function threadsave?
        return self._state

    def shutdown(self):
        if not self.proc:
            s_logger.info("No process to terminate. You should do run() first. Ignoring shutdown().")
            return

        if self.proc.poll() is None:
            s_logger.info("Sending SIGTERM to Selenese Runner. PID={}".format(self.proc.pid))
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
            except Exception as e:
                s_logger.exception(e)
        else:
            s_logger.info("No need to send SIGTERM, process terminated with code {}.".format(self.proc.poll()))


if __name__ == '__main__':
    from sharedconf import Config
    import sys
    conf = Config({
        "noproxy": "*.com,*.net,*.org",
        "timeout": "640000",
        "wait": 2,
        "log": "test",
        "jar": sys.argv[1],
        "selargs": sys.argv[2]
    })

    s_logger.info("Running selrun")
    
    p = SeleneseRunner(sys.argv[3], conf)
    try:
        for cmd, f in p.commands:
            print cmd.command(), cmd.target(), cmd.value(), f
        # thr = p.run()
        # while thr.isAlive():
        #    thr.join(1)
    except Exception:
        print "exception"
        pass
    # p.shutdown()
    # thr.join(4)
