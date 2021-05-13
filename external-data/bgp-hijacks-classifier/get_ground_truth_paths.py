#!/usr/bin/python2

'''
WARNING: this must be run with python2
'''

import pickle
import argparse


def parse_path(path_str):
    path = path_str.split(' ')

    path_clean = [path[0]]
    for u in path[1:]:
        if u != path_clean[-1]:
            path_clean.append(u)

    path_clean_str = ' '.join(path_clean)

    return path_clean_str


def get_hijacked_paths(filepath):

    unique = set()

    f = open(filepath, 'r')
    x = pickle.load(f)

    for collector, data in x['as_paths'].items():
        for ip, prefixed_paths in data.items():
            for prefix, anouncement in prefixed_paths.items():
                if prefix == x['hijack_prefix']:
                    for a in anouncement:
                        if a[2] and (a[2] not in unique):
                            path = parse_path(a[2])
                            print(path)
                            unique.add(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help='path to the pickle file')
    args = parser.parse_args()

    get_hijacked_paths(args.filepath)

