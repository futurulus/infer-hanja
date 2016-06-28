import codecs


def uprint(s):
    print s.encode('utf-8')


def urepr(s):
    return repr(s).decode('unicode_escape')


def uopen(filename, *args, **kwargs):
    return codecs.open(filename, *args, encoding='utf-8', **kwargs)
