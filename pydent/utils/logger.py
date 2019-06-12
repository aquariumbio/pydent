import logging
import math
import pprint


def new_logger(name, level=logging.ERROR):
    """Instantiate a new logger with the given name. If channel handler exists, do not create a new one."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # make stream handler
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    else:
        ch = logger.handlers[0]
    return logger, ch


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


class Loggable:
    def init_logger(self, name):
        self._logger_name = name
        new_logger(name)

    @property
    def _logger(self):
        return logging.getLogger(self._logger_name)

    @property
    def _log_handler(self):
        return self._logger.handlers[0]

    def set_verbose(self, verbose):
        if verbose:
            self._log_handler.setLevel(logging.INFO)
        else:
            self._log_handler.setLevel(logging.ERROR)

    def _pprint_data(
        self, data, width=80, depth=10, max_list_len=20, compact=True, indent=1
    ):
        return pprint.pformat(
            condense_long_lists(data, max_list_len=max_list_len),
            indent=indent,
            width=width,
            depth=depth,
            compact=compact,
        )

    def _info(self, msg):
        self._logger.info(msg)

    def _error(self, msg):
        self._logger.error(msg)
