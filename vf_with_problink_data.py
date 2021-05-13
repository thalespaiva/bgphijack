#!python3

import os
import sys


AS_RELATIONSHIP_FILEPATH = os.path.join('asn_data', 'relat.txt')

RELAT = {
    -1: 'P2C',
    0: 'P2P',
    1: 'S2S'
}


class ASRelationshipGraph():

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = {}

        f = open(AS_RELATIONSHIP_FILEPATH)
        for line in f:
            l = line.split('|')
            as1, as2, relat = int(l[0]), int(l[1]), int(l[2])

            graph[(as1, as2)] = RELAT[relat]

        return graph

    def get_relationship(self, as1, as2):

        if (as1, as2) in self.graph:
            return self.graph[(as1, as2)]

        elif (as2, as1) in self.graph:
            rel = self.graph[(as2, as1)]
            if rel == 'P2C':
                return 'C2P'
            return rel

        return None


    def is_vf(self, path):
        edges = [self.get_relationship(path[i], path[i + 1]) for i, _ in enumerate(path[:-1])]

        try:
            p2c_index = edges.index('P2C')
            if not all([e != 'C2P' for e in edges[p2c_index + 1:]]):
                # print(edges)
                return False
        except ValueError:
            pass

        try:
            p2p_index = edges.index('P2P')
            if not all([e != 'P2P' and e != 'C2P'
                        for e in edges[p2p_index + 1:]]):
                # print(edges)
                return False
        except ValueError:
            pass

        return True


def main():

    asr = ASRelationshipGraph()

    not_vf = 0
    for i, l in enumerate(sys.stdin):
        # path_str = l.split('|')[2].rstrip()
        path_str = l.rstrip()
        try:
            path = list(map(int, path_str.split(' ')))
            vf = asr.is_vf(path)

            if vf:
                color = 'GREEN'
            else:
                color = 'RED'
                not_vf += 1

            print(f'{path_str},{color}')

        except ValueError:
            print(f'Error parsing line {i} path: {path_str}', file=sys.stderr)

        print(f'Not VF: {not_vf}/{i + 1} = {not_vf/(i + 1)}', file=sys.stderr)


if __name__ == "__main__":
    main()
