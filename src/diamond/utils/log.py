# coding=utf-8
import configparser
import logging
import logging.config
import sys
import os


class DebugFormatter(logging.Formatter):

    def __init__(self, fmt=None):
        if fmt is None:
            fmt = ('%(created)s\t' +
                   '[%(processName)s:%(process)d:%(levelname)s]\t' +
                   '%(message)s')
        self.fmt_default = fmt
        self.fmt_prefix = fmt.replace('%(message)s', '')
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        self._fmt = self.fmt_default

        if record.levelno in [logging.ERROR, logging.CRITICAL]:
            self._fmt = ''
            self._fmt += self.fmt_prefix
            self._fmt += '%(message)s'
            self._fmt += '\n'
            self._fmt += self.fmt_prefix
            self._fmt += '%(pathname)s:%(lineno)d'

        return logging.Formatter.format(self, record)


def setup_logging(configfile, stdout=False):
    log = logging.getLogger('diamond')

    try:
        config_parser = configparser.RawConfigParser(strict=False)
        config_parser.read(configfile)
        logging.config.fileConfig(config_parser, disable_existing_loggers=False)

        # if the stdout flag is set, we use the log level of the root logger
        # for logging to stdout, and keep all loggers defined in the conf file
        if stdout:
            rootLogLevel = logging.getLogger().getEffectiveLevel()

            log.setLevel(rootLogLevel)
            streamHandler = logging.StreamHandler(sys.stdout)
            streamHandler.setFormatter(DebugFormatter())
            streamHandler.setLevel(rootLogLevel)
            log.addHandler(streamHandler)

    except Exception as e:
        sys.stderr.write("Error occurs when initialize logging: ")
        sys.stderr.write(str(e))
        sys.stderr.write(os.linesep)

    return log
