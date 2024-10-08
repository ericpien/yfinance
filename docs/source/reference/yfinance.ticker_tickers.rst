=====================
Ticker and Tickers
=====================

.. contents::
   :depth: 2
   :local:

Ticker Class
------------------

The `Ticker` class provides access to Yahoo! Finance data for a specific ticker symbol (e.g., "AAPL" for Apple, "GOOG" for Google). It offers a Pythonic interface to retrieve stock data, financial statements, actions, and more.

.. autoclass:: yfinance.Ticker
   :members:
   :undoc-members:
   :show-inheritance:


Tickers Class
------------------

The `Tickers` class provides access to multiple ticker symbols at once. It allows you to retrieve data for a group of tickers in a bulk operation.

.. autoclass:: yfinance.Tickers
   :members:
   :undoc-members:
   :show-inheritance:

TickerBase
------------------

TickerBase Abstract Class

.. autoclass:: yfinance.base.TickerBase
   :members: 
   :undoc-members:
   :show-inheritance:

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