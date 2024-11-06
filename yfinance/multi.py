#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yfinance - market data downloader
# https://github.com/ranaroussi/yfinance
#
# Copyright 2017-2019 Ran Aroussi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

import logging
import time as _time
import traceback
from typing import Union

import multitasking as _multitasking
import pandas as _pd

from . import Ticker, utils
from .data import YfData
from . import shared


@utils.log_indent_decorator
def download(tickers, start=None, end=None, actions=False, threads=True,
             ignore_tz=None, group_by='column', auto_adjust=False, back_adjust=False,
             repair=False, keepna=False, progress=True, period="max", interval="1d",
             prepost=False, proxy=None, rounding=False, timeout=10, session=None,
             multi_level_index=True) -> Union[_pd.DataFrame, None]:
    """
    Download yahoo tickers

    Args:
        tickers (str or list): List of tickers to download.
        period (str): Time period to download.
            Valid periods are: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'.
            Either use `period` or specify `start` and `end`.
        interval (str): Data interval.
            Valid intervals are: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'.
            Intraday data is limited to the last 60 days.
        start (str): Start date (YYYY-MM-DD) or _datetime, inclusive.
            Default is 99 years ago.
            Example: For `start="2020-01-01"`, the first data point will be "2020-01-01".
        end (str): End date (YYYY-MM-DD) or _datetime, exclusive.
            Default is the current date.
            Example: For `end="2023-01-01"`, the last data point will be "2022-12-31".
        group_by (str): Group data by 'ticker' or 'column'. Default is 'column'.
        prepost (bool): Include pre and post market data in results? Default is False.
        auto_adjust (bool): Automatically adjust all OHLC data? Default is False.
        repair (bool): Detect and repair currency unit mixups (e.g., 100x errors)? Default is False.
        keepna (bool): Keep rows with NaN values returned by Yahoo? Default is False.
        actions (bool): Download dividend and stock split data? Default is False.
        threads (bool or int): Number of threads for mass downloading. Default is True (automatically determines the number of threads).
        ignore_tz (bool): Ignore timezones when combining data across timezones?
            Default depends on the interval. For intraday intervals, the default is False. For daily and above, the default is True.
        proxy (str, optional): URL of the proxy server. Default is None.
        rounding (bool, optional): Round values to two decimal places? Default is False.
        timeout (None or float, optional): Maximum time to wait for a response, in seconds. Can be a fraction of a second (e.g., 0.01). Default is None.
        session (None or Session, optional): Pass a custom session object for all requests. Default is None.
        multi_level_index (bool): Optional. Always return a MultiIndex DataFrame? Default is False

    Returns:
        pd.DataFrame or None
    """
    logger = utils.get_yf_logger()

    if logger.isEnabledFor(logging.DEBUG):
        if threads:
            # With DEBUG, each thread generates a lot of log messages.
            # And with multi-threading, these messages will be interleaved, bad!
            # So disable multi-threading to make log readable.
            logger.debug('Disabling multithreading because DEBUG logging enabled')
            threads = False
        if progress:
            # Disable progress bar, interferes with display of log messages
            progress = False

    if ignore_tz is None:
        # Set default value depending on interval
        if interval[1:] in ['m', 'h']:
            # Intraday
            ignore_tz = False
        else:
            ignore_tz = True

    # create ticker list
    tickers = tickers if isinstance(
        tickers, (list, set, tuple)) else tickers.replace(',', ' ').split()

    # accept isin as ticker
    shared._ISINS = {}
    _tickers_ = []
    for ticker in tickers:
        if utils.is_isin(ticker):
            isin = ticker
            ticker = utils.get_ticker_by_isin(ticker, proxy, session=session)
            shared._ISINS[ticker] = isin
        _tickers_.append(ticker)

    tickers = _tickers_

    tickers = list(set([ticker.upper() for ticker in tickers]))

    if progress:
        shared._PROGRESS_BAR = utils.ProgressBar(len(tickers), 'completed')

    # reset shared._DFS
    shared._DFS = {}
    shared._ERRORS = {}
    shared._TRACEBACKS = {}

    # Ensure data initialised with session.
    YfData(session=session)

    # download using threads
    if threads:
        if threads is True:
            threads = min([len(tickers), _multitasking.cpu_count() * 2])
        _multitasking.set_max_threads(threads)
        for i, ticker in enumerate(tickers):
            _download_one_threaded(ticker, period=period, interval=interval,
                                   start=start, end=end, prepost=prepost,
                                   actions=actions, auto_adjust=auto_adjust,
                                   back_adjust=back_adjust, repair=repair, keepna=keepna,
                                   progress=(progress and i > 0), proxy=proxy,
                                   rounding=rounding, timeout=timeout)
        while len(shared._DFS) < len(tickers):
            _time.sleep(0.01)
    # download synchronously
    else:
        for i, ticker in enumerate(tickers):
            data = _download_one(ticker, period=period, interval=interval,
                                 start=start, end=end, prepost=prepost,
                                 actions=actions, auto_adjust=auto_adjust,
                                 back_adjust=back_adjust, repair=repair, keepna=keepna,
                                 proxy=proxy,
                                 rounding=rounding, timeout=timeout)
            if progress:
                shared._PROGRESS_BAR.animate()

    if progress:
        shared._PROGRESS_BAR.completed()

    if shared._ERRORS:
        # Send errors to logging module
        logger = utils.get_yf_logger()
        logger.error('\n%.f Failed download%s:' % (
            len(shared._ERRORS), 's' if len(shared._ERRORS) > 1 else ''))

        # Log each distinct error once, with list of symbols affected
        errors = {}
        for ticker in shared._ERRORS:
            err = shared._ERRORS[ticker]
            err = err.replace(f'{ticker}', '%ticker%')
            if err not in errors:
                errors[err] = [ticker]
            else:
                errors[err].append(ticker)
        for err in errors.keys():
            logger.error(f'{errors[err]}: ' + err)

        # Log each distinct traceback once, with list of symbols affected
        tbs = {}
        for ticker in shared._TRACEBACKS:
            tb = shared._TRACEBACKS[ticker]
            tb = tb.replace(f'{ticker}', '%ticker%')
            if tb not in tbs:
                tbs[tb] = [ticker]
            else:
                tbs[tb].append(ticker)
        for tb in tbs.keys():
            logger.debug(f'{tbs[tb]}: ' + tb)

    if ignore_tz:
        for tkr in shared._DFS.keys():
            if (shared._DFS[tkr] is not None) and (shared._DFS[tkr].shape[0] > 0):
                shared._DFS[tkr].index = shared._DFS[tkr].index.tz_localize(None)

    try:
        data = _pd.concat(shared._DFS.values(), axis=1, sort=True,
                          keys=shared._DFS.keys(), names=['Ticker', 'Price'])
    except Exception:
        _realign_dfs()
        data = _pd.concat(shared._DFS.values(), axis=1, sort=True,
                          keys=shared._DFS.keys(), names=['Ticker', 'Price'])
    data.index = _pd.to_datetime(data.index, utc=True)
    # switch names back to isins if applicable
    data.rename(columns=shared._ISINS, inplace=True)

    if group_by == 'column':
        data.columns = data.columns.swaplevel(0, 1)
        data.sort_index(level=0, axis=1, inplace=True)

    if not multi_level_index and len(tickers) == 1:
        data = data.droplevel(0 if group_by == 'ticker' else 1, axis=1).rename_axis(None, axis=1)

    return data


