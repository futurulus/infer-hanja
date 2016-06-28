import glob
import json
import Levenshtein as lev
import numpy as np
import os
import warnings
from collections import namedtuple

from stanza.research import config

from libhanja_eval import print_visualization


parser = config.get_options_parser()
parser.add_argument('--max_examples', type=int, default=100,
                    help='The maximum number of examples to display in error analysis.')
parser.add_argument('--html', type=config.boolean, default=False,
                    help='If true, output errors in HTML.')

Output = namedtuple('Output', 'config,results,data,scores,predictions')


def print_error_analysis():
    options = config.options(read=True)
    output = get_output(options.run_dir, 'eval')
    errors = [(inst['input'], pred, inst['output'])
              for inst, pred in zip(output.data, output.predictions)
              if inst['output'] != pred]
    if 0 < options.max_examples < len(errors):
        indices = np.random.choice(np.arange(len(errors)), size=options.max_examples, replace=False)
    else:
        indices = range(len(errors))

    if options.html:
        print('<!DOCTYPE html>')
        print('<html><head><title>Error analysis</title><meta charset="utf-8" /></head><body>')
    for i in indices:
        inp, pred, gold = [unicode(s).strip() for s in errors[i]]
        editops = lev.editops(gold, pred)
        print_visualization(inp, pred, gold, editops, html=options.html)
    if options.html:
        print('</body></html>')


def get_output(run_dir, split):
    config_dict = load_dict(os.path.join(run_dir, 'config.json'))

    results = {}
    for filename in glob.glob(os.path.join(run_dir, 'results.*.json')):
        results.update(load_dict(filename))

    data = load_dataset(os.path.join(run_dir, 'data.%s.jsons' % split))
    scores = load_dataset(os.path.join(run_dir, 'scores.%s.jsons' % split))
    predictions = load_dataset(os.path.join(run_dir, 'predictions.%s.jsons' % split))
    return Output(config_dict, results, data, scores, predictions)


def load_dict(filename):
    try:
        with open(filename) as infile:
            return json.load(infile)
    except IOError, e:
        warnings.warn(str(e))
        return {'error.message.value': str(e)}


def load_dataset(filename, transform_func=(lambda x: x)):
    try:
        dataset = []
        with open(filename) as infile:
            for line in infile:
                js = json.loads(line.strip())
                dataset.append(transform_func(js))
        return dataset
    except IOError, e:
        warnings.warn(str(e))
        return [{'error': str(e)}]


if __name__ == '__main__':
    print_error_analysis()
