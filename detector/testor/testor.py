import xdebugparser as Xdebug
from distributedSelenese.hq import HQ_sub, HQ_sub_seq
from evaluation.evaluation import count_equalp_fingerprints, get_xdebugs, count_equalp_fingerprints_relaxed
from evaluation.xdebug_fingerprinting import XdebugFingerprint, PaQu
import time
import zlib

STRICT_CHECK = "strict"
RELAXED_CHECK = "relaxed"
_ERROR_XDEBUG_DUMP = "./bad_xdebug.xt"


def run_simple_interleaving(tc, target, firebases, root, pwd,
                            xpath, refXdebug, refpaqu, refQuery,
                            projname, session, user, logger,
                            db_host, db_user, db_pwd, db_name, expid,
                            hit_function=STRICT_CHECK):
    """
    assumptions:
    1. vm is already running
    2. vm is set up with interceptor
    3. interceptor is already configured
    4. firebases are already started
    """
    start_time_testing = time.time()
    successfull_runs = HQ_sub(tc, target, firebases, logger=logger)
    end_time_testing = time.time()
    xdebugtriples = get_xdebugs(root, target, pwd,
                                xpath, logger=logger)
    refFingerprints = list()
    for triple in xdebugtriples:
        try:
            x = Xdebug.XdebugTrace(triple[2])
        except IndexError:
            logger.error("Encountered an XDEBUG that is broken dumped at {}".format(
                _ERROR_XDEBUG_DUMP))
            with open(_ERROR_XDEBUG_DUMP, 'w') as f:
                f.write(zlib.decompress(triple[0]), file=f)
            raise
        fingerprint = XdebugFingerprint(x, PaQu(triple[1], logger=logger))
        refFingerprints.append(fingerprint)

    logger.info("extracted {} xdebugs".format(len(refFingerprints)))

    for ref in refFingerprints:
        logger.debug(ref)

    fingerprint = XdebugFingerprint(refXdebug, PaQu(refpaqu, logger=logger))

    start_time_eval = time.time()
    if hit_function == STRICT_CHECK:
        matches = count_equalp_fingerprints(fingerprint, refFingerprints,
                                            projname, session, user, db_host, 
                                            db_user, db_pwd, db_name, expid,
                                            logger=logger)
    elif hit_function == RELAXED_CHECK:
        matches = count_equalp_fingerprints_relaxed(fingerprint, refQuery,
                                                    refFingerprints,
                                                    projname, session, user, db_host, 
                                                    db_user, db_pwd, db_name, expid,
                                                    logger=logger)
    end_time_eval = time.time()

    return matches, xdebugtriples, successfull_runs, [start_time_testing,
                                                      end_time_testing,
                                                      start_time_eval,
                                                      end_time_eval]


def run_litmus_test(tc, target, firebases, root, pwd,
                    xpath, logger, sequentialp=True):
    """
    assumptions:
    1. vm is already running
    2. firebases are started
    3. interceptor is configured empty
    """
    if sequentialp is False:
        ret = HQ_sub(tc, target, firebases,
                     logger=logger)
    else:
        ret = HQ_sub_seq(tc, target, firebases,
                         logger=logger)
    xdebugs = get_xdebugs(root, target, pwd,
                          xpath, logger=logger)
    return xdebugs, ret
