=======================
Sector and Industry
=======================

.. contents::
   :depth: 2
   :local:

Sector Class
--------------

.. autoclass:: yfinance.Sector
   :members:
   :undoc-members:
   :show-inheritance:

The `Sector` class provides access to US sector-level data.

Industry Class
--------------

.. autoclass:: yfinance.Industry
   :members:
   :undoc-members:
   :show-inheritance:

The `Industry` class provides access to US industry-level data.


Domain
--------------

Domain Abstract Class

.. autoclass:: yfinance.domain.domain.Domain
   :members:
   :undoc-members:
   :show-inheritance:


Sample Code
------------------
The `Sector` and `Industry` modules allow you to access the US market information.

To initialize, use the relevant sector or industry key as below. (Complete mapping of the keys is available in `const.py`.)

.. literalinclude:: examples/sector_industry.py
   :language: python

The modules can be chained with Ticker as below.

.. literalinclude:: examples/sector_industry_ticker.py
   :language: python
