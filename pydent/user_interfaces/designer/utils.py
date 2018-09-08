def arr_to_pairs(arr):
    arr1 = arr[:-1]
    arr2 = arr[1:]
    return list(zip(arr1, arr2))