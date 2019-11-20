import logging
import math
import pprint
import time
import traceback
import weakref
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from itertools import count
from logging import CRITICAL
from logging import DEBUG
from logging import ERROR
from logging import INFO
from logging import WARN
from logging import WARNING
from warnings import warn

from colorlog import ColoredFormatter
from tqdm import tqdm


def utcnow():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def pprint_data(data, width=80, depth=10, max_list_len=20, compact=True, indent=1):
    """Pretty print data."""
    return pprint.pformat(
        condense_long_lists(data, max_list_len=max_list_len),
        indent=indent,
        width=width,
        depth=depth,
        compact=compact,
    )


class LoggableWarning(Warning):
    """Generic logger warning."""


class LoggableException(Exception):
    """Generic exception for loggable class."""


class LoggableHandler(logging.Handler):
    pass


class TqdmLoggingHandler(LoggableHandler):
    def __init__(self, level=logging.NOTSET, tqdm=tqdm):
        super().__init__(level)
        self._tqdm = tqdm
        self.tb_limit = 0

    def emit(self, record):
        try:
            msg = self.format(record)
            self._tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def condense_long_lists(d, max_list_len=20):
    """Condense the long lists in a dictionary.

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
    DEFAULT_FORMAT = "%(log_color)s%(levelname)s - %(name)s - %(asctime)s - %(message)s"
    DEFAULT_COLORS = {
        "DEBUG": "cyan",
        "INFO": "white",
        "SUCCESS:": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }
    graph = {}
    registered = {}  # id to Loggable
    counter = count()

    def __init__(self, object_or_name, format=None, log_colors=None, tqdm=tqdm):
        """Instantiates a new logger.

        :param object_or_name: The name or object to attach the logger. If o
            bject is provided, the name
            is produced from the object instance.
        :param format: The logger format. Default is found at
            Loggable.DEFAULT_FORMAT
        :param log_colors: The logger colors. Default is found
            Loggable.DEFAULT_COLORS.
        :param tqdm: This tqdm class to instantiate progress bars with.
            Default is tqdm.tqdm.
        """
        if isinstance(object_or_name, str):
            self.name = object_or_name
        else:
            self.name = "{}(id={})".format(
                object_or_name.__class__.__name__, id(object_or_name)
            )

        self.format = format or self.DEFAULT_FORMAT
        self.log_colors = log_colors or self.DEFAULT_COLORS
        self._tqdm = tqdm
        self._id = next(self.counter)

    def _new_logger(self, name, level=logging.ERROR):
        """Instantiate a new logger with the given name.

        If channel handler exists, do not create a new one.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handlers = self._log_handlers(logger)
        # make stream handler
        if not handlers:
            handler = TqdmLoggingHandler(level, tqdm=self._tqdm)
            handler.tb_limit = 0
            formatter = ColoredFormatter(self.format, log_colors=self.log_colors)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            handler = handlers[0]
        return logger, handler

    @property
    def _children(self):
        """The logger's children loggers."""
        return self.registered.setdefault(self._id, weakref.WeakValueDictionary())

    @property
    def logger(self):
        """The native logger."""
        return self._new_logger(self.name)[0]

    @property
    def logger_handlers(self):
        """The logging handlers for this logger."""
        return self._log_handlers(self.logger)

    def set_tb_limit(self, limit):
        """Set the throwback limit."""
        for h in self.logger.handlers:
            h.tb_limit = limit
        return self

    def level_name(self):
        """Return the current level name, as a string."""
        return logging._levelToName[self.level()]

    def level(self):
        """Return the current level, as an int."""
        return self.logger_handlers[0].level

    def is_enabled(self, level):
        """Returns whether this logger is enabled for the level specified."""
        level = self._get_level(level)
        return level >= self.level()

    def _get_level(self, level):
        if isinstance(level, str):
            try:
                level = {
                    "INFO": INFO,
                    "ERROR": ERROR,
                    "DEBUG": DEBUG,
                    "CRITICAL": CRITICAL,
                    "WARNING": WARNING,
                    "WARN": WARN,
                }[level.upper()]
            except KeyError as e:
                raise KeyError("Level {} not recognized.".format(level)) from e
        return level

    def set_level(self, level, tb_limit=None):
        """Sets the level for this logger and its children."""
        level = self._get_level(level)
        self.logger.setLevel(level)
        for h in self.logger.handlers:
            h.setLevel(level)
        if tb_limit is not None:
            self.set_tb_limit(tb_limit)
        for child in self._children.values():
            child.set_level(level, tb_limit=tb_limit)
        return self

    def set_verbose(self, verbose, tb_limit=0):
        """Sets to 'INFO' if True, or 'ERROR' if False."""
        if verbose:
            return self.set_level(logging.INFO, tb_limit)
        else:
            return self.set_level(logging.ERROR, tb_limit)

    pprint_data = staticmethod(pprint_data)

    def tqdm(self, iterable, level, *args, **kwargs):
        """Produce a logged progress bar for an interable."""
        level = self._get_level(level)
        if self.is_enabled(level):
            progress_bar = self._tqdm(iterable, *args, **kwargs)
            progress_bar.set_description(
                "{:8} {}".format(logging._levelToName[level], progress_bar.desc)
            )
            return progress_bar
        else:
            return iterable

    def _add_child(self, other):
        self._children[other._id] = other
        return other

    def _log_handlers(self, logger):
        return [h for h in logger.handlers if issubclass(type(h), LoggableHandler)]

    def log(self, msg, level):
        """Log at specified level."""
        level = self._get_level(level)
        logger = self.logger
        logger.log(level, msg)
        if logger.isEnabledFor(level):
            tb_limit = self.logger_handlers[0].tb_limit
            if tb_limit:
                traceback.print_stack(limit=tb_limit)
        return self

    def critical(self, msg):
        """Log critical error."""
        return self.log(msg, CRITICAL)

    def error(self, msg):
        """Log error."""
        return self.log(msg, ERROR)

    def warn(self, msg):
        """Log warning."""
        return self.log(msg, WARNING)

    def info(self, msg):
        """Log info."""
        return self.log(msg, INFO)

    def debug(self, msg):
        """Log debug."""
        return self.log(msg, DEBUG)

    def __copy__(self):
        return self.copy()

    def copy(self, name=None):
        """Copy this logger."""
        copied = self.__class__(
            name or self.name,
            format=self.format,
            log_colors=self.log_colors,
            tqdm=self._tqdm,
        )
        copied.set_level(self.level())
        return copied

    def spawn(self, name=None):
        """Spawn a child logger.

        Child loggers will automatically inherit the level of their
        parent. This inheritance occurs after creation as well.
        """
        return self._add_child(self.copy(name))

    def timeit(self, level, prefix=""):
        """Spawn a logger that computes the time it takes to run commands.

        The start time and total time will be logged.
        """
        child = TimedLoggable(
            self.name,
            level,
            prefix=prefix,
            format=self.format,
            log_colors=self.log_colors,
            tqdm=self._tqdm,
        )
        child.set_level(self.level())
        return self._add_child(child)

    def track(self, level, total=None, desc=None):
        """Spawn a progress bar logger, which can update a progress bar."""
        child = ProgressLoggable(
            self.name,
            level,
            desc=desc,
            total=total,
            format=self.format,
            log_colors=self.log_colors,
            tqdm=self._tqdm,
        )
        child.set_level(self.level())
        return self._add_child(child)

    # alias for 'track', which is hard to remember
    pbar = track

    def __call__(self, name):
        return self.spawn(name)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__ = d

    # def __str__(self):
    #     return "<{} {}>".format(self.__class__.__name__, self.logger)
    #
    # def __repr__(self):
    #     return str(self)


