import pytest

from pydent.utils import MagicList, magiclist


def test_MagicList_inheritance():
    x = MagicList([1, 2, 3])
    assert isinstance(x, list)
    assert isinstance(x, MagicList)
    assert list(x) == [1, 2, 3]


def test_MagicList_chaining():
    """Tests various chaining of MagicList attributes. Applying an attribute or function
    should be equivalent to a list comperhension (but less code necessary)."""

    xlist = [" the cow", "jumped    ", "over the ", "moon"]
    xmagic = MagicList(xlist)

    # xmagic should be functionally equiavlent as a parameter
    assert ''.join(xmagic) == ''.join(xlist)

    # .strip() should functionally equivalent to a list comprehension
    assert xmagic.strip() == [x.strip() for x in xlist]

    # .strip().upper() should be chainable
    assert xmagic.strip().upper() == [x.strip().upper() for x in xlist]

    # list used to derive the MagicList should be distinct from the MagicList instance
    xlist.pop()
    assert len(xlist) + 1 == len(xmagic)

    # should be able to apply list functions to xmagic
    xmagic.pop()
    assert len(xlist) == len(xmagic)


def test_MagicList_apply():
    """MagicList should be able to apply a callable function to all of its members."""

    xlist = [" the cow", "jumped    ", "over the ", "moon"]
    xmagic = MagicList(xlist)

    fxn = lambda x: x.strip()

    assert xmagic.apply(fxn) == [x.strip() for x in xlist]


def test_MagicList_callable():
    """MagicList can contain a list of callables, that can be applied using arguments.
    In this case, we have a list of lambdas and are applying a single parameter to each
    lambda."""

    xlist = [lambda x: x ** 2, lambda y: y ** 3]
    xmagic = MagicList(xlist)

    assert xmagic(3) == [3 ** 2, 3 ** 3]
    assert xmagic(4) == [4 ** 2, 4 ** 3]


def test_MagicList_getitem():
    """We can apply dictionary keys to a MagicList. However, applying ...['x'] should raise a type
    error, as the magiclist expects [int] to return the positional object in the list. However, '.get'
    get return the dictionary key"""
    xlist = [
        {'x': 5, 'y': 6},
        {'x': 4, 'y': 60}
    ]
    xmagic = MagicList(xlist)

    with pytest.raises(TypeError):
        xmagic['x']

    assert xmagic.get('x') == [5, 4]
    assert xmagic.get('y') == [6, 60]


def test_MagicList_indexing():
    """Positional indices should work on MagicList instances"""
    xlist = [
        {'x': 5, 'y': 6},
        {'x': 4, 'y': 60},
        {'x': 3, 'y': 70}
    ]
    xmagic = MagicList(xlist)

    assert xmagic[-1] == xlist[-1]
    assert xmagic[0] == xlist[0]


def test_MagicList_slicing():
    """List slices of magiclist should return a new MagicList instance"""
    xlist = [
        {'x': 5, 'y': 6},
        {'x': 4, 'y': 60},
        {'x': 3, 'y': 70}
    ]
    xmagic = MagicList(xlist)

    assert isinstance(xmagic[1:-1], MagicList)
    assert len(xmagic[1:]) == 2
    assert list(xmagic[:-1]) == [{'x': 5, 'y': 6}, {'x': 4, 'y': 60}, ]


def test_MagicList_copy():
    xlist = [" the cow", "jumped    ", "over the ", "moon"]
    xmagic1 = MagicList(xlist)
    xmagic2 = MagicList(xlist)

    assert xmagic1 == xmagic2

    # altering two different lists
    xmagic1[0] = " the bear"
    assert not xmagic1 == xmagic2

    # copy equivalent
    copied_xmagic1 = xmagic1[:]
    assert copied_xmagic1 == xmagic1

    # alter copy
    copied_xmagic1[0] = 0
    assert not copied_xmagic1 == xmagic1


def test_MagicList_2D():
    xlist = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    xmagic = MagicList(xlist)

    assert xmagic[1] == [4, 5, 6]


def test_MagicList_TypeError():
    """Only iterables should be allowed to create MagicLists"""
    with pytest.raises(TypeError):
        MagicList(5)

    with pytest.raises(TypeError):
        MagicList(False)


def test_magiclist_decorator():
    """Ensures that magiclist decorator forces returned iterable to a MagicList"""

    @magiclist
    def returns_a_list():
        somelist = [1, 2, 3]
        return somelist

    @magiclist
    def returns_a_tuple():
        sometuple = (1, 2, 3)
        return sometuple

    @magiclist
    def returns_a_dict_keys():
        somedict = {1: 2, 3: 5}
        return somedict.keys()

    assert isinstance(returns_a_list(), MagicList)
    assert isinstance(returns_a_tuple(), MagicList)
    assert isinstance(returns_a_dict_keys(), MagicList)


def test_magiclist_decorator_TypeError():
    """If returned value is not iterable, value should be returned without forcing to a magiclist """

    @magiclist
    def returns_int():
        return 5

    assert returns_int() == 5


def test_magiclist_applied_to_class_method():
    """magiclist decorator should work using class methods"""

    class Klass(object):
        def __init__(self):
            pass

        @magiclist
        def foo(self):
            return [1, 2, 3]

    assert isinstance(Klass().foo(), MagicList)
