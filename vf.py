#!python3
'''
This file contains the implementation of 3 algorithms for classifying the relationships between
two Autonomous Systems (ASes), as described in

Lixin Gao. 2001. On inferring autonomous system relationships in the internet. IEEE/ACM Trans.
Netw. 9, 6 (December 2001), 733–745. DOI:https://doi.org/10.1109/90.974527
'''

import argparse
import numpy as np
import sys
from tqdm import tqdm


from collections import defaultdict


SIBLING_TO_SIBLING = 'S2S'
PROVIDER_TO_CUSTOMER = 'P2C'
CUSTOMER_TO_PROVIDER = 'C2P'
PEER_TO_PEER = 'P2P'
UNDEFINED = 'UNDEF'

PARAMETER_R = 60

class GaoGraphBasic():

    def __init__(self, paths):
        self.paths = paths
        self.edges = self.get_classified_edges()
        self.stats = self.compute_stats()
        self.vf_class = self.classify_paths()

    def get_classified_edges(self):
        neighbors = self._phase1()
        transit = self._phase2(neighbors)
        edges = self._phase3(transit)

        return edges

    def is_valley_free(self, path):

        edge_sequence = [self.edges[(path[i], path[i + 1])] for i, _ in enumerate(path[:-1])]
        try:
            p2c_index = edge_sequence.index(PROVIDER_TO_CUSTOMER)
            if not all([e != CUSTOMER_TO_PROVIDER for e in edge_sequence[p2c_index + 1:]]):
                return False
        except ValueError:
            pass

        try:
            p2p_index = edge_sequence.index(PEER_TO_PEER)
            if not all([e != PEER_TO_PEER and e != CUSTOMER_TO_PROVIDER
                        for e in edge_sequence[p2p_index + 1:]]):
                return False
        except ValueError:
            pass

        return True

    def classify_paths(self):
        paths_vf_class = []
        for path in tqdm(self.paths, desc="Classifying paths"):
            paths_vf_class.append(self.is_valley_free(path))

        nfalse = paths_vf_class.count(False)
        print(f'Not vf: {nfalse}', file=sys.stderr)
        return paths_vf_class

    def compute_stats(self):
        stats = {}
        for tor in tqdm(self.edges.values(), desc='Computing stats'):
            if tor not in stats:
                stats[tor] = 0
            stats[tor] += 1
        return stats

    def _phase1(self):
        neighbors = defaultdict(set)

        for path in tqdm(self.paths, desc="Phase 1"):
            for i, u in enumerate(path[:-1]):
                u_next = path[i + 1]

                neighbors[u].add(u_next)
                neighbors[u_next].add(u)

        return neighbors

    def _phase2(self, neighbors):
        transit = defaultdict(bool)

        def put_transit(u1, u2):
            transit[(u1, u2)] = True

        for path in tqdm(self.paths, desc="Phase 2"):
            j_max_degree = np.argmax([len(neighbors[u]) for u in path])

            for i in range(j_max_degree):
                put_transit(path[i], path[i + 1])

            for i in range(j_max_degree, len(path) - 1):
                put_transit(path[i + 1], path[i])

        return transit

    def _phase3(self, transit):
        edges = {}

        def is_transit(u1, u2):
            return transit[(u1, u2)]

        for path in tqdm(self.paths, desc="Phase 3"):
            for i, u in enumerate(path[:-1]):
                u_next = path[i + 1]

                if is_transit(u, u_next) and is_transit(u_next, u):
                    edges[(u, u_next)] = SIBLING_TO_SIBLING

                elif is_transit(u_next, u):
                    edges[(u, u_next)] = PROVIDER_TO_CUSTOMER

                elif is_transit(u, u_next):
                    edges[(u, u_next)] = CUSTOMER_TO_PROVIDER

        return edges

    def print_stats(self):
        total = sum(self.stats.values())
        for tor, count in self.stats.items():
            ratio = count/total
            print(f'{tor}: {count}/{total} = {ratio}', file=sys.stderr)


