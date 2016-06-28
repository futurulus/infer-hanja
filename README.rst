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
