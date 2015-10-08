import regex
from collections import Counter
from kde import all_hangul
from utils import uprint

def is_cjk(c):
  return bool(regex.match(r'\p{CJK}', c, regex.UNICODE))

def key(hangul_list):
  return ''.join(sorted(hangul_list))


if __name__ == '__main__':
  print 'Reading text...'
  with open('data/kokore_pages_current.txt', 'r') as infile:
    text = infile.read().decode('utf-8')

  print 'Counting characters...'
  counter = Counter(c for c in text if is_cjk(c))

  for c, count in counter.most_common():
    uprint('%d %s [%s]' % (count, c, key(all_hangul(c))))
