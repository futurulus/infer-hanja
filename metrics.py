import Levenshtein as lev
import numpy as np


def cer_tuples(golds, predictions):
    tuples = []
    for gold, pred in zip(golds, predictions):
        gold = gold.strip()
        pred = pred.strip()
        editops = lev.editops(unicode(gold), unicode(pred))
        tuples.append((len(editops), len(gold)))
    return tuples


def cer(eval_data, predictions, scores='ignored', learner='ignored'):
    '''
    Character Edit Rate: Average Levenshtein distance between gold and prediction,
    weighted and normalized by the length of the gold. Returns a single
    corpus-level (micro) average.
    '''
    golds = [inst.output for inst in eval_data]
    edits, ref_lens = zip(*cer_tuples(golds, predictions))
    return [np.sum(edits) * 1.0 / np.sum(ref_lens)]


def char_errors(eval_data, predictions, scores='ignored', learner='ignored'):
    '''
    Total character errors: total Levenshtein distance between gold and prediction,
    reported per sentence. Aggregate by sum.
    '''
    golds = [inst.output for inst in eval_data]
    return [edits for edits, ref_len in cer_tuples(golds, predictions)]


def sent_errors(eval_data, predictions, scores='ignored', learner='ignored'):
    '''
    Total sentence errors: 0 for sentences where the gold matches the prediction
    perfectly, 1 otherwise. Aggregate by sum or mean.
    '''
    golds = [inst.output for inst in eval_data]
    return [int(edits != 0) for edits, ref_len in cer_tuples(golds, predictions)]


def ref_lens(eval_data, predictions, scores='ignored', learner='ignored'):
    '''
    Total reference length: number of characters in the gold. A diagnostic metric;
    does not change with model output. Aggregate by sum or mean.
    '''
    golds = [inst.output for inst in eval_data]
    return [ref_len for edits, ref_len in cer_tuples(golds, predictions)]


METRICS = {
    name: globals()[name]
    for name in dir()
    if (name not in ['np']
        and not name.startswith('_'))
}
