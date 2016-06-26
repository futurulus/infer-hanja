from collections import defaultdict
import multiprocessing
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from stanza.monitoring import progress
from stanza.research import config
from stanza.research.learner import Learner

import kengdict


class ClassifierLearner(Learner):
    def __init__(self):
        self.classifiers = {}
        self.label_dicts = {}
        self.singletons = {}

    def train(self, training_instances, validation_instances='ignored', metrics='ignored'):
        training_instances = list(training_instances)

        print('Assembling label sets')
        # Vectorize once to get the labels for the dictionary features
        _, labels, _ = self.data_to_arrays(training_instances)
        for hangul in labels:
            enc = LabelEncoder()
            enc.fit(labels[hangul])
            if len(enc.classes_) == 1:
                self.singletons[hangul] = enc.classes_[0]
                continue
            else:
                assert len(enc.classes_) > 1
                self.label_dicts[hangul] = enc

        print('Featurizing')
        # Vectorize a second time to fill in the dictionary feature values
        features, labels, _ = self.data_to_arrays(training_instances)

        print('Training')
        progress.start_task('Character', len(labels))
        for i, hangul in enumerate(labels):
            progress.progress(i)

            if hangul in self.singletons:
                continue

            vec = DictVectorizer()
            arr_features = vec.fit_transform(features[hangul])

            enc = self.label_dicts[hangul]
            arr_labels = enc.transform(labels[hangul])

            model = LogisticRegression(solver='lbfgs', multi_class='multinomial')
            model.fit(arr_features, arr_labels)

            self.classifiers[hangul] = (model, vec, self.label_dicts[hangul])
        progress.end_task()

    @property
    def num_params(self):
        total = 0
        for model, _, _ in self.classifiers.values():
            total += np.prod(model.coef_.shape) + np.prod(model.intercept_.shape)
        return total

    def predict_and_score(self, eval_instances):
        print('Featurizing')
        features, _, indices = self.data_to_arrays(eval_instances)
        pred_labels = {}

        print('Predicting')
        progress.start_task('Character', len(features))
        for i, hangul in enumerate(features):
            progress.progress(i)

            if hangul in self.classifiers:
                model, vec, enc = self.classifiers[hangul]
                arr_features = vec.transform(features[hangul])
                arr_pred_labels = model.predict(arr_features)
                pred_labels[hangul] = enc.inverse_transform(arr_pred_labels)
            elif hangul in self.singletons:
                pred_labels[hangul] = [self.singletons[hangul]] * len(features[hangul])
            else:
                pred_labels[hangul] = [hangul] * len(features[hangul])
        progress.end_task()

        predictions = []
        scores = []
        for i, inst in enumerate(eval_instances):
            pred = ''.join([pred_labels[g][indices[i][j]]
                            for j, g in enumerate(inst.input)])
            score = -float('inf')  # TODO
            predictions.append(pred)
            scores.append(score)
        return predictions, scores

    def data_to_arrays(self, insts):
        options = config.options()

        worker_pool = multiprocessing.Pool(options.featurization_threads)

        features = defaultdict(list)
        labels = defaultdict(list)
        indices = []
        progress.start_task('Sentence', len(insts))
        for i, inst in enumerate(insts):
            progress.progress(i)

            assert len(inst.input) == len(inst.output), inst.__dict__
            indices_inst = []
            featurizer_args = []
            for j, (hangul, hanja) in enumerate(zip(inst.input, inst.output)):
                if hangul in self.label_dicts:
                    classes = self.label_dicts[hangul].classes_
                else:
                    classes = []

                indices_inst.append(len(labels[hangul]))
                featurizer_args.append((inst.input, j, classes, options.features))
                labels[hangul].append(hanja)

            for hangul, feats in worker_pool.map(featurize, featurizer_args):
                features[hangul].append(feats)

            indices.append(indices_inst)
        progress.end_task()
        return features, labels, indices


def featurize(args):
    input, idx, hanjas, feat_types = args
    feats = {}
    for feat_type in feat_types:
        feats.update(FEATURES[feat_type](input, idx, hanjas))
    return input[idx], feats


def next_features(input, idx, hanjas):
    return {'next': input[idx + 1:idx + 2]}


def prev_features(input, idx, hanjas):
    return {'prev': input[max(0, idx - 1):idx]}


def sent_boc_features(input, idx, hanjas):
    return {u'sent:' + c: 1 for i, c in enumerate(input) if i != idx}


def dict_features(input, idx, hanjas):
    feats = {}
    for hanja in hanjas:
        for entry in kengdict.entries_for_hanja(hanja):
            for pos in find_all(entry.hanja, hanja):
                if input[idx - pos:idx - pos + len(entry.hangul)] == entry.hangul:
                    feats[u'dictentry%s' % len(entry.hangul)] = hanja
    return feats


def find_all(haystack, needle):
    start = 0
    while True:
        pos = haystack.find(needle, start)
        if pos == -1:
            break
        yield pos
        start = pos + 1


FEATURES = {
    'next': next_features,
    'prev': prev_features,
    'sent_boc': sent_boc_features,
    'dict': dict_features,
}

parser = config.get_options_parser()
parser.add_argument('--features', nargs='*', choices=FEATURES.keys(),
                    help='Feature set to use for ClassifierLearner')
parser.add_argument('--featurization_threads', type=int, default=8,
                    help='Number of processes to use for multiprocessing-based featurization')
