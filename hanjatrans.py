# -*- coding: utf-8 -*-
import cPickle as pickle

from stanza.research.instance import Instance

from utils import urepr  # NOQA: for doctest


class HanjaTranslator(object):
    '''
    A wrapper class for (by default) the logistic regression model in classifier.py.
    '''
    def __init__(self, picklefile=None):
        '''
        :param file picklefile: An open file-like object from which to
            load the model. Can be produced either from a normal experiment
            run or a quickpickle.py run. If `None`, try to load the default
            quickpickle file (this is less future-proof than the normal
            experiment-produced pickle files).
        '''
        if picklefile is None:
            with open('models/lr_prevnext/model.pkl', 'rb') as infile:
                self.model = pickle.load(infile)
        else:
            self.model = pickle.load(picklefile)
        self.model.options.verbosity = 0

    def translate(self, hangul_sent):
        u'''
        Infer the most likely hanja for each syllable in `hangul_sent` (where
        "leave the hangul unchanged" is usually one option), and return a string
        with the predicted hanja substituted for the hangul.

        >>> tr = HanjaTranslator()
        >>> print urepr(tr.translate(u'2011년 12월 26일'))
        u'2011年 12月 26日'
        '''
        return self.translate_all([hangul_sent])[0]

    def translate_all(self, hangul_sents):
        u'''
        Infer the most likely hanja for each syllable of each sentence in
        `hangul` (where "leave the hangul unchanged" is usually one options),
        and return a list of strings with the predicted hanja substituted
        for the hangul.

        >>> tr = HanjaTranslator()
        >>> print urepr(tr.translate_all([u'2011년 12월 26일', u'중화인민공화국']))
        [u'2011年 12月 26日', u'中華人民共和國']
        '''
        insts = [Instance(g) for g in hangul_sents]
        return self.model.predict(insts, verbosity=0)
