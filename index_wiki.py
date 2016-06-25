# coding: utf-8
import re
import glob
from utils import uopen, uprint


KOWIKI_GLOB = 'data/kowiki/*/*'
INDEX_FILE = 'data/kowiki_index.tsv'


def index_file(infile):
    u'''
    >>> from StringIO import StringIO
    >>> testfile = StringIO(u"""<doc id="1" url="http://example.com/1" title="File A">
    ... Sentence 一 one. Sentence 이 two.
    ...
    ... Sentence three
    ... </doc>
    ... <doc id="2" url="http://example.com/2" title="File B">
    ... Sentence four, in a different doc.
    ... </doc>
    ... """.encode('utf-8'))
    >>> list(index_file(testfile))  # doctest: +NORMALIZE_WHITESPACE
    [(55, u'File A'),
     (169, u'File B')]
    '''
    for line in iter(infile.readline, ''):
        line = line.decode('utf-8')
        match = re.match(r'^<doc .*title="(.*)".*>$', line)
        if match:
            yield infile.tell(), match.group(1)


INDEX = None
TITLES = []


def load_index():
    global INDEX
    if INDEX is not None:
        return INDEX

    INDEX = {}
    with uopen(INDEX_FILE, 'r') as infile:
        for line in infile:
            filename, seekpos, title = line.strip().split('\t')
            INDEX[title] = (filename, int(seekpos))
            TITLES.append(title)

    return INDEX


def load_document(title):
    load_index()
    collected = []
    filename, seekpos = INDEX[title]
    with open(filename, 'r') as infile:
        infile.seek(seekpos, 0)
        for line in iter(infile.readline, ''):
            line = line.decode('utf-8')
            if line.strip() == '</doc>':
                break
            collected.append(line)
    return ''.join(collected)


def all_titles():
    load_index()
    return TITLES


if __name__ == '__main__':
    for filename in sorted(glob.glob(KOWIKI_GLOB)):
        with open(filename, 'r') as infile:
            for seekpos, title in index_file(infile):
                uprint(u'\t'.join([filename, str(seekpos), title]))
