# coding: utf-8
import Levenshtein as lev
from hanja import hanja as libhanja
from utils import uopen, uprint
from kde import all_hangul


def no_conversion(input_seq):
    return input_seq


def haeng_pron_char(c):
    if c == u'行':
        return u'행'
    hangul = all_hangul(c)
    if hangul:
        return hangul[0]
    else:
        return c


def first_pron_char(c):
    hangul = all_hangul(c)
    if hangul:
        return hangul[0]
    else:
        return c


def first_pron(input_seq):
    return u''.join(first_pron_char(c) for c in input_seq)


def haeng_pron(input_seq):
    return u''.join(haeng_pron_char(c) for c in input_seq)


def libhanja_pron(input_seq):
    return libhanja.translate(input_seq, 'substitution')


COLORS = ['black', 'red', 'green', 'yellow', 'blue', 'purple', 'cyan', 'white']


def wrap_color(s, color):
    code = COLORS.index(color)
    if code == -1:
        raise ValueError('unrecognized color: ' + color)
    return '\033[1;3%dm%s\033[0m' % (code, s)


def highlight(text, positions, color):
    chars = []
    for i, c in enumerate(text):
        if i in positions:
            chars.append(wrap_color(c, color))
        else:
            chars.append(c)
    return u''.join(chars)


def print_visualization(input_seq, pred_output_seq,
                        gold_output_seq, editops):
    gold_highlights = []
    pred_highlights = []
    for optype, gold_idx, pred_idx in editops:
        gold_highlights.append(gold_idx)
        pred_highlights.append(pred_idx)

    input_seq = highlight(input_seq, pred_highlights, 'cyan')
    pred_output_seq = highlight(pred_output_seq, pred_highlights, 'red')
    gold_output_seq = highlight(gold_output_seq, gold_highlights, 'yellow')
    uprint(input_seq)
    uprint(pred_output_seq)
    uprint(gold_output_seq)
    uprint('')


def evaluate(predict_fn, devtest, visualize=False):
    total_errors = 0
    total_perfect = 0
    examples = len(devtest)
    for input_seq, gold_output_seq in devtest:
        input_seq = input_seq.strip()
        gold_output_seq = gold_output_seq.strip()

        pred_output_seq = predict_fn(input_seq)
        editops = lev.editops(gold_output_seq, pred_output_seq)
        total_errors += len(editops)
        if editops:
            if visualize:
                print_visualization(input_seq, pred_output_seq,
                                    gold_output_seq, editops)
        else:
            total_perfect += 1
    return (total_errors, total_perfect, examples)


if __name__ == '__main__':
    with uopen('data/gold_pron_dataset.hanja', 'r') as hanja, \
            uopen('data/gold_pron_dataset.hangul', 'r') as hangul:
        test_set = zip(hanja, hangul)

    possible_errors, possible_perfect, examples = evaluate(no_conversion, test_set)

    first_errors, first_perfect, _ = evaluate(first_pron, test_set, visualize=False)
    first_error_reduction = (possible_errors - first_errors) * 100.0 / possible_errors
    pct_first_perfect = first_perfect * 100.0 / examples

    haeng_errors, haeng_perfect, _ = evaluate(haeng_pron, test_set, visualize=False)
    haeng_error_reduction = (possible_errors - haeng_errors) * 100.0 / possible_errors
    pct_haeng_perfect = haeng_perfect * 100.0 / examples

    libhanja_errors, libhanja_perfect, _ = evaluate(libhanja_pron, test_set, visualize=True)
    libhanja_error_reduction = (possible_errors - libhanja_errors) * 100.0 / possible_errors
    pct_libhanja_perfect = libhanja_perfect * 100.0 / examples
    print('No conversion: %d errors, %d perfect of %d examples' %
          (possible_errors, possible_perfect, examples))
    print(('First pronunciation: %d errors (%f%% reduction), ' +
           '%d perfect of %d examples (%f%%)') %
          (first_errors, first_error_reduction, first_perfect, examples, pct_first_perfect))
    print(('haeng pronunciation: %d errors (%f%% reduction), ' +
           '%d perfect of %d examples (%f%%)') %
          (haeng_errors, haeng_error_reduction, haeng_perfect, examples, pct_haeng_perfect))
    print(('libhanja pronunciation: %d errors (%f%% reduction), ' +
           '%d perfect of %d examples (%f%%)') %
          (libhanja_errors, libhanja_error_reduction, libhanja_perfect,
           examples, pct_libhanja_perfect))
