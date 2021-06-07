#!/usr/bin/env python3

import argparse
import datetime as dt
import itertools as it
import pybgpstream
import sys

from tqdm import tqdm


COLLECTORS = [
    'route-views3',
    'route-views4',
    'route-views6',
    'route-views.amsix',
    'route-views.chicago',
    'route-views.chile',
    'route-views.eqix',
    'route-views.flix',
    'route-views.gorex',
    'route-views.isc',
    'route-views.kixp',
    'route-views.jinx',
    'route-views.linx',
    'route-views.napafrica',
    'route-views.nwax',
    'route-views.phoix',
    'route-views.telxatl',
    'route-views.wide',
    'route-views.sydney',
    'route-views.saopaulo',
    'route-views2.saopaulo',
    'route-views.sg',
    'route-views.perth',
    'route-views.sfmix',
    'route-views.soxrs',
    'route-views.mwix',
    'route-views.rio',
    'route-views.fortaleza',
    'route-views.gixa',
]

def parse_path(path_str, not_collapse_prepending_asns=False):
    if not_collapse_prepending_asns:
        return path_str

    path = path_str.split(' ')

    path_clean = [path[0]]
    for u in path[1:]:
        if u != path_clean[-1]:
            path_clean.append(u)

    path_clean_str = ' '.join(path_clean)

    return path_clean_str


def main(args):

    start_date_time = dt.datetime.combine(args.start_date, args.time)

    days_collectors = it.product(range(args.ndays), COLLECTORS)
    tqdm_total = args.ndays*len(COLLECTORS)

    unique_paths = set()

    for nday, collector in tqdm(days_collectors, desc='Days and collectors', total=tqdm_total):
        date_time = start_date_time + dt.timedelta(days=nday)
        date_time_str = date_time.strftime(r'%Y-%m-%d %H:%M:%S')

        print(f'Collecting data from {collector} at {date_time_str}', file=sys.stderr)

        stream = pybgpstream.BGPStream(
            from_time=date_time_str, until_time=date_time_str,
            collectors=[collector],
            record_type="ribs",
        )

        n_paths_for_pair = 0

        for elem in stream:
            path_str = elem.fields["as-path"]
            path_clean_str = parse_path(path_str, args.not_collapse_prepending_asns)

            if args.verbose and path_clean_str != path_str:
                print(f'Cleaned {path_str} to {path_clean_str}', file=sys.stderr)

            if not args.not_only_unique_paths:
                if path_clean_str in unique_paths:
                    if args.verbose:
                        print(f'Found repeated path {path_clean_str}', file=sys.stderr)

                    continue

                unique_paths.add(path_clean_str)

            elem_time = dt.datetime.fromtimestamp(elem.time)
            if args.path_only:
                print(f'{path_clean_str}')
            else:
                print(f'{elem_time}|{elem.collector}|{path_clean_str}')

            n_paths_for_pair += 1

        print(f'Added {n_paths_for_pair} paths', file=sys.stderr)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('start_date',
                        type=lambda s: dt.datetime.strptime(s, '%d/%m/%Y').date(),
                        help='day when data will start being collected (dd/mm/yyy)')
    parser.add_argument('time',
                        type=lambda s: dt.datetime.strptime(s, '%H:%M:%S').time(),
                        help='time of snapshots (hh:mm:ss)'),
    parser.add_argument('ndays', type=int, help='total number of days when the collection is done')
    parser.add_argument('--path-only', action='store_true',
                        help='print only the path for each record')
    parser.add_argument('--not-only-unique-paths', action='store_true',
                        help='output repeating paths')
    parser.add_argument('--not-collapse-prepending-asns', action='store_true',
                        help='ouput prepending asns in paths (AS1 AS2 AS2 AS3)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output to stderr')
    args = parser.parse_args()

    main(args)

