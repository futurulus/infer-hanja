from collections import Counter
import numpy as np

from stanza.monitoring import progress
from stanza.research.learner import Learner


def new(key):
    '''
    Construct a new learner with the class named by `key`. A list
    of available learners is in the dictionary `LEARNERS`.
    '''
    return LEARNERS[key]()


class MostCommonLearner(Learner):
    def __init__(self):
        self.seen = Counter()
        self.num_examples = 0

    def train(self, training_instances, validation_instances='ignored', metrics='ignored'):
        progress.start_task('Example', len(training_instances))
        for i, inst in enumerate(training_instances):
            progress.progress(i)
            self.seen.update([inst.output])
        progress.end_task()
        self.num_examples += len(training_instances)

    @property
    def num_params(self):
        return len(self.seen)

    def predict_and_score(self, eval_instances):
        most_common = self.seen.most_common(1)[0][0]
        predict = [most_common] * len(eval_instances)
        score = []
        progress.start_task('Example', len(eval_instances))
        for i, inst in enumerate(eval_instances):
            progress.progress(i)
            score.append(np.log(self._get_smoothed_prob(inst.output)))
        progress.end_task()
        return predict, score

    def _get_smoothed_prob(self, output):
        if output in self.seen and self.seen[output] > 1:
            return (self.seen[output] - 1.0) / self.num_examples
        else:
            return 1.0 * len(self.seen) / self.num_examples


LEARNERS = {
    'MostCommon': MostCommonLearner,
}
