#!python3

import argparse
import ast
import gensim
import os
import pandas as pd
import sys


from gensim.models import KeyedVectors
from tensorflow import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences


import vf_with_problink_data as vf


def encode_and_pad_paths_from_file(b2v, gt_summary_df, filepath):

    # Have to remove the directory and the appended .dat added to the file
    file_summary = gt_summary_df.loc[os.path.split(filepath)[1]]
    hj_asns = set(file_summary.hj_as)
    victim_asn = file_summary.vt_as

    try:
        data_df = pd.read_csv(filepath, header=None, converters={0: lambda x: x.split()})
    except KeyError:
        print(f'File not described in summary {filepath}', file=sys.stderr)
        return [], 0

    paths_before_padding = []
    errors = 0
    for path in data_df[0]:
        p = []
        if len([u for u in path if u in hj_asns]) == 0:
            continue

        try:
            for asn in path:
                p.append(b2v.wv.key_to_index[asn] + 1)
            paths_before_padding.append(p)
        except KeyError:
            print(f'Cannot find asn {asn} (relative to path {path}) in the bgp2vec asns', file=sys.stderr)
            errors += 1
            continue

    return pad_sequences(paths_before_padding, maxlen=13, padding="post", truncating="pre",
                         value=0), paths_before_padding, errors


def main(args):

    asr = vf.ASRelationshipGraph()

    gt_summary_df = pd.read_csv(
        args.gt_summary,
        converters={'hj_as': lambda x: ast.literal_eval(x),
                    'vt_as': lambda x: str(x)}
    )
    gt_summary_df.set_index('title', inplace=True)

    model = keras.models.load_model(args.model)
    b2v = KeyedVectors.load('bgp2vec/unique-jan-march2018-20h.dat.b2v')

    print('file,red_rnn,red_vf,total')

    for f in os.listdir(args.gt_dir):
        filepath = os.path.join(args.gt_dir, f)
        paths, paths_before_padding, errors = encode_and_pad_paths_from_file(b2v, gt_summary_df, filepath)
        # print(paths, errors/(len(paths) + errors))

        if len(paths) == 0:
            # print(f'{f} no target path found for this')
            print(f'{f},0,0,0')

            continue

        preds = model.predict_classes(paths)
        suspect = list(preds).count(1)
        # print(f'{f}: {suspect}/{len(preds)} = {suspect/len(preds)} bad paths')

        vf_bad = [asr.is_vf(p) for p in paths_before_padding].count(False)

        print(f'{f},{suspect},{vf_bad},{len(paths)}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('bgp2vec', help='path to the bgp2vec model')
    parser.add_argument('model', help='path to the trained model')
    parser.add_argument('gt_dir', help='path to the ground-truth directory')
    parser.add_argument('gt_summary', help='path to the ground-truth summary file')
    args = parser.parse_args()

    main(args)
