pyletterpress
=============

A python script for trying to generate the best words to play in Letterpress for iOS

Simply run `python pyletterpress.py` followed by your board letters:

```python
python pyletterpress.py abcdefghijklmnopqrstuvwxy
```

Uses the [Logbook](http://packages.python.org/Logbook/index.html) library for logging and the [SortedCollection](http://code.activestate.com/recipes/577197-sortedcollection/) recipe for ordering the resulting suggestions.