#!python3

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


def get_neighbors_table(bgp2vec, target_asn: str):
    target_asn_vector = bgp2vec.wv.get_vector(target_asn)

    asn_df = pd.read_csv(ASN_DATA_FILEPATH, delimiter="<SEP>", index_col='ASN', engine='python')

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


def reproduce_table1_from_bgp2vec(bgp2vec):
    LEVEL3_ASN = '3356'
    GOOGLE_ASN = '15169'

    df_level3 = get_neighbors_table(bgp2vec, LEVEL3_ASN)
    df_google = get_neighbors_table(bgp2vec, GOOGLE_ASN)

    return df_level3, df_google


def reproduce_all(aspaths_filepath: str):
    bgp2vec = get_bgp2vec(aspaths_filepath)
    df_level3, df_google = reproduce_table1_from_bgp2vec(bgp2vec)

    print(df_level3)
    print(df_google)