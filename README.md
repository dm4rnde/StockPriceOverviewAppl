<br>

> Because module this app depends on does
> not work anymore (google finance side interrupted)
> **graph side (historical prices) does NOT WORK** at the moment.

<br>

# Stock Price Overview Appl

<br>


Short and **basic GUI application written in Python** that **uses tkinter** (created for practice and study purpose only).

Application allows user to:
- see current price of selected stock
- observe historical price change of selected stock on a graph
- add/remove stock symbols to/from list

<br>

#### In case of 'does not start/run'

*Note #1*. Haven't tested with other than mentioned specifics (see below).<br>
*Note #2*. There is always possibility that when running Python program written by others, that some packages are not available/not on computer/environment (then have to try to install them manually - but this is already, out of scope of this document, and specific to every python/environment setup).<br>
*Note #3*. And there is some awkward possibility that program might not work in certain circumstances at all (or some unknown adjustment is needed).<br>
*Note #4*. Dependencies have become defunct.

<br>

Specifics (that surrounded application at the moment of development):
- Python 3.6.2
- tkinter 8.5
- pandas (0.20.3) [package]
- pandas-datareader (0.5.0) [package]
- matplotlib (2.0.2) [package]
- json (2.0.9) [package]
- (did run/tested under macOS 10)
