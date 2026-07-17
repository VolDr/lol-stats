import sys
import os
from multiprocessing import Pool as ThreadPool


def work_parallel(function, numbers, thread_number=4):
    pool = ThreadPool(thread_number)
    results = pool.map(function, numbers)
    return results


def remove_dict_and_lists_from_dict(dictionary):
    dictionary = dictionary.copy()
    for key, elem in dict(dictionary).items():
        if isinstance(elem, list) or isinstance(elem, dict):
            del dictionary[key]
    return dictionary


def add_prefix_to_numeric_keys(dictionary):
    for key, elem in dictionary.copy().items():
        try:
            int(key.split('-')[0])
        except:
            pass
        else:
            new_key = f'minutes{key}'
            new_key = new_key.replace('-', '_')
            dictionary[new_key] = dictionary[key]
            del dictionary[key]