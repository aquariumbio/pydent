import logging
import pickle
import time
from uuid import uuid4

import pytest
from tqdm import tqdm

from pydent.utils.loggable import Enterable
from pydent.utils.loggable import Loggable
from pydent.utils.loggable import LoggableWarning


class Foo:
    def __init__(self):
        self.log = Loggable(self)

    def bar(self):
        self.log.info("bar")


def test_init_with_class():
    foo = Foo()
    foo.log.set_level("INFO")
    foo.log.info("ok")


class TestLogging:
    def test_basic(self):
        foo = Foo()
        foo.log.set_verbose(True)
        foo.log.info("This is some information")
        foo.log.info("This is more information")

    @pytest.mark.parametrize(
        "level",
        [
            "error",
            "critical",
            "debug",
            "info",
            "warn",
            "ERROR",
            "CRITICAL",
            "DEBUG",
            "INFO",
            "WARN",
        ],
    )
    @pytest.mark.parametrize(
        "level_as_str", [True, False], ids=["LVL_AS_STR", "LVL_AS_INT"]
    )
    def test_does_log(self, level, level_as_str, capsys):
        logger = Loggable("test")

        fxn = getattr(logger, level.lower())

        level_str = level

        if not level_as_str:
            level = getattr(logging, level.upper())

        # check log
        logger.set_level(level)
        msg = str(uuid4())
        fxn(msg)
        log, _ = capsys.readouterr()

        print(log)
        assert msg in log
        assert level_str.upper() in log

    @pytest.mark.parametrize("level", ["error", "critical", "debug", "info", "warn"])
    def test_does_not_log(self, level, capsys):
        logger = Loggable("test")
        fxn = getattr(logger, level.lower())

        # does log
        logger.set_level(level)
        msg = str(uuid4())
        fxn(msg)
        log, _ = capsys.readouterr()
        # print(log)
        assert msg in log
        assert level.upper() in log

        # does not log
        logger.set_level(logging.CRITICAL + 1)
        msg = str(uuid4())
        fxn(msg)
        log, _ = capsys.readouterr()
        assert not log
        assert not _

    @pytest.mark.parametrize("level", ["error", "critical", "debug", "info", "warn"])
    def test_log(self, level, capsys):
        logger = Loggable("test")
        msg = str(uuid4())
        logger.set_level(level)
        logger.log(msg, level)
        log, _ = capsys.readouterr()
        print(log)
        assert msg in log


class TestProgressBar:
    def test_basic_progress_bar(self):
        log = Loggable("test")
        for x in tqdm(range(10)):
            log.info(x)
            time.sleep(0.01)
        log.info("This is more information")

    @pytest.mark.parametrize("level", ["error", "critical", "debug", "info", "warn"])
    def test_leveled_progress_bar(self, level):
        log = Loggable("Test")
        for x in log.tqdm(range(10), level, desc="this is a description"):
            log.info(x)
        log.info("This is more information")


class TestTimedLoggable:
    def test_basic_log(self, capsys):
        logger = Loggable("loggable_test")
        logger.set_level("INFO")

        logger.timeit("INFO").info("log2")
        log, _ = capsys.readouterr()
        assert "INFO" in log

    def test_spawn(self, capsys):
        log = Loggable("loggable_test")
        log.set_level("INFO")
        log2 = log.timeit(logging.INFO)
        log2.enter()
        log2.info("log2")
        log2.exit()
        msg, _ = capsys.readouterr()
        assert "started" in msg.lower()
        assert "log2" in msg
        assert "finished" in msg.lower()

    def test_timeit(self):
        log = Loggable("loggable_test")
        log.set_level("INFO")

        with log.timeit(logging.INFO, "TimeItTest"):
            log.info("ok")

    def test_timeit(self, capsys):
        log = Loggable("loggable_test")
        log.set_level("INFO")

        timeit = log.timeit(logging.INFO)
        timeit.enter()
        timeit.info("ok")
        time.sleep(0.1)
        timeit.exit()
        log, _ = capsys.readouterr()
        print(log)
        assert "started" in log.lower()
        assert "ok" in log
        assert "finished" in log.lower()

    def test_does_not_log(self, capsys):
        log = Loggable("loggable_test")
        log.set_level("ERROR")

        timeit = log.timeit(logging.INFO)
        timeit.enter()
        timeit.info("ok")
        time.sleep(0.1)
        timeit.exit()
        log, _ = capsys.readouterr()
        print(log)
        assert not log

    def test_prefix(self, capsys):
        log = Loggable("loggable_test")
        log.set_level("INFO")

        timeit = log.timeit(logging.INFO, "prefix")
        timeit.enter()
        timeit.info("Some information")
        timeit.exit()
        log, _ = capsys.readouterr()
        print(log)
        assert "prefix" in log


