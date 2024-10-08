******************************
Smarter Scraping with Caching
******************************


Install the `nospam` package to cache API calls and reduce spam to Yahoo:

.. code-block:: bash

   pip install yfinance[nospam]

Use `requests_cache` for smarter scraping:

.. code-block:: python

   import requests_cache
   session = requests_cache.CachedSession('yfinance.cache')
   session.headers['User-agent'] = 'my-program/1.0'

   ticker = yf.Ticker('MSFT', session=session)
   ticker.actions
