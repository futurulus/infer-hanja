# coding: utf-8

import sys
import cPickle as cp
import regex
from itertools import groupby as g
from collections import Counter
from random import sample
from cjklib import characterlookup

from utils import uprint


cjk = characterlookup.CharacterLookup('C')


CHARS = r'\p{Hangul}|\p{CJK}'


def score(x):
    return len([c for c in x if regex.match(CHARS, c, regex.UNICODE)])


def convert(s):
    return s.decode('utf-8').strip()


def fix(s):
    s = convert(s)
    try:
        mangled = s.encode('latin-1').decode('utf-8')
        if score(mangled) > score(s):
            return mangled
        else:
            return s
    except UnicodeEncodeError:
        return s
    except UnicodeDecodeError:
        return s


def memoize(f):
    memo = {}

    def helper(x):
        if x not in memo:
            memo[x] = f(x)
        return memo[x]

    return helper


@memoize
def all_hanja(syll):
    chars = cjk.getCharactersForReading(syll, 'Hangul')
    result = set(chars)
    for c in chars:
        for v in cjk.getAllCharacterVariants(c):
            result.add(v[0])
    return sorted(result)


@memoize
def all_hangul(hanja):
    sylls = cjk.getReadingForCharacter(hanja, 'Hangul')
    result = set(sylls)
    for v in cjk.getAllCharacterVariants(hanja):
        result.update(cjk.getReadingForCharacter(v[0], 'Hangul'))
    return sorted(result)


if __name__ == '__main__':
    with open('data/KDE4.ko-zh_CN.ko', 'r') as ko, open('data/KDE4.ko-zh_CN.zh_CN', 'r') as zh:
        dataset = zip(ko, zh)

    dataset = [(fix(k), fix(c)) for k, c in dataset]

    dataset = [p for p in dataset if score(p[0]) != 0]
    with open('data/dataset.p', 'wb') as outfile:
            cp.dump(dataset, outfile)

    uprint('Sample pairs:')
    for ko, cn in sample(dataset, 20):
            uprint(ko)
            uprint(cn)
            print

    best = sorted(dataset, key=lambda p: score(p[0]))

    uprint('Histogram of sentence scores:')
    for key, group in g(best, key=lambda p: score(p[0])):
            uprint('%s %d' % (key, len(list(group))))
    print

    nsylls = nplaus = n1plaus = 0
    cooc = Counter()
    for i, (k, c) in enumerate(dataset):
        if i % 1000 == 0:
            print >>sys.stderr, '.',
        for s in k:
            if score(s) == 0:
                continue
            nsylls += 1
            plaus = False
            for h in all_hanja(s):
                if h in c:
                    nplaus += 1
                    plaus = True
                    cooc.update([(s, h)])
                if plaus:
                    n1plaus += 1

    uprint('Plausible co-occurrences:')
    for ((s, h), count) in cooc.most_common():
            uprint(u'%d %s -> %s' % (count, s, h))
    print

    div = Counter([s for ((s, h), count) in cooc.most_common()])

    uprint('Plausible hanja diversity by syllable:')
    for syll, count in div.most_common():
                uprint('%d %s' % (count, syll))
    print

    uprint('Total Hangul syllable types with plausible hanja: %d' % len(div))
    uprint('Total plausible hanja types identified: %d' % len(cooc))
