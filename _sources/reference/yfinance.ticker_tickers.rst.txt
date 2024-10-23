=====================
Ticker and Tickers
=====================

.. currentmodule:: yfinance

Class
~~~~~~~
.. autosummary::
   :toctree: api/

   Ticker
   Tickers

Sample Code
------------------
The `Ticker` module, which allows you to access ticker data in a more Pythonic way:

.. literalinclude:: examples/ticker.py
   :language: python

To initialize multiple `Ticker` objects, use

.. literalinclude:: examples/tickers.py
   :language: python

For tickers that are ETFs/Mutual Funds, `Ticker.funds_data` provides access to fund related data. 

Funds' Top Holdings and other data with category average is returned as `pd.DataFrame`.

.. literalinclude:: examples/funds_data.py
   :language: python