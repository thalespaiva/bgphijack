# bgphijack


This project contains the implementation of the LSTM-based classification of BGP hijacking paths
as described in

    Tal Shapira and Yuval Shavitt. A Deep Learning Approach for IP Hijack Detection Based on ASN
    Embedding. Proceedings of the Workshop on Network Meets AI & ML. 2020.

The paper can be found in the author's archive
[here](http://www.eng.tau.ac.il/~shavitt/pub/NetAI2020.pdf).

# Structure

* `bgp2vec.py`
    Implements of word2vec using set of paths as a corpus.
* `daily_collector.py`
    Program to download RIBs data from RouteViews.
* `validation_gt.py`
    Runs the validation process over known IP Hijacking events for the trained Neural Network.
* `vf.py`
    Implements Lixin Gao procedure for classifying Valley-Free paths.
* `vf_with_problink_data.py`
    Implements VF classification using ProbLink's inferred relationship between ASes.
* `lstm_hijack_classifier.py`
    The LSTM model using BGP2Vec as the first embedding layer.

# Usage

In this section, we describe how the code can be used to learn to classify possible hijacking
events.

First let us clone the repository
```
$ git clone https://github.com/thalespaiva/bgphijack.git
```

Now we install our environment and the project's dependencies using Pipenv.
```
$ pipenv shell
$ pipenv install
```

We are ready to use the code :^)

## Data collection

