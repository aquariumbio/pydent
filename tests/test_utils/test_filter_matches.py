import pytest

from pydent.utils import filter_list

@pytest.fixture
def example():
    class Foo:
        pass

    f1 = Foo()
    f2 = Foo()
    f3 = Foo()

    f1.name = "Joe"
    f1.role = "Worker"
    f1.happy = False
    f2.name = "Joe"
    f2.role = "Boss"
    f2.happy = True

    f3.role = "Worker"
    f3.happy = True
    return f1, f2, f3


# def test_filter_matches(example):
#     f1, f2, f3 = example
#
#     res = filter_matches(f1, [f1, f2, f3], attributes=('role',))
#     assert len(res) == 2
#     assert res == [f1, f3]
#
#     res = filter_matches(f3, [f1, f2, f3], attributes=('happy',))
#     assert len(res) == 2
#     assert res == [f2, f3]
#
#     res = filter_matches(f3, [f1, f2, f3], attributes=('happy', 'role'))
#     assert len(res) == 1
#     assert res == [f3]


def test_filter_list(example):
    class MyList(list):
        pass

    f1, f2, f3 = example

    res = filter_list(MyList([f1, f2, f3]), happy=True)
    assert isinstance(res, MyList)
    assert res == [f2, f3]

    res = filter_list([f1, f2, f3], happy=True, role='Worker')
    assert res == [f3]