def _realign_dfs():
    idx_len = 0
    idx = None

    for df in shared._DFS.values():
        if len(df) > idx_len:
            idx_len = len(df)
            idx = df.index

    for key in shared._DFS.keys():
        try:
            shared._DFS[key] = _pd.DataFrame(
                index=idx, data=shared._DFS[key]).drop_duplicates()
        except Exception:
            shared._DFS[key] = _pd.concat([
                utils.empty_df(idx), shared._DFS[key].dropna()
            ], axis=0, sort=True)

        # remove duplicate index
        shared._DFS[key] = shared._DFS[key].loc[
            ~shared._DFS[key].index.duplicated(keep='last')]


@_multitasking.task
def _download_one_threaded(ticker, start=None, end=None,
                           auto_adjust=False, back_adjust=False, repair=False,
                           actions=False, progress=True, period="max",
                           interval="1d", prepost=False, proxy=None,
                           keepna=False, rounding=False, timeout=10):
    _download_one(ticker, start, end, auto_adjust, back_adjust, repair,
                         actions, period, interval, prepost, proxy, rounding,
                         keepna, timeout)
    if progress:
        shared._PROGRESS_BAR.animate()


def _download_one(ticker, start=None, end=None,
                  auto_adjust=False, back_adjust=False, repair=False,
                  actions=False, period="max", interval="1d",
                  prepost=False, proxy=None, rounding=False,
                  keepna=False, timeout=10):
    data = None
    try:
        data = Ticker(ticker).history(
                period=period, interval=interval,
                start=start, end=end, prepost=prepost,
                actions=actions, auto_adjust=auto_adjust,
                back_adjust=back_adjust, repair=repair, proxy=proxy,
                rounding=rounding, keepna=keepna, timeout=timeout,
                raise_errors=True
        )
    except Exception as e:
        # glob try/except needed as current thead implementation breaks if exception is raised.
        shared._DFS[ticker.upper()] = utils.empty_df()
        shared._ERRORS[ticker.upper()] = repr(e)
        shared._TRACEBACKS[ticker.upper()] = traceback.format_exc()
    else:
        shared._DFS[ticker.upper()] = data

    return data