class TestProgressLoggable:
    def test_basic_log(self, capsys):
        logger = Loggable("loggable_test")
        logger.set_level("INFO")

        logger.track("INFO").info("log2")
        log, _ = capsys.readouterr()
        assert "INFO" in log

    def test_update(self, capsys):
        logger = Loggable("loggable_test")
        logger.set_level("INFO")

        track = logger.track("INFO", total=100).enter()
        track.update(10, "10% there!")
        track.update(20, "20% there!")
        track.exit()

    def test_not_enabled(self):
        logger = Loggable("loggable_test")
        logger.set_level("CRITICAL")

        track = logger.track("INFO")
        assert not track.is_enabled()

        track = logger.track("CRITICAL")
        assert track.is_enabled()

    def test_track_iterable(self):
        logger = Loggable("loggable_test")
        logger.set_level("INFO")
        track = logger.track("INFO", desc="This is a progress bar")
        for x in track(range(10)):
            track.info(x)

    def test_no_update(self, capsys):
        logger = Loggable("loggable_test")
        logger.set_level("CRITICAL")
        assert not logger.is_enabled("INFO")

        track = logger.track("INFO", total=100).enter()
        track.update(10, "10% there!")
        track.update(20, "20% there!")
        track.exit()


def test_tb_limit(capsys):
    foo = Foo()
    foo.log.set_verbose(True, tb_limit=10)
    foo.bar()


def test_copy(capsys):
    """We expect copies to initially inherit the log level of their parents."""

    logger1 = Loggable("Parent")
    logger1.set_level("INFO")
    logger2 = logger1.copy("newname")
    assert logger2.name == "newname"
    # logger 1 output
    logger1.info("msg")
    log, _ = capsys.readouterr()
    assert "msg" in log

    # logger 2 output
    logger2.info("msg")
    log, _ = capsys.readouterr()
    assert "msg" in log

    logger1.set_level("ERROR")

    # logger 1 output
    logger1.info("msg")
    log, _ = capsys.readouterr()
    assert not log

    # logger 2 output
    logger2.info("msg")
    log, _ = capsys.readouterr()
    assert "msg" in log


def test_spawn(capsys):
    """We expect spawned copies to inherit the log level of their parents."""

    logger1 = Loggable("Parent")
    logger1.set_level("INFO")
    logger2 = logger1.spawn("new name")

    # logger 1 output
    logger1.info("msg")
    log, _ = capsys.readouterr()
    assert "msg" in log

    # logger 2 output
    logger2.info("msg")
    log, _ = capsys.readouterr()
    assert "msg" in log

    logger1.set_level("ERROR")

    # logger 1 no output
    logger1.info("msg")
    log, _ = capsys.readouterr()
    assert not log

    # logger 2 no output
    logger2.info("msg")
    log, _ = capsys.readouterr()
    assert not log


def test_copy_object_with_logger():
    class LoggableObject:
        @property
        def logger(self):
            return Loggable(self)

    class Foo(LoggableObject):
        def __init__(self):
            pass

    from copy import copy

    foo = Foo()
    foo.logger.set_level("INFO")
    print(id(foo.logger))
    foo.logger.info("HEY!")
    bar = copy(foo)

    del foo
    bar.logger.info("HEY!")


def test_pickle():

    logger1 = Loggable("Parent")
    s = pickle.dumps(logger1)
    logger2 = pickle.loads(s)

    assert logger1.name == "Parent"


def test_pickle_span():

    logger1 = Loggable("Parent")
    logger1.set_level("INFO")
    logger2 = logger1.spawn("new name")

    assert logger1._children
    assert logger2._children == {}

    logger3 = pickle.loads(pickle.dumps(logger1))
    logger4 = pickle.loads(pickle.dumps(logger2))

    assert dict(logger3._children)
    assert logger3._children[logger2._id] is logger2
    assert logger4._children == {}

    for lvl in ["ERROR", "DEBUG", "INFO"]:
        logger1.set_level(lvl)
        assert logger1.level_name() == lvl
        assert logger2.level_name() == lvl
        assert logger3.level_name() == lvl
        assert logger4.level_name() == lvl


class TestException:
    def test_exception_during_exit_raises_only_warning(self):
        class FooClass(Enterable):
            def enter(self):
                return self

            def exit(self):
                raise ValueError("This is my warning")

        foo = FooClass()

        with pytest.warns(LoggableWarning) as record:
            with foo as f:
                pass

            assert len(record) == 1
            msg = record[0].message.args[0]

            assert "ValueError" in msg
            assert "Exception during 'exit' of " in msg
            assert "This is my warning" in msg

    def test_exception_in_enterable_is_raised(self, capsys):
        class FooClass(Enterable):
            def enter(self):
                return self

            def exit(self):
                raise ValueError("This is my warning")

        foo = FooClass()

        with pytest.raises(ValueError) as e:
            with foo as f:
                raise ValueError("This is my error")

    def test_exception_is_raised_for_timeit(self):
        logger = Loggable("test loggable")
        with pytest.raises(ValueError) as e:
            with logger.timeit("ERROR"):
                raise ValueError

    def test_exception_is_raised_for_track(self):
        logger = Loggable("test loggable")
        with pytest.raises(ValueError) as e:
            with logger.track("ERROR", 100):
                raise ValueError

    def test_exception_is_raised_for_pbar(self):
        logger = Loggable("test loggable")
        with pytest.raises(ValueError) as e:
            for i in logger.tqdm(range(10), "ERROR"):
                if i == 5:
                    raise ValueError
