# External Data

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



