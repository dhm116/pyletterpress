from __future__ import division
import sys, itertools
from logbook import Logger
from multiprocessing import Pool, Queue, Process, Manager
import time
from threading import Thread
from bisect import bisect_left, bisect_right

class SortedCollection(object):
    '''Sequence sorted by a key function.

    SortedCollection() is much easier to work with than using bisect() directly.
    It supports key functions like those use in sorted(), min(), and max().
    The result of the key function call is saved so that keys can be searched
    efficiently.

    Instead of returning an insertion-point which can be hard to interpret, the
    five find-methods return a specific item in the sequence. They can scan for
    exact matches, the last item less-than-or-equal to a key, or the first item
    greater-than-or-equal to a key.

    Once found, an item's ordinal position can be located with the index() method.
    New items can be added with the insert() and insert_right() methods.
    Old items can be deleted with the remove() method.

    The usual sequence methods are provided to support indexing, slicing,
    length lookup, clearing, copying, forward and reverse iteration, contains
    checking, item counts, item removal, and a nice looking repr.

    Finding and indexing are O(log n) operations while iteration and insertion
    are O(n).  The initial sort is O(n log n).

    The key function is stored in the 'key' attibute for easy introspection or
    so that you can assign a new key function (triggering an automatic re-sort).

    In short, the class was designed to handle all of the common use cases for
    bisect but with a simpler API and support for key functions.

    >>> from pprint import pprint
    >>> from operator import itemgetter

    >>> s = SortedCollection(key=itemgetter(2))
    >>> for record in [
    ...         ('roger', 'young', 30),
    ...         ('angela', 'jones', 28),
    ...         ('bill', 'smith', 22),
    ...         ('david', 'thomas', 32)]:
    ...     s.insert(record)

    >>> pprint(list(s))         # show records sorted by age
    [('bill', 'smith', 22),
     ('angela', 'jones', 28),
     ('roger', 'young', 30),
     ('david', 'thomas', 32)]

    >>> s.find_le(29)           # find oldest person aged 29 or younger
    ('angela', 'jones', 28)
    >>> s.find_lt(28)           # find oldest person under 28
    ('bill', 'smith', 22)
    >>> s.find_gt(28)           # find youngest person over 28
    ('roger', 'young', 30)

    >>> r = s.find_ge(32)       # find youngest person aged 32 or older
    >>> s.index(r)              # get the index of their record
    3
    >>> s[3]                    # fetch the record at that index
    ('david', 'thomas', 32)

    >>> s.key = itemgetter(0)   # now sort by first name
    >>> pprint(list(s))
    [('angela', 'jones', 28),
     ('bill', 'smith', 22),
     ('david', 'thomas', 32),
     ('roger', 'young', 30)]

    '''

    def __init__(self, iterable=(), key=None):
        self._given_key = key
        key = (lambda x: x) if key is None else key
        decorated = sorted((key(item), item) for item in iterable)
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]
        self._key = key

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)' % (
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        'Find the position of an item.  Raise ValueError if not found.'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def count(self, item):
        'Return number of occurrences of item'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def insert_right(self, item):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(item)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        'Remove first occurence of item.  Raise ValueError if not found'
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def find(self, k):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_le(self, k):
        'Return last item with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        'Return last item with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_ge(self, k):
        'Return first item with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        'Return first item with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))

def evaluator(args):#word, letters, queue, log_queue):
	word, letters, queue = args
	common = len([letters.pop(letters.index(x)) for x in word if x in letters])
	if common == len(word):
		queue.put(word)

		return word
	else:
		return None

def top_words(sorted_set):
	log = Logger("Top Words")
	top = []

	while True:
		if(len(sorted_set) > 0):
			test = list(reversed(sorted_set[-10:]))
			if 0 in [item in top for item in test]:
				top = test

				log.info('#1-10 of {}: {}'.format(len(sorted_set), ', '.join(top)))
		time.sleep(0.01)

def result_collector(results, best_words):
	while True:
		if not results.empty():
			best_words.insert(results.get())
		time.sleep(0.01)

def percent_reporter(complete):
	while True:
		log.notice('{:.2f}% complete'.format(complete.get()))

		time.sleep(0.01)

if __name__ == '__main__':
	log = Logger('Main')

	if len(sys.argv) > 1:
		letters = sys.argv[1]

		if letters:
			letters = [x for x in letters]

			log.info('Working with {}'.format(letters))

			words = set()

			with open('wordsEn.txt') as dictionary:
				words = set(word.strip().lower() for word in dictionary if len(word) <= len(letters) and len(word) > 1)
				
			log.info('Evaluation against {} words'.format(len(words)))

			log.info('Sorting words')
			words = sorted(words, key=lambda word: len(word))
			#max_length = max(words, key= lambda word: len(word))

			#log.info('Max word length is {}'.format(max_length))

			log.info('Creating worker pool')
			manager = Manager()
			results = manager.Queue()
			complete = manager.Queue()
			pool = Pool()

			best_words = SortedCollection(key=lambda word: len(word))

			top_printer = Thread(target=top_words, args=(best_words,))
			top_printer.daemon = True
			top_printer.start()

			collector = Thread(target=result_collector, args=(results, best_words))
			collector.daemon = True
			collector.start()

			reporter = Thread(target=percent_reporter, args=(complete,))
			reporter.daemon = True
			reporter.start()

			block_size = 1000
			for x in xrange(0, len(words), block_size):
				complete.put(x/len(words) * 100)
				#log.debug('Items {} through {} contains {} elements'.format(x, x+block_size, len(words[x:x+block_size])))

				pool.map_async(evaluator, [(word, letters, results) for word in words[x:x+block_size]])

			#log.info(len([(word, letters, results) for word in words]))
			#blah = pool.map_async(evaluator, [(word, letters, results) for word in words])
			#log.info('Done: {}'.format([word for word in blah.get() if word is not None]))
			pool.close()

			done = False
			try:
				while not done:
					if len(best_words) > 1 and results.empty() and complete.empty():
						done = True
						
					time.sleep(0.01)
			except KeyboardInterrupt:
				log.warn('Exiting application')
			
			pool.terminate()

			log.info('Best words: {}'.format(', '.join(reversed(best_words))))
	else:
		log.critical('No letters supplied')