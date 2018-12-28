from copy import deepcopy


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
