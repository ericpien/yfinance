********************
Installation Guide
********************

Install `yfinance` using `pip`:

.. code-block:: bash

   $ pip install yfinance --upgrade --no-cache-dir

You can also install using Conda:

.. code-block:: bash

   $ conda install -c ranaroussi yfinance

To install with optional dependencies, replace `optional` with: `nospam` for smarter scraping, `repair` for price repair, or `nospam,repair` for both:

.. code-block:: bash

   $ pip install "yfinance[optional]"

For required dependencies, check out the `requirements file <./requirements.txt>`_, and for all dependencies, see the `setup.py file <./setup.py#L62>`_.
