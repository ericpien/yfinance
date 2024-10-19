=========================
Functions and Utilities
=========================

.. contents::
   :depth: 2
   :local:

Functions
---------

Download Market Data
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: yfinance.download

The `download` function allows you to retrieve market data for multiple tickers at once.

Query Market Data
~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: yfinance.EquityQuery
   :members: operator, operands
   :undoc-members:
   :show-inheritance:

.. autoclass:: yfinance.Screener
   :members:
   :undoc-members:

Utilities
---------

Enable Debug Mode
~~~~~~~~~~~~~~~~~

.. autofunction:: yfinance.enable_debug_mode

Enables logging of debug information for the `yfinance` package.

Set Timezone Cache Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: yfinance.set_tz_cache_location

Sets the cache location for timezone data.
