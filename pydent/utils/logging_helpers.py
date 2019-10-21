import difflib
from pprint import pformat

from pydent.utils import condense_long_lists


def did_you_mean(word, words):
    msg = ""
    try:
        matches = difflib.get_close_matches(word, words)
        if len(matches) == 1:
            msg = 'Did you mean "{}"?'.format(matches[0])
        elif len(matches) > 1:
            msg = "Did you mean any of these? {}".format(pformat(matches))
    except TypeError:
        pass
    finally:
        return msg
