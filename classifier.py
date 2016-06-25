from collections import defaultdict
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from stanza.monitoring import progress
from stanza.research import config
from stanza.research.learner import Learner


class ClassifierLearner(Learner):
    def __init__(self):
        self.classifiers = {}
        self.singletons = {}

    def train(self, training_instances, validation_instances='ignored', metrics='ignored'):
        training_instances = list(training_instances)

        features, labels, _ = self.data_to_arrays(training_instances)

        progress.start_task('Character', len(labels))
        for i, hangul in enumerate(labels):
            progress.progress(i)

            enc = LabelEncoder()
            arr_labels = enc.fit_transform(labels[hangul])
            if len(enc.classes_) == 1:
                self.singletons[hangul] = enc.classes_[0]
                continue
            else:
                assert len(enc.classes_) > 1

            vec = DictVectorizer()
            arr_features = vec.fit_transform(features[hangul])

            model = LogisticRegression(solver='lbfgs', multi_class='multinomial')
            model.fit(arr_features, arr_labels)

            self.classifiers[hangul] = (model, vec, enc)
        progress.end_task()

    @property
    def num_params(self):
        total = 0
        for model, _, _ in self.classifiers.values():
            total += np.prod(model.coef_.shape) + np.prod(model.intercept_.shape)
        return total

    def predict_and_score(self, eval_instances):
        features, _, indices = self.data_to_arrays(eval_instances)
        pred_labels = {}

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
        features = defaultdict(list)
        labels = defaultdict(list)
        indices = []
        for i, inst in enumerate(insts):
            assert len(inst.input) == len(inst.output), inst.__dict__
            indices_inst = []
            for j, (hangul, hanja) in enumerate(zip(inst.input, inst.output)):
                indices_inst.append(len(labels[hangul]))
                features[hangul].append(self.featurize(inst.input, j))
                labels[hangul].append(hanja)
            indices.append(indices_inst)
        return features, labels, indices

    def featurize(self, input, idx):
        options = config.options()
        feats = {}
        for feat_type in options.features:
            feats.update(FEATURES[feat_type](input, idx))
        return feats


def next_feature(input, idx):
    return {'next': input[idx + 1:idx + 2]}


def prev_feature(input, idx):
    return {'prev': input[max(0, idx - 1):idx]}


FEATURES = {
    'next': next_feature,
    'prev': prev_feature,
}

parser = config.get_options_parser()
parser.add_argument('--features', nargs='*', choices=FEATURES.keys(),
                    help='Feature set to use for ClassifierLearner')
