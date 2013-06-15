import logging
from rpi.constants import logfile as logfile

def newlogger(logginglevel=None):
    # set logging facility
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(logfile)
    hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(hdlr)

    if logginglevel == None:
        logger.setLevel(logging.ERROR)
    else:
        try:
            logger.setLevel({
              'CRITICAL': logging.CRITICAL,
              'ERROR'   : logging.ERROR,
              'WARNING' : logging.WARNING,
              'INFO'    : logging.INFO,
              'DEBUG'   : logging.DEBUG,
            } [logginglevel])
        except:
            logger.setLevel(logging.ERROR)

    return logger
