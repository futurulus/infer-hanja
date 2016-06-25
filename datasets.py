from collections import namedtuple
import numpy as np
from hanja import hanja as libhanja

from stanza.research import config
from stanza.research.instance import Instance
from stanza.research.rng import get_rng

import gold_pron
from utils import uopen


rng = get_rng()

parser = config.get_options_parser()
parser.add_argument('--num_distractors', type=int, default=4,
                    help='The number of random colors to include in addition to the true '
                         'color in generating reference game instances. Ignored if not '
                         'using one of the `ref_` data sources.')


SPLITS = None


def kokore_splits():
    global SPLITS

    if SPLITS is None:
        with uopen(gold_pron.KOKORE, 'r') as infile:
            all_docs = list(gold_pron.all_documents(infile))

        lens = np.array([len(d[1]) for d in all_docs])
        short_size = len(all_docs) / 3
        indices = np.argpartition(lens, kth=short_size)
        indices_short, indices_midlong = indices[:short_size], indices[short_size:]

        lens_midlong = lens[indices_midlong]
        mid_size = len(lens_midlong) / 2
        double_indices = np.argpartition(lens_midlong, kth=mid_size)
        indices_mid, indices_long = (indices_midlong[double_indices[:mid_size]],
                                     indices_midlong[double_indices[mid_size:]])

        (indices_train, indices_dev, indices_test) = split_indices(indices_short,
                                                                   indices_mid,
                                                                   indices_long)

        for name, inds in [('train', indices_train), ('dev', indices_dev), ('test', indices_test)]:
            titles = [all_docs[i][0] for i in inds]
            with config.open('titles.%s.jsons' % name, 'w') as outfile:
                for title in titles:
                    outfile.write(title.encode('utf-8') + '\n')

        SPLITS = [list(docs_to_instances([all_docs[i] for i in inds]))
                  for inds in (indices_train, indices_dev, indices_test)]

    return SPLITS


def split_indices(*inds):
    train, dev, test = [], [], []
    for ind in inds:
        ind = np.sort(ind)
        split_size = len(ind) / 3
        train.append(ind[:split_size])
        dev.append(ind[split_size:split_size * 2])
        test.append(ind[split_size * 2:])
    return [np.sort(np.hstack(s)) for s in (train, dev, test)]


def docs_to_instances(docs):
    for title, document in docs:
        for i, sentence in enumerate(gold_pron.sentence_split(document)):
            hangul = libhanja.translate(sentence, 'substitution')
            yield Instance(hangul, sentence, source='%s:%s' % (title, i))


def kokore_traintune():
    insts = list(kokore_splits()[0])
    rng.shuffle(insts)
    return insts


def kokore_dev():
    insts = list(kokore_splits()[1])
    return insts


def kokore_test():
    insts = list(kokore_splits()[2])
    return insts


DataSource = namedtuple('DataSource', ['train_data', 'test_data'])

SOURCES = {
    'dev': DataSource(kokore_traintune, kokore_dev),
    'test': DataSource(kokore_traintune, kokore_test),
}
