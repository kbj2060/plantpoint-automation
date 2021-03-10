def grouping(arr):
    result = dict()
    for key, value in arr:
        if key not in result:
            result[key] = []
        result[key].append(value)
    return result