class RenamedLoggable(Loggable):
    def __init__(self, object_or_name, format=None, log_colors=None, tqdm=tqdm):
        new_name = "{}({})".format(self.__class__.__name__, object_or_name)
        super().__init__(new_name, format, log_colors, tqdm)


class LockedLoggable(RenamedLoggable):
    def __init__(self, object_or_name, level, format=None, log_colors=None, tqdm=tqdm):
        super().__init__(object_or_name, format, log_colors, tqdm)
        self.locked_level = level

    def is_enabled(self, level=None):
        level = level or self.locked_level
        return super().is_enabled(level)

    def log(self, msg, level=None):
        level = level or self.locked_level
        super().log(msg, level)


class Enterable(ABC):
    @abstractmethod
    def enter(self):
        pass

    @abstractmethod
    def exit(self):
        pass

    def __enter__(self):
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.exit()
        except Exception as e:
            warn(
                LoggableWarning(
                    "Exception during 'exit' of {}: {}\n{}".format(self, type(e), e)
                )
            )


class ProgressLoggable(Enterable, LockedLoggable):
    def __init__(
        self,
        object_or_name,
        level,
        total,
        desc,
        format=None,
        log_colors=None,
        tqdm=tqdm,
    ):
        super().__init__(
            object_or_name, level, format=format, log_colors=log_colors, tqdm=tqdm
        )
        self.desc = desc
        self.total = total
        self.pbar = None

    def update(self, x=1, msg=""):
        if self.pbar is None:
            raise LoggableException(
                "Progress bar not instantiated. Run 'enter()' or 'with' to instantiate."
            )
        if msg:
            self.log(msg)
        if self.is_enabled():
            self.pbar.update(x)

    def __call__(self, iterable, *args, **kwargs):
        d = {"desc": self.desc}
        d.update(kwargs)
        return self.tqdm(iterable, self.locked_level, *args, **d)

    def enter(self):
        if self.is_enabled():
            self.pbar = tqdm(total=self.total)
        else:
            self.pbar = 0
        return self

    def exit(self):
        if self.is_enabled():
            self.pbar.close()
        else:
            self.pbar = 0
        return self


class TimedLoggable(Enterable, LockedLoggable):
    def __init__(
        self, object_or_name, level, prefix="", format=None, log_colors=None, tqdm=tqdm
    ):
        super().__init__(
            object_or_name, level, format=format, log_colors=log_colors, tqdm=tqdm
        )
        now = time.time()
        self.t1 = now
        self.t2 = None
        self.time = None
        self.prefix = prefix

    def log(self, msg, level=None):
        if self.prefix:
            msg = '{}("{}"): {}'.format(self.__class__.__name__, self.prefix, msg)
        super().log(msg, level)

    def enter(self):
        now = time.time()
        self.t1 = now
        self.log("Started at {}".format(self.t1))
        return self

    def exit(self):
        t2 = time.time()
        self.t2 = t2
        self.time = self.t2 - self.t1
        self.log("Finished in {}.".format(self.time))
        return self


class LoggableFactory:
    def __init__(self, format=None, log_colors=None, tqdm=tqdm):
        self.format = format
        self.log_colors = log_colors
        self._tqdm = tqdm

    def __call__(self, name):
        return Loggable(
            name, format=self.format, log_colors=self.log_colors, tqdm=self._tqdm
        )
