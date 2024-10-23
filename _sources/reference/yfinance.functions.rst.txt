=========================
Functions and Utilities
=========================

.. currentmodule:: yfinance
   
Download Market Data
~~~~~~~~~~~~~~~~~~~~~

.. autosummary:: 
   :toctree: api/

   download

The `download` function allows you to retrieve market data for multiple tickers at once.

Query Market Data
~~~~~~~~~~~~~~~~~~~~~
.. autosummary:: 
   :toctree: api/

   EquityQuery
   Screener

.. seealso::
   :attr:`EquityQuery.valid_fields <yfinance.EquityQuery.valid_fields>`
      supported operand values for query
   :attr:`EquityQuery.valid_eq_map <yfinance.EquityQuery.valid_eq_map>`
      supported `EQ query operand parameters`
   :attr:`Screener.predefined_bodies <yfinance.Screener.predefined_bodies>`
      supported predefined screens
   

Enable Debug Mode
~~~~~~~~~~~~~~~~~
.. autosummary:: 
   :toctree: api/

   enable_debug_mode

Enables logging of debug information for the `yfinance` package.

Set Timezone Cache Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary:: 
   :toctree: api/

   set_tz_cache_location

Sets the cache location for timezone data.
