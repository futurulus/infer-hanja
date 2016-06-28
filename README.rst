Hangul to Hanja conversion
==========================

Setup
~~~~~

You'll need Python 2 with scikit-learn (and therefore numpy, scipy, and ctypes)
installed. Anaconda is highly recommended.

::

    $ ./dependencies

Usage
~~~~~

::

    >>> import hanjatrans
    >>> tr = hanjatrans.HanjaTranslator()
    >>> print tr.translate(u'2011년 12월 26일')
    2011年 12月 26日

Output examples
~~~~~~~~~~~~~~~

Inferring correct hanja is somewhat difficult, and this library doesn't do it
perfectly. See
https://htmlpreview.github.io/?http://github.com/futurulus/infer-hanja/blob/master/sample_errors.html
for more examples of the library's output, with errors highlighted.
