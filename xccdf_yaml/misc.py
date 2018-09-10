def deepmerge(left, right):
    def copy_of(item):
        if isinstance(item, dict):
            result = {}
            result.update(item)
        elif isinstance(item, list):
            result = []
            result.extend(item)
        else:
            result = item
        return result

    if left is None and right is None:
        return None

    if left is None:
        return copy_of(right)

    if right is None:
        return copy_of(left)

    if type(left) != type(right):
        raise Exception("Type mismatch")

    if isinstance(left, dict):
        result = {}
        for lkey, lvalue in left.items():
            result[lkey] = deepmerge(lvalue, right.get(lkey))
        for rkey, rvalue in right.items():
            result[rkey] = deepmerge(left.get(rkey), rvalue)
        return result

    if isinstance(left, list):
        result = []
        result.extend(left)
        result.extend(right)
        return result

    return right
