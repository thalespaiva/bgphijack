#!/usr/bin/env python3

import argparse
import gensim
import pandas as pd
import os

PARAMETER_NEGATIVE_SAMPLES = 5
PARAMETER_SEED = 42
PARAMETER_VECTOR_SIZE = 32
PARAMETER_WINDOW = 2
PARAMETER_NPATHS = 3600000

NWORKERS_WORD2VEC = 6

ASN_DATA_FILEPATH = os.path.join('asn_data', 'asn.dat')


def get_bgp2vec(aspaths_filepath: str):
    corpus = gensim.models.word2vec.LineSentence(aspaths_filepath, limit=PARAMETER_NPATHS)
    return gensim.models.Word2Vec(sentences=corpus,
                                  window=PARAMETER_WINDOW,
                                  negative=PARAMETER_NEGATIVE_SAMPLES,
                                  seed=PARAMETER_SEED,
                                  hs=1,
                                  min_count=1,
                                  workers=NWORKERS_WORD2VEC,
                                  vector_size=PARAMETER_VECTOR_SIZE)


def get_neighbors_table(bgp2vec, target_asn: str, asn_data_filepath: str):
    target_asn_vector = bgp2vec.wv.get_vector(target_asn)

    asn_df = pd.read_csv(asn_data_filepath, delimiter="<SEP>", index_col='ASN', engine='python')

    table = {
        'Neighbor': [],
        'ASN': [],
        'Owner': [],
        'Cosine Sim.': [],
    }

    neighbors = bgp2vec.wv.most_similar([target_asn_vector])
    for i, (asn, sim) in enumerate(neighbors):
        table['Neighbor'].append(i)
        table['ASN'].append(asn)
        table['Owner'].append(asn_df.loc[int(asn)].AS)
        table['Cosine Sim.'].append(sim)

    return pd.DataFrame.from_dict(table)


def reproduce_table1_from_bgp2vec(bgp2vec, asn_data_filepath):
    LEVEL3_ASN = '3356'
    GOOGLE_ASN = '15169'

    df_level3 = get_neighbors_table(bgp2vec, LEVEL3_ASN, asn_data_filepath)
    df_google = get_neighbors_table(bgp2vec, GOOGLE_ASN, asn_data_filepath)

    return df_level3, df_google


def reproduce_all(aspaths_filepath: str, asn_data_filepath):
    bgp2vec = get_bgp2vec(aspaths_filepath)
    df_level3, df_google = reproduce_table1_from_bgp2vec(bgp2vec, asn_data_filepath)

    print(df_level3)
    print(df_google)


def main(args):
    b2v = get_bgp2vec(args.as_paths)
    b2v.save(args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('as_paths', help='path to file containing as_paths')
    parser.add_argument('output', help='path where the bgp2vec model will be saved')
    args = parser.parse_args()

    main(args)
