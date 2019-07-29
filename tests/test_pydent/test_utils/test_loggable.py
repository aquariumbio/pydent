from pydent.utils import Loggable
from uuid import uuid4


class Foo(object):
    def __init__(self):
        self.log = Loggable(self)

    def bar(self):
        self.log.info("bar")


def test_basic():
    foo = Foo()
    foo.log.set_verbose(True)
    foo.log.info("This is some information")


def test_log_info(capsys):
    msg = str(uuid4())
    foo = Foo()
    foo.log.set_verbose(True)
    foo.log.info(msg)
    _, log = capsys.readouterr()
    assert "INFO" in log
    assert "Foo" in log
    assert msg in log

    foo.log.set_verbose(False)
    foo.log.info(msg)
    _, log = capsys.readouterr()
    assert not log


def test_tb_limit(capsys):
    msg = str(uuid4())
    foo = Foo()
    foo.log.set_verbose(True, tb_limit=10)
    foo.bar()
