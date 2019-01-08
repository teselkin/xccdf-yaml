import re

from copy import deepcopy
from xccdf_yaml.appdata import APPDATA


def deepmerge(left, right, deep_copy=False):
    def _deepcopy(obj, deep_copy=False):
        if deep_copy:
            return deepcopy(obj)
        return obj

    if left is None:
        if right is None:
            return None
        return _deepcopy(right, deep_copy)
    elif right is None:
        return _deepcopy(left, deep_copy)

    if type(left) != type(right):
        raise Exception("Type mismatch")

    if isinstance(left, dict):
        result = {}
        for lkey, lvalue in left.items():
            result[lkey] = deepmerge(lvalue, right.get(lkey),
                                     deep_copy=deep_copy)
        for rkey, rvalue in right.items():
            result[rkey] = deepmerge(left.get(rkey), rvalue,
                                     deep_copy=deep_copy)
        return result

    if isinstance(left, list):
        result = _deepcopy(left, deep_copy)
        result.extend(_deepcopy(right, deep_copy))
        return result

    return right


def unlist(seq):
    if isinstance(seq, list):
        for x in seq:
            for y in unlist(x):
                yield y
    else:
        yield seq


def resolve_file_ref(filename, workdir=None, basedir=None):
    if basedir is None:
        basedir = APPDATA['basedir']

    if workdir is None:
        workdir = APPDATA['workdir']

    match = re.match(r'<(.*)>', filename)
    if match:
        return workdir, match.group(1)
    else:
        return basedir, filename
