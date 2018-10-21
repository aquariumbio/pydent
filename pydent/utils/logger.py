import logging


def new(name, level=logging.ERROR):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # make stream handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger, ch