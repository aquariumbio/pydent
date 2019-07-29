import logging
import math
import pprint
import traceback
from logging import DEBUG, INFO, CRITICAL, ERROR, WARNING
from colorlog import ColoredFormatter


def new_logger(name, level=logging.ERROR):
    """Instantiate a new logger with the given name. If channel handler exists, do not create a new one."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # make stream handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.tb_limit = 0
        formatter = ColoredFormatter(
            "%(log_color)s%(levelname)s - %(name)s - %(asctime)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
                "SUCCESS:": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        handler = logger.handlers[0]
    return logger, handler


def condense_long_lists(d, max_list_len=20):
    """
    Condense the long lists in a dictionary

    :param d: dictionary to condense
    :type d: dict
    :param max_len: max length of lists to display
    :type max_len: int
    :return:
    :rtype:
    """
    if isinstance(d, dict):
        return_dict = {}
        for k in d:
            return_dict[k] = condense_long_lists(dict(d).pop(k))
        return dict(return_dict)
    elif isinstance(d, list):
        if len(d) > max_list_len:
            g = max_list_len / 2
            return d[: math.floor(g)] + ["..."] + d[-math.ceil(g) :]
        else:
            return d[:]
    return str(d)


class Loggable(object):
    def __init__(self, inst, name=None):
        self.instance = inst
        if name is None:
            self.name = "{}(id={})".format(self.instance.__class__, id(self.instance))
        else:
            self.name = name

    @property
    def logger(self):
        return new_logger(self.name)[0]

    def set_tb_limit(self, limit):
        for h in self.logger.handlers:
            h.tb_limit = limit

    def set_log_level(self, level, tb_limit=None):
        for h in self.logger.handlers:
            h.setLevel(level)
        if tb_limit is not None:
            self.set_tb_limit(tb_limit)

    def set_verbose(self, verbose, tb_limit=0):
        if verbose:
            self.set_log_level(logging.INFO, tb_limit)
        else:
            self.set_log_level(logging.ERROR, tb_limit)

    def pprint_data(
        self, data, width=80, depth=10, max_list_len=20, compact=True, indent=1
    ):
        return pprint.pformat(
            condense_long_lists(data, max_list_len=max_list_len),
            indent=indent,
            width=width,
            depth=depth,
            compact=compact,
        )

    def log(self, msg, level):
        self.logger.log(level, msg)
        if self.logger.isEnabledFor(level):
            tb_limit = self.logger.handlers[0].tb_limit
            if tb_limit:
                traceback.print_stack(limit=tb_limit)

    def critical(self, msg):
        self.log(msg, CRITICAL)

    def error(self, msg):
        self.log(msg, ERROR)

    def warn(self, msg):
        self.log(msg, WARNING)

    def info(self, msg):
        self.log(msg, INFO)

    def debug(self, msg):
        self.log(msg, DEBUG)
