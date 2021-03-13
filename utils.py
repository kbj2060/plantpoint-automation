from logger.custom_logger import custom_logger


def handle_arr_length(arr):
    if len(arr) != 1:
        custom_logger.error("Status Length Error Occurred!")
        raise ValueError()
    else:
        return arr[0]


def grouping(arr):
    result = dict()
    for key, value in arr:
        if key not in result:
            result[key] = []
        result[key].append(value)
    return result
