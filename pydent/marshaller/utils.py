def make_signature_str(_args, _kwargs):
    return "({}, {})".format(
        ", ".join([str(_a) for _a in _args]),
        ", ".join(["{}={}".format(name, val) for name, val in _kwargs.items()]),
    )
