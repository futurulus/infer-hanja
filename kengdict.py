# -*- coding: utf-8 -*-
import sys
import unicodecsv as csv
from collections import namedtuple, defaultdict

Entry = namedtuple('Entry', ['hangul', 'hanja', 'english'])


class KEngDict(object):
    def __init__(self, infile=None):
        self.entries = []
        self.hanja_index = defaultdict(list)
        if infile:
            rdr = csv.reader(infile, dialect=csv.excel_tab)
            rows = list(rdr)
            for row in rows:
                hanjas = row[9].split(',')
                for j in hanjas:
                    self.add_entry(row[1], j, row[3])

    def add_entry(self, hangul, hanja, english):
        hangul, hanja = strip_dittos(hangul, hanja)
        if hanja is None:
            return
        entry = Entry(hangul, hanja, english)
        self.entries.append(entry)
        for j in set(hanja):
            self.hanja_index[j].append(entry)

    def entries_for_hanja(self, hanja):
        return self.hanja_index[hanja]


_dict = None


def load_dict():
    global _dict
    if _dict is None:
        with open('data/restricted/kengdic_2011.tsv', 'r') as infile:
            _dict = KEngDict(infile)
    return _dict


def entries_for_hanja(hanja):
    d = load_dict()
    return d.entries_for_hanja(hanja)


def strip_dittos(hangul, hanja):
    u'''
    Fills in the full hanja version of a dictionary entry that might
    contain '-' and '~' placeholders.

    "NULL" hanja are replaced with the hangul.

    >>> g, j = strip_dittos(u'갈비', u'NULL'); print g; print j
    갈비
    갈비

    Placeholders at the end are stripped; these consist overwhelmingly of
    variable endings like '하다'.

    >>> g, j = strip_dittos(u'제거하다', u'除去~~'); print g; print j
    제거
    除去
    >>> g, j = strip_dittos(u'제거하다', u'除去'); print g; print j
    제거
    除去
    >>> g, j = strip_dittos(u'가공품', u'加工品-'); print g; print j
    가공품
    加工品
    >>> g, j = strip_dittos(u'가능해지다', u'可能-'); print g; print j
    가능
    可能
    >>> g, j = strip_dittos(u'감미로운', u'甘味---'); print g; print j
    감미
    甘味

    Placeholders at the beginning are replaced with the hangul; these
    are often content words.

    >>> g, j = strip_dittos(u'갈비탕', u'-湯'); print g; print j
    갈비탕
    갈비湯
    '''
    # orig_hangul, orig_hanja = hangul, hanja

    if hanja == 'NULL':
        return hangul, hangul

    while hanja.endswith('-') or hanja.endswith('~'):
        hanja = hanja[:-1]

    ditto_start = False
    while hanja.startswith('-') or hanja.startswith('~'):
        ditto_start = True
        hanja = hanja[1:]

    if not ditto_start and len(hanja) <= len(hangul):
        return hangul[:len(hanja)], hanja
    elif ditto_start and len(hanja) <= len(hangul):
        return hangul, hangul[:-len(hanja)] + hanja
    else:
        # sys.stderr.write('kengdict: could not fill in missing hanja: %s [%s]\n' %
        #                  (orig_hangul.encode('utf-8'), orig_hanja.encode('utf-8')))
        return None, None
