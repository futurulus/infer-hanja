# coding: utf-8
import regex as re

from utils import uopen, uprint
import index_wiki
from index_wiki import load_document
from kde import all_hangul

OUT_PREFIX = 'data/gold_pron_dataset'
KOKORE = 'data/kokore_pages_current.txt'
KOWIKI = 'data/kowiki'


def all_documents(infile):
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
    ... """)
    >>> list(all_documents(testfile))  # doctest: +NORMALIZE_WHITESPACE
    [(u'File A', u'Sentence \\u4e00 one. Sentence \\uc774 two.\\n\\nSentence three\\n'),
     (u'File B', u'Sentence four, in a different doc.\\n')]
    '''
    collected = []
    title = None
    for line in infile:
        match = re.match(r'^<doc .*title="(.*)".*>$', line)
        if match:
            assert title is None
            title = match.group(1)
        elif line.strip() == '</doc>':
            assert title is not None
            yield title, ''.join(collected)
            collected = []
            title = None
        else:
            assert title is not None
            collected.append(line)


def sentence_split(document):
    u'''
    >>> document = u"""Sentence 一 one. Sentence 이 two.
    ...
    ... =See also=
    ... Sentence three, without a period
    ...
    ... Sentence four, with
    ... a line break.
    ... """
    >>> list(sentence_split(document))  # doctest: +NORMALIZE_WHITESPACE
    [u'Sentence \\u4e00 one.',
     u'Sentence \\uc774 two.',
     u'Sentence three, without a period',
     u'Sentence four, with a line break.']
    '''
    # Strip headers
    document = re.sub(r'^=.*=\s*$', '', document.strip(), flags=re.MULTILINE)
    for para in re.split(r'\s*\n\s*\n\s*', document):
        for sent in re.split(r'(?<=\.)\s+', para):
            yield ' '.join(sent.split())


def all_tagged_sentences(infile):
    u'''
    >>> from StringIO import StringIO
    >>> testfile = StringIO(u"""<doc id="1" url="http://example.com/1" title="File A">
    ... Sentence 一 one. Sentence 이 two.
    ...
    ... =See also=
    ... Sentence three, without a period
    ...
    ... Sentence four, with
    ... a line break.
    ... </doc>
    ... <doc id="2" url="http://example.com/2" title="File B">
    ... Sentence five, in a different doc.
    ... </doc>
    ... """)
    >>> list(all_tagged_sentences(testfile))  # doctest: +NORMALIZE_WHITESPACE
    [(u'File A', u'Sentence \\u4e00 one.'),
     (u'File A', u'Sentence \\uc774 two.'),
     (u'File A', u'Sentence three, without a period'),
     (u'File A', u'Sentence four, with a line break.'),
     (u'File B', u'Sentence five, in a different doc.')]
    '''
    for title, document in all_documents(infile):
        for sentence in sentence_split(document):
            yield title, sentence


def element_of(collection, elem):
    return elem in collection


MULTIPLE = ['MULTIPLE']


def find_unique(needle, haystack, match_fn=None):
    '''
    >>> find_unique(2, [1, 2, 3, 4])
    2
    >>> print find_unique(2, [1, 2, 2, 4])
    None
    >>> def match_fn(targets, candidate):
    ...     count = targets.count(candidate.upper())
    ...     if count > 1:
    ...         return MULTIPLE
    ...     else:
    ...         return count == 1
    >>> find_unique(['SEE', 'BE'], ['go', 'do', 'be', 'have'],
    ...             match_fn=match_fn)
    'be'
    >>> print find_unique(['SEE', 'BE', 'DO'], ['go', 'do', 'be', 'have'],
    ...                   match_fn=match_fn)
    None
    '''
    if match_fn is None:
        match_fn = (lambda needle, straw: needle == straw)

    found = None
    for straw in haystack:
        match = match_fn(needle, straw)
        if match:
            if found is None and match is not MULTIPLE:
                found = straw
            else:
                return None
    return found


def strip_parens(s):
    r'''
    Return `s` with all smallest parenthesized substrings removed, also
    normalizing all contiguous whitespace to a single space.

    >>> strip_parens("Hello\t(hi) world!   It's me!")
    "Hello world! It's me!"
    '''
    return re.sub(r'\s+', ' ', re.sub(r'\([^()]+\)', '', s))


def is_match(hanja, hangul, strict=False):
    ur'''
    Return `True` if `hanja` contains the same non-Hanja characters in
    the same order as `hangul`.

    >>> is_match(u'漢字이다', u'한자이다')
    True
    >>> is_match(u'漢字이다', u'한자야')
    False

    Text in parentheses is removed from both strings before comparing, as
    such text is often (but inconsistently) used to provide equivalent text
    in the opposite character set.

    >>> is_match(u'漢字(한자)이다', u'한자(漢字)이다')
    True
    >>> is_match(u'漢字(한자)이다', u'한자이다')
    True
    >>> is_match(u'漢字이다', u'한자(漢字)이다')
    True
    >>> is_match(u'漢字 使用하다', u'한자 (한자) 사용하다')
    True

    By default, no checks on the pronunciation of the characters are
    performed (to allow unusual pronuciations--e.g., in Japanese names).
    Pass `strict=True` to enforce that all Hangul syllables are paired
    with pronunciations listed in the Unihan database.

    >>> is_match(u'漢字이다', u'프랑스어이다')
    True
    >>> is_match(u'漢字이다', u'프랑스어이다', strict=True)
    False
    >>> is_match(u'漢字이다', u'한자이다', strict=True)
    True
    '''
    hanja = strip_parens(hanja)
    hangul = strip_parens(hangul)

    if strict:
        if len(hanja) != len(hangul):
            return False
        for cj, cg in zip(hanja, hangul):
            if cj != cg and cg not in all_hangul(cj):
                return False
        return True
    else:
        pattern = '^%s$' % re.sub(ur'\p{CJK}', ur'\p{Hangul}+',
                                  re.escape(hanja, re.UNICODE),
                                  re.UNICODE)
        return bool(re.match(pattern, hangul))


def is_reverse_match(hangul, hanja):
    return is_match(hanja, hangul)


def is_strict_match(hanja, hangul):
    '''
    Convenience function for use with find_unique. Same as
    `is_match(..., strict=True)`.
    '''
    return is_match(hanja, hangul, strict=True)


def all_pronunciations(hanja):
    if hanja == '':
        yield ''
    else:
        char = hanja[0]
        for pron_rest in all_pronunciations(hanja[1:]):
            yield char + pron_rest
            for pron_char in all_hangul(char):
                yield pron_char + pron_rest


def find_document_match(hanja_title):
    return find_unique(set(index_wiki.load_index()),
                       all_pronunciations(hanja_title),
                       match_fn=element_of)


def find_reverse_match(hangul_sentence, hanja_sentences):
    return find_unique(hangul_sentence, hanja_sentences,
                       match_fn=is_reverse_match)


def find_sentence_match(hanja_sentence, hangul_sentences):
    return find_unique(hanja_sentence, hangul_sentences,
                       match_fn=is_match)


if __name__ == '__main__':
    with uopen(KOKORE, 'r') as hanjain, \
            uopen(OUT_PREFIX + '.hanja', 'w') as hanjaout, \
            uopen(OUT_PREFIX + '.hangul', 'w') as hangulout:
        for hanja_title, hanja_doc in all_documents(hanjain):
            hangul_title = find_document_match(hanja_title)
            if hangul_title:
                uprint('%s\t%s' % (hanja_title, hangul_title))
                hangul_doc = load_document(hangul_title)
                hanja_sentences = list(sentence_split(hanja_doc))
                hangul_sentences = list(sentence_split(hangul_doc))
                for hanja_sentence in hanja_sentences:
                    hangul_sentence = find_sentence_match(hanja_sentence, hangul_sentences)
                    hanja_sentence = strip_parens(hanja_sentence)
                    if hangul_sentence and re.search(ur'\p{CJK}', hanja_sentence, re.UNICODE) \
                            and re.search(ur'\p{Hangul}.*\p{Hangul}', hanja_sentence, re.UNICODE) \
                            and find_reverse_match(hangul_sentence, hanja_sentences):
                        hangul_sentence = strip_parens(hangul_sentence)
                        hanjaout.write(hanja_sentence + '\n')
                        hangulout.write(hangul_sentence + '\n')
