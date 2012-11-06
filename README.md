pyletterpress
=============

A python script for trying to generate the best words to play in Letterpress for iOS

Simply run `python pyletterpress.py` followed by your board letters:

```python
python pyletterpress.py abcdefghijklmnopqrstuvwxy
```

You can also optionally specify preferred letters as the third parameter:

```python
python pyletterpress.py abcdefghijklmnopqrstuvwxy vxp
```

which will then sort the word list by words containing your preferred letters.

Uses the [Logbook](http://packages.python.org/Logbook/index.html) library for logging and the [SortedCollection](http://code.activestate.com/recipes/577197-sortedcollection/) recipe for ordering the resulting suggestions.