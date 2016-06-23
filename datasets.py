from collections import namedtuple

from stanza.research import config
from stanza.research.instance import Instance
from stanza.research.rng import get_rng


rng = get_rng()

parser = config.get_options_parser()
parser.add_argument('--num_distractors', type=int, default=4,
                    help='The number of random colors to include in addition to the true '
                         'color in generating reference game instances. Ignored if not '
                         'using one of the `ref_` data sources.')


def kokore_traintune():
    insts = []  # TODO
    rng.shuffle(insts)
    return insts


def kokore_dev():
    insts = []  # TODO
    return insts


def kokore_test():
    insts = []  # TODO
    return insts


DataSource = namedtuple('DataSource', ['train_data', 'test_data'])

SOURCES = {
    'dev': DataSource(kokore_traintune, kokore_dev),
    'test': DataSource(kokore_traintune, kokore_test),
}