The basis of the classification is the set of paths downloaded from
[RouteViews](http://www.routeviews.org/). We can collect the paths from a set
of collectors using `daily_collector.py` as follows

```
$ mkdir paths
$ ./daily_collector.py --path-only 01/01/2020 20:00:00 2 > paths/2days_2020.paths
```

This command will collect data corresponding to the snapshots of RIBs files at 20:00:00 of each day
from 01/01/2020 to 02/01/2020. Notice that it may take around 5-10 minutes to download the whole
file. If you don't set `--path-only` it will collect additional information, you won't be able to feed it directly to the next step.

The expected format of the file generated is:
```
$ head -n 5 paths/2days_2020.paths
23367
55222
202365 13335
38001 13335
39120 13335
3402 174 13335
39351 13335
29479 13335
6939 13335
3561 209 3356 13335
```

## Labeling paths

Now we can proceed to classify these paths using the Valley-Free method. To classify these paths
into `GREEN` and `RED`, corresponding to VF and non-VF paths, we can use ProbLink data on
AS relationships. The file `vf_with_problink_data.py` implements this functionality, and you
can run it as:

```
$ mkdir classified
$ cat paths/2days_2020.paths | ./vf_with_problink_data.py external-data/problink/relat.txt > classified/2days_2020.vf 2> /dev/null
```

The expected output is
```
$ head classified/2days_2020.vf
23367,GREEN
55222,GREEN
202365 13335,GREEN
38001 13335,GREEN
39120 13335,GREEN
3402 174 13335,GREEN
39351 13335,GREEN
29479 13335,GREEN
6939 13335,GREEN
3561 209 3356 13335,GREEN
```

Let us see the number of paths labeled as `GREEN` and `RED`:
```
$ grep GREEN classified/2days_2020.vf | wc -l
2570999
$ grep RED classified/2days_2020.vf | wc -l
126533
```

## BGP2Vec

Notice that this step and the VF classification are independent.

We can now run the BGP2Vec encoding over the steps we downloaded in the
first step running the following:
```
$ mkdir bgp2vec
$ time ./bgp2vec.py paths/2days_2020.paths bgp2vec/2days_2020.b2v
./bgp2vec.py paths/2days_2020.paths bgp2vec/2days_2020.b2v
```

This will save the BGP2Vec model in `bgp2vec/2days_2020.b2v`, so that we
can later use it as the embedding layer for our Neural Network.

To see the closest neighbors to AS3356 (Google) and AS15169 (Level3),
we can run the following in ipython:
```
$ ipython
Python 3.8.9 (default, Apr 27 2021, 17:55:19)
Type 'copyright', 'credits' or 'license' for more information
IPython 7.23.1 -- An enhanced Interactive Python. Type '?' for help.
In [1]: import gensim
   ...: from gensim.models import KeyedVectors
   ...: b2v = KeyedVectors.load('bgp2vec/2days_2020.b2v')

In [2]: import bgp2vec
   ...: dfs = bgp2vec.reproduce_table1_from_bgp2vec(b2v, 'external-data/cidr-report/asn.dat')
```

This will return the following two dataframes:

`In [7]: print(dfs[0].to_markdown())`
|    |   Neighbor |   ASN | Owner                                           |   Cosine Sim. |
|---:|-----------:|------:|:------------------------------------------------|--------------:|
|  0 |          0 |  3356 | LEVEL3, US                                      |      1        |
|  1 |          1 |  1299 | TELIANET Telia Carrier, SE                      |      0.963699 |
|  2 |          2 |   174 | COGENT-174, US                                  |      0.957699 |
|  3 |          3 |  3257 | GTT-BACKBONE GTT, US                            |      0.95724  |
|  4 |          4 |  2914 | NTT-COMMUNICATIONS-2914, US                     |      0.942149 |
|  5 |          5 |  3549 | LVLT-3549, US                                   |      0.915178 |
|  6 |          6 | 37468 | ANGOLA-CABLES, AO                               |      0.890896 |
|  7 |          7 |  6461 | ZAYO-6461, US                                   |      0.890357 |
|  8 |          8 |  8220 | COLT COLT Technology Services Group Limited, GB |      0.888785 |
|  9 |          9 | 12956 | TELEFONICA TELXIUS, ES                          |      0.884327 |

`In [8]: print(dfs[1].to_markdown())`
|    |   Neighbor |    ASN | Owner                                                      |   Cosine Sim. |
|---:|-----------:|-------:|:-----------------------------------------------------------|--------------:|
|  0 |          0 |  15169 | GOOGLE, US                                                 |      1        |
|  1 |          1 | 138132 | FASTEL-NAP-AS-ID PT. FASTEL SARANA INDONESIA, ID           |      0.628328 |
|  2 |          2 |  17893 | PALAU-AS-AP Palau National Communications Corp., PW        |      0.62502  |
|  3 |          3 |  36385 | GOOGLE-IT, US                                              |      0.620861 |
|  4 |          4 |   6660 | CWASIA, GB                                                 |      0.616502 |
|  5 |          5 | 136237 | SSCTC-AS-AP Shuangyu Communication Technology co.,Ltd., CN |      0.614795 |
|  6 |          6 |  29386 | EXT-PDN-STE-AS, SY                                         |      0.599123 |
|  7 |          7 | 202818 | LEVEL3COMMUNICATIONS, GB                                   |      0.580802 |
|  8 |          8 | 205988 | PLAYCO-AS, AE                                              |      0.579128 |
|  9 |          9 |   6400 | Compania Dominicana de Telefonos S. A., DO                 |      0.575691 |


## Training the LSTM

We are ready to train the LSTM network for IP Hijack detection. You can run the following command
to train the model and save it to `lstm/2days_2020.lstm`.
Notice that we are omitting tensorflow logs from the output.
```
$ mkdir lstm
$ ./lstm_hijack_classifier.py bgp2vec/2days_2020.b2v classified/2days_2020.vf lstm/2days_2020.lstm
Model: "sequential"
_________________________________________________________________
Layer (type)                 Output Shape              Param #
=================================================================
BGP2Vec (Embedding)          (None, 13, 32)            2016192
_________________________________________________________________
conv1d (Conv1D)              (None, 13, 32)            3104
_________________________________________________________________
max_pooling1d (MaxPooling1D) (None, 6, 32)             0
_________________________________________________________________
lstm (LSTM)                  (None, 100)               53200
_________________________________________________________________
dense (Dense)                (None, 1)                 101
=================================================================
Total params: 2,072,597
Trainable params: 56,405
Non-trainable params: 2,016,192
_________________________________________________________________
Epoch 1/10
33720/33720 [==============================] - 143s 4ms/step - loss: 0.0968 - accuracy: 0.9746 - val_loss: 0.0510 - val_accuracy: 0.9867
Epoch 2/10
33720/33720 [==============================] - 141s 4ms/step - loss: 0.0492 - accuracy: 0.9867 - val_loss: 0.0408 - val_accuracy: 0.9889
Epoch 3/10
33720/33720 [==============================] - 138s 4ms/step - loss: 0.0407 - accuracy: 0.9889 - val_loss: 0.0353 - val_accuracy: 0.9901
Epoch 4/10
33720/33720 [==============================] - 137s 4ms/step - loss: 0.0348 - accuracy: 0.9903 - val_loss: 0.0316 - val_accuracy: 0.9909
Epoch 5/10
33720/33720 [==============================] - 138s 4ms/step - loss: 0.0305 - accuracy: 0.9913 - val_loss: 0.0300 - val_accuracy: 0.9913
Epoch 6/10
33720/33720 [==============================] - 137s 4ms/step - loss: 0.0280 - accuracy: 0.9920 - val_loss: 0.0259 - val_accuracy: 0.9926
Epoch 7/10
33720/33720 [==============================] - 137s 4ms/step - loss: 0.0252 - accuracy: 0.9927 - val_loss: 0.0280 - val_accuracy: 0.9916
Epoch 8/10
33720/33720 [==============================] - 137s 4ms/step - loss: 0.0234 - accuracy: 0.9932 - val_loss: 0.0221 - val_accuracy: 0.9936
Epoch 9/10
33720/33720 [==============================] - 137s 4ms/step - loss: 0.0219 - accuracy: 0.9935 - val_loss: 0.0217 - val_accuracy: 0.9936
Epoch 10/10
33720/33720 [==============================] - 138s 4ms/step - loss: 0.0206 - accuracy: 0.9940 - val_loss: 0.0205 - val_accuracy: 0.9940
Confusion matrix:
[[0.99781268 0.00218732]
 [0.0835253  0.9164747 ]]
...
```

## Validating the results over ground-truth data

To validate the model against hijack events documented by the project
[bgp-hijacks-classifier](https://github.com/grace71/bgp-hijacks-classifier), we can run
the following commands.
```
$ mkdir validation
$ ./validation_gt.py bgp2vec/2days_2020.b2v lstm/2days_2020.lstm external-data/bgp-hijacks-classifier/paths external-data/bgp-hijacks-classifier/results_news_updated_2.csv > validation/2days_2020.gt
```

This will create a file in the following format:
```
$ head validation/2days_2020.gt
file,red_rnn,total
prepend_155176.pickle,22,53
h3s_1.pickle,17,251
carlson_1.pickle,56,293
bitcanal_4.pickle,0,0
typo_pfx_123862.pickle,174,712
typo_pfx_125850.pickle,31,293
sprint_1.pickle,9,122
typo_1.pickle,0,0
torg_2.pickle,0,0
```

Each line corresponds to an event. The columns corresponds to:
* `file` pickle containing paths associated with an identified hijack event
* `red_rnn` paths classified as red from the `total` defined below
* `total` number of paths found corresponding to the hijacked prefix which contain only
    ASNs that are known by the BGP2Vec model.

It is questionable whether we should exclude paths outside the trained BGP2Vec model in the
analysis and we encourage other researchers to come with better solutions to analyze this
dataset using these models.

The file just generated can be used almost directly for plotting as we describe next.
```
$ ipython
Python 3.8.9 (default, Apr 27 2021, 17:55:19)
Type 'copyright', 'credits' or 'license' for more information
IPython 7.23.1 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import pandas as pd
   ...: import matplotlib.pyplot as plt

In [2]: df = pd.read_csv('validation/2days_2020.gt')

In [3]: df['Event'] = df.file.map(lambda x: str(x)[:-7])

In [4]: df['Fraction of red paths'] = df.red_rnn/df.total

In [5]: df
Out[5]:
                      file  red_rnn  total            Event  Fraction of red paths
0    prepend_155176.pickle       22     53   prepend_155176               0.415094
1             h3s_1.pickle       17    251            h3s_1               0.067729
2         carlson_1.pickle       56    293        carlson_1               0.191126
3        bitcanal_4.pickle        0      0       bitcanal_4                    NaN
4   typo_pfx_123862.pickle      174    712  typo_pfx_123862               0.244382
..                     ...      ...    ...              ...                    ...
65  typo_asn_152909.pickle      238    770  typo_asn_152909               0.309091
66   prepend_120619.pickle        0     22   prepend_120619               0.000000
67         amazon_1.pickle        4     40         amazon_1               0.100000
68    backconnect_1.pickle        0      0    backconnect_1                    NaN
69  typo_pfx_121630.pickle       67    375  typo_pfx_121630               0.178667

[70 rows x 5 columns]

In [6]: %matplotlib
Using matplotlib backend: TkAgg

In [7]: df[df.total > 0].sort_values('Fraction of red paths', ascending=False)[:20].plot(x='Event', y='Fraction of red paths', kind='bar')
Out[8]: <AxesSubplot:xlabel='Event'>

In [8]: plt.tight_layout()

In [9]: mkdir figs

In [10]: plt.savefig('figs/hijack-20-events-rnn.png', dpi=300)
```

This will generate the following figure, with the 20 events that have the most paths classified
as `RED`.

![Events with most paths classified as hijacks](/figs/hijack-20-events-rnn.png)


# Use of data from other sources

Part of our code require additional information such as AS relationships, AS information and
Hijack events for validation. To help users trying to run our code, we added to this repository
data from other projects, which are detailed below.

# [bgp-hijacks-classifier](https://github.com/grace71/bgp-hijacks-classifier)

This project documents BGP Hijacking events and it is used for validation of the trained
model. We parsed the pickles of their `collections` using our Python2 script
`bgp-hijacks-classifier/get_ground_truth_paths.py`, extracting only the paths
without AS prepending to`bgp-hijacks-classifier/paths`.

# [CIDR](https://www.cidr-report.org/as2.0/)

CIDR keeps an update list of ASNs and their ownership info. This is used only by the BGP2Vec
code when plotting the table of closest neighbors.


# [ProbLink](https://github.com/YuchenJin/ProbLink)

ProbLink is tool for inference of AS relationships. Knowledge of AS relationships is important
for classification of Valley-Free paths, which is one definition for non-suspicious paths.

In `ProbLink`, you will find ProbLink's inferred relationships for 01/01/2019. This file
is decompress to facilitate its usage directly from cloners of this repository. The file
corresponds to [this compressed file from the ProbLink project](https://yuchenjin.github.io/problink-as-relationships/20190101.tar.gz)

# License

MIT

# Authors

* Thales Paiva
* Yaissa Siqueira