class GaoGraphRefined(GaoGraphBasic):

    def _phase2(self, neighbors):
        transit = defaultdict(int)

        def put_transit(u1, u2):
            transit[(u1, u2)] += 1

        for path in tqdm(self.paths, desc="Phase 2"):
            j_max_degree = np.argmax([len(neighbors[u]) for u in path])

            for i in range(j_max_degree):
                put_transit(path[i], path[i + 1])

            for i in range(j_max_degree, len(path) - 1):
                put_transit(path[i + 1], path[i])

        return transit

    def _phase3(self, transit, L=1):
        edges = {}

        def get_transit(u1, u2):
            return transit[(u1, u2)]

        for path in tqdm(self.paths, desc="Phase 3"):
            for i, u in enumerate(path[:-1]):
                u_next = path[i + 1]

                fwd_t = get_transit(u, u_next)
                bwd_t = get_transit(u_next, u)

                if ((fwd_t > L and bwd_t > L) or (0 < fwd_t <= L and 0 < bwd_t <= L)):
                    edges[(u, u_next)] = SIBLING_TO_SIBLING

                elif bwd_t > L or fwd_t == 0:
                    edges[(u, u_next)] = PROVIDER_TO_CUSTOMER

                elif fwd_t > L or bwd_t == 0:
                    edges[(u, u_next)] = CUSTOMER_TO_PROVIDER

        return edges


class GaoGraphHeuristic(GaoGraphRefined):

    def get_classified_edges(self):
        neighbors = self._phase1()
        transit = self._phase2(neighbors)
        edges = self._phase3(transit)
        not_peering = self._heuristic_phase2(neighbors, edges)
        # Adds P2P relationships to edges
        self._heuristic_phase3_writing_over_edges(neighbors, not_peering, edges)

        return edges

    def _heuristic_phase2(self, neighbors, edges):
        not_peering = defaultdict(bool)

        def put_not_peering(u1, u2):
            not_peering[(u1, u2)] = True

        for path in tqdm(self.paths, desc="Phase 4.1"):
            j_max_degree = np.argmax([len(neighbors[u]) for u in path])

            for i in range(j_max_degree - 1):
                put_not_peering(path[i], path[i + 1])

            for i in range(j_max_degree + 1, len(path) - 1):
                put_not_peering(path[i], path[i + 1])

            if j_max_degree == 0 or j_max_degree == len(path) - 1:
                continue

            uj = path[j_max_degree]

            uj_prev = path[j_max_degree - 1]
            edge_uj_prev = edges[(uj_prev, uj)]

            uj_next = path[j_max_degree + 1]
            edge_uj_next = edges[(uj, uj_next)]


            if edge_uj_prev != SIBLING_TO_SIBLING and edge_uj_next != SIBLING_TO_SIBLING:
                if len(neighbors[uj_prev]) > len(neighbors[uj_next]):
                    put_not_peering(uj, uj_next)
                else:
                    put_not_peering(uj_prev, uj)

        return not_peering

    def _heuristic_phase3_writing_over_edges(self, neighbors, not_peering, edges, R=PARAMETER_R):
        def deg(u):
            return len(neighbors[u])

        for path in tqdm(self.paths, desc="Phase 4.2"):
            for i, u in enumerate(path[:-1]):
                u_next = path[i + 1]

                if ((not not_peering[(u, u_next)]) and (not not_peering[(u_next, u)]) and
                    (1/R < deg(u)/deg(u_next) < R)):

                    edges[(u, u_next)] = PEER_TO_PEER

        return edges


def get_paths_from_file(filepath=None):
    paths = []

    f = sys.stdin
    if filepath:
        f = open(filepath)

    for line in f:
        l = line.rstrip()
        path = l.split(' ')

        if len(path) > 2:
            paths.append(path)

    return paths


def classify_edges_from_stdin():
    print('Parsing paths...', file=sys.stderr)
    paths = get_paths_from_file()
    gh = GaoGraphHeuristic(paths)
    for p, c in zip(gh.paths, gh.vf_class):
        color = 'GREEN'
        if not c:
            color = 'RED'
        print(' '.join(p) + ',' + color)
    gh.print_stats()
    return gh


def main():
    classify_edges_from_stdin()


if __name__ == '__main__':
    main()
