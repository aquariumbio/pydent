import logging


def new_logger(name, level=logging.ERROR):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # make stream handler
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    else:
        ch = logger.handlers[0]
    return logger, ch


class Loggable:

    def init_logger(self, name):
        self._logger, self._log_handler = new_logger(name)

    def set_verbose(self, verbose):
        if verbose:
            self._log_handler.setLevel(logging.INFO)
        else:
            self._log_handler.setLevel(logging.ERROR)

    def _info(self, msg):
        self._logger.info(msg)

    def _error(self, msg):
        self._logger.error(msg)
