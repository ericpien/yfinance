=======================
Sector and Industry
=======================

.. currentmodule:: yfinance

Class
~~~~~~~
.. autosummary::
   :toctree: api/
   :recursive:

   Sector
   Industry

.. seealso::
   :attr:`Sector.industries <yfinance.Sector.industries>`
      Map of sector and industry

Sample Code
~~~~~~~~~~~~~~
The `Sector` and `Industry` modules allow you to access the US market information.

To initialize, use the relevant sector or industry key as below.

.. literalinclude:: examples/sector_industry.py
   :language: python

The modules can be chained with Ticker as below.

.. literalinclude:: examples/sector_industry_ticker.py
   :language: python
