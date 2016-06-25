from collections import Counter, defaultdict
import numpy as np

from stanza.monitoring import progress
from stanza.research.learner import Learner

import classifier


def new(key):
    '''
    Construct a new learner with the class named by `key`. A list
    of available learners is in the dictionary `LEARNERS`.
    '''
    return LEARNERS[key]()


class IdentityLearner(Learner):
    def __init__(self):
        pass

    def train(self, training_instances, validation_instances='ignored', metrics='ignored'):
        pass

    @property
    def num_params(self):
        return 0

    def predict_and_score(self, eval_instances):
        predictions = [inst.input for inst in eval_instances]
        scores = [-float('inf') for inst in eval_instances]
        return predictions, scores


class MostCommonLearner(Learner):
    def __init__(self):
        self.counter_map = defaultdict(Counter)
        self.num_examples = defaultdict(int)

    def train(self, training_instances, validation_instances='ignored', metrics='ignored'):
        progress.start_task('Example', len(training_instances))
        for i, inst in enumerate(training_instances):
            progress.progress(i)
            assert len(inst.input) == len(inst.output), inst.__dict__
            for hangul, hanja in zip(inst.input, inst.output):
                self.counter_map[hangul].update([hanja])
        progress.end_task()
        for hangul, counts in self.counter_map.iteritems():
            num_ex = sum(counts.values())
            assert num_ex > 0, num_ex
            self.num_examples[hangul] = num_ex

    @property
    def num_params(self):
        return sum(len(c) for c in self.counter_map.values())

    def predict_and_score(self, eval_instances):
        predictions = []
        scores = []
        progress.start_task('Example', len(eval_instances))
        for i, inst in enumerate(eval_instances):
            assert len(inst.input) == len(inst.output), inst.__dict__
            pred = ''.join([self.lookup(g) for g in inst.input])
            score = np.sum([np.log(self._get_smoothed_prob(g, j))
                            for g, j in zip(inst.input, inst.output)])
            predictions.append(pred)
            scores.append(score)
            progress.progress(i)
        progress.end_task()
        return predictions, scores

    def lookup(self, hangul):
        if hangul not in self.counter_map:
            return hangul

        mc = self.counter_map[hangul].most_common(1)
        try:
            return mc[0][0]
        except IndexError:
            return hangul

    def _get_smoothed_prob(self, hangul, hanja):
        if hangul not in self.counter_map:
            return 1.0
        elif hanja in self.counter_map[hangul] and self.counter_map[hangul][hanja] > 1:
            assert hangul in self.num_examples and self.num_examples[hangul] > 0, hangul
            return (self.counter_map[hangul][hanja] - 1.0) / self.num_examples[hangul]
        else:
            assert hangul in self.num_examples and self.num_examples[hangul] > 0, hangul
            return 1.0 * len(self.counter_map[hangul]) / self.num_examples[hangul]


LEARNERS = {
    'Identity': IdentityLearner,
    'MostCommon': MostCommonLearner,
    'Classifier': classifier.ClassifierLearner,
}
