from tests.context import yfinance as yf
from tests.context import session_gbl
from tests.helper import MockYfData

import unittest

import datetime as _dt
import pytz as _tz
import numpy as _np
import pandas as _pd

class TestPriceHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = session_gbl
        cls.mock_yf_data = MockYfData()
        cls.mock_get = cls.mock_yf_data.mock_get
        
    @classmethod
    def tearDownClass(cls):
        if cls.session is not None:
            cls.session.close()

    def test_daily_index(self):
        tkrs = ["BHP.AX", "IMP.JO", "BP.L", "PNL.L", "INTC"]
        period = "5y"
        intervals = ["1d", "1wk", "1mo"]
        for tkr in tkrs:
            dat = yf.Ticker(tkr, session=self.session)

            for interval in intervals:
                with self.mock_get(ticker=tkr, function_name="history", period=period, interval=interval):
                    df = dat.history(period=period, interval=interval)

                    f = df.index.time == _dt.time(0)
                    self.assertTrue(f.all())

    def test_download_multi_large_interval(self):
        tkrs = ["BHP.AX", "IMP.JO", "BP.L", "PNL.L", "INTC"]
        period = "5y"
        intervals = ["1d", "1wk", "1mo"]
        for interval in intervals:
            with self.subTest(interval):
                with self.mock_get(ticker=tkrs, function_name="download", period=period, interval=interval):
                    df = yf.download(tkrs, period=period, interval=interval)

                    f = df.index.time == _dt.time(0)
                    self.assertTrue(f.all())

                    df_tkrs = df.columns.levels[1]
                    self.assertEqual(sorted(tkrs), sorted(df_tkrs))

    def test_download_multi_small_interval(self):
        tkrs = ["AAPL", "0Q3.DE", "ATVI"]
        period = "1d"
        interval = "5m"
        with self.mock_get(ticker=tkrs, function_name="download", period=period, interval=interval):
            df = yf.download(tkrs, period=period, interval=interval)
            self.assertEqual(df.index.tz, _dt.timezone.utc)

    def test_download_with_invalid_ticker(self):
        #Checks if using an invalid symbol gives the same output as not using an invalid symbol in combination with a valid symbol (AAPL)
        #Checks to make sure that invalid symbol handling for the date column is the same as the base case (no invalid symbols)

        invalid_tkrs = ["AAPL", "ATVI"] #AAPL exists and ATVI does not exist
        valid_tkrs = ["AAPL", "INTC"] #AAPL and INTC both exist

        start='2023-11-16'
        end='2023-11-17'
        data_invalid_sym, data_valid_sym = None, None
        
        with self.mock_get(ticker=invalid_tkrs, function_name="download", start=start, end=end):
            data_invalid_sym = yf.download(invalid_tkrs, start=start, end=end)
        with self.mock_get(ticker=invalid_tkrs, function_name="download", start=start, end=end):
            data_valid_sym = yf.download(valid_tkrs, start=start, end=end)

        self.assertEqual(data_invalid_sym['Close']['AAPL'][start],data_valid_sym['Close']['AAPL'][start])

    def test_duplicatingHourly(self):
        tkrs = ["IMP.JO", "BHG.JO", "SSW.JO", "BP.L", "INTC"]
        for tkr in tkrs:
            dat = yf.Ticker(tkr, session=self.session)
            tz = dat._get_ticker_tz(proxy=None, timeout=None)

            dt_utc = _pd.Timestamp.utcnow()
            dt = dt_utc.astimezone(_tz.timezone(tz))
            start_d = dt.date() - _dt.timedelta(days=7)
            
            interval="1h"
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, interval=interval):
                df = dat.history(start=start_d, interval=interval)

                dt0 = df.index[-2]
                dt1 = df.index[-1]
                try:
                    self.assertNotEqual(dt0.hour, dt1.hour)
                except AssertionError:
                    print("Ticker = ", tkr)
                    raise

    def test_duplicatingDaily(self):
        tkrs = ["IMP.JO", "BHG.JO", "SSW.JO", "BP.L", "INTC"]
        test_run = False
        for tkr in tkrs:
            dat = yf.Ticker(tkr, session=self.session)
            tz = dat._get_ticker_tz(proxy=None, timeout=None)

            dt_utc = _pd.Timestamp.utcnow()
            dt = dt_utc.astimezone(_tz.timezone(tz))
            if dt.time() < _dt.time(17, 0):
                continue
            test_run = True

            start = start=dt.date() - _dt.timedelta(days=7)
            interval = "1d"
            with self.mock_get(ticker=tkr, function_name="history", start=start, interval=interval):
                df = dat.history(start=start, interval=interval)

                dt0 = df.index[-2]
                dt1 = df.index[-1]
                try:
                    self.assertNotEqual(dt0, dt1)
                except AssertionError:
                    print("Ticker = ", tkr)
                    raise

        if not test_run:
            self.skipTest("Skipping test_duplicatingDaily() because only expected to fail just after market close")

    def test_duplicatingWeekly(self):
        tkrs = ['MSFT', 'IWO', 'VFINX', '^GSPC', 'BTC-USD']
        test_run = False
        for tkr in tkrs:
            dat = yf.Ticker(tkr, session=self.session)
            tz = dat._get_ticker_tz(proxy=None, timeout=None)

            dt = _tz.timezone(tz).localize(_dt.datetime.now())
            if dt.date().weekday() not in [1, 2, 3, 4]:
                continue
            test_run = True

            start = dt.date() - _dt.timedelta(days=7)
            interval = "1wk"
            with self.mock_get(ticker=tkr, function_name="history", start=start, interval=interval):
                df = dat.history(start=start, interval=interval)
                dt0 = df.index[-2]
                dt1 = df.index[-1]
                try:
                    self.assertNotEqual(dt0.week, dt1.week)
                except AssertionError:
                    print("Ticker={}: Last two rows within same week:".format(tkr))
                    print(df.iloc[df.shape[0] - 2:])
                    raise

        if not test_run:
            self.skipTest("Skipping test_duplicatingWeekly() because not possible to fail Monday/weekend")

    def test_pricesEventsMerge(self):
        # Test case: dividend occurs after last row in price data
        tkr = 'INTC'
        start_d = _dt.date(2022, 1, 1)
        end_d = _dt.date(2023, 1, 1)
        interval='1d'
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval):
            dat = yf.Ticker(tkr, session=self.session)
            df = dat.history(interval=interval, start=start_d, end=end_d)
            div = 1.0
            future_div_dt = df.index[-1] + _dt.timedelta(days=1)
            if future_div_dt.weekday() in [5, 6]:
                future_div_dt += _dt.timedelta(days=1) * (7 - future_div_dt.weekday())
            divs = _pd.DataFrame(data={"Dividends":[div]}, index=[future_div_dt])
            df2 = yf.utils.safe_merge_dfs(df.drop(['Dividends', 'Stock Splits'], axis=1), divs, '1d')
            self.assertIn(future_div_dt, df2.index)
            self.assertIn("Dividends", df2.columns)
            self.assertEqual(df2['Dividends'].iloc[-1], div)

    def test_pricesEventsMerge_bug(self):
        # Reproduce exception when merging intraday prices with future dividend
        interval = '30m'
        df_index = []
        d = 13
        for h in range(0, 16):
            for m in [0, 30]:
                df_index.append(_dt.datetime(2023, 9, d, h, m))
        df_index.append(_dt.datetime(2023, 9, d, 16))
        df = _pd.DataFrame(index=df_index)
        df.index = _pd.to_datetime(df.index)
        df['Close'] = 1.0

        div = 1.0
        future_div_dt = _dt.datetime(2023, 9, 14, 10)
        divs = _pd.DataFrame(data={"Dividends":[div]}, index=[future_div_dt])

        yf.utils.safe_merge_dfs(df, divs, interval)
        # No exception = test pass

    def test_intraDayWithEvents(self):
        tkrs = ["BHP.AX", "IMP.JO", "BP.L", "PNL.L", "INTC"]
        for tkr in tkrs:
            start_d = _dt.date.today() - _dt.timedelta(days=59)
            end_d = None
            interval="1d"
            actions=True
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
                df_daily = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=actions)
                df_daily_divs = df_daily["Dividends"][df_daily["Dividends"] != 0]
                if df_daily_divs.shape[0] == 0:
                    continue

                start_d = df_daily_divs.index[0].date()
                end_d = df_daily_divs.index[-1].date() + _dt.timedelta(days=1)
                df_intraday = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval="15m", actions=True)
                self.assertTrue((df_intraday["Dividends"] != 0.0).any())

                df_intraday_divs = df_intraday["Dividends"][df_intraday["Dividends"] != 0]
                df_intraday_divs.index = df_intraday_divs.index.floor('D')
                self.assertTrue(df_daily_divs.equals(df_intraday_divs))

    def test_intraDayWithEvents_tase(self):
        # TASE dividend release pre-market, doesn't merge nicely with intra-day data so check still present

        tase_tkrs = ["ICL.TA", "ESLT.TA", "ONE.TA", "MGDL.TA"]
        for tkr in tase_tkrs:
            start_d = _dt.date.today() - _dt.timedelta(days=59)
            end_d = None
            interval="1d"
            actions=True
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
                df_daily = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=actions)
                df_daily_divs = df_daily["Dividends"][df_daily["Dividends"] != 0]
                if df_daily_divs.shape[0] == 0:
                    continue

                start_d = df_daily_divs.index[0].date()
                end_d = df_daily_divs.index[-1].date() + _dt.timedelta(days=1)
                df_intraday = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval="15m", actions=True)
                self.assertTrue((df_intraday["Dividends"] != 0.0).any())

                df_intraday_divs = df_intraday["Dividends"][df_intraday["Dividends"] != 0]
                df_intraday_divs.index = df_intraday_divs.index.floor('D')
                self.assertTrue(df_daily_divs.equals(df_intraday_divs))

    def test_dailyWithEvents(self):
        start_d = _dt.date(2022, 1, 1)
        end_d = _dt.date(2023, 1, 1)
        interval = "1d"

        tkr_div_dates = {'BHP.AX': [_dt.date(2022, 9, 1), _dt.date(2022, 2, 24)],  # Yahoo claims 23-Feb but wrong because DST
                         'IMP.JO': [_dt.date(2022, 9, 21), _dt.date(2022, 3, 16)],
                         'BP.L': [_dt.date(2022, 11, 10), _dt.date(2022, 8, 11), _dt.date(2022, 5, 12), _dt.date(2022, 2, 17)],
                         'INTC': [_dt.date(2022, 11, 4), _dt.date(2022, 8, 4), _dt.date(2022, 5, 5), _dt.date(2022, 2, 4)]
                        }

        for tkr, dates in tkr_div_dates.items():
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval):
                dat = yf.Ticker(tkr) 
                df = dat.history(interval=interval, start=start_d, end=end_d)
                df_divs = df[df['Dividends'] != 0].sort_index(ascending=False)
                try:
                    self.assertTrue((df_divs.index.date == dates).all())
                except AssertionError:
                    print(f'- ticker = {tkr}')
                    print('- response:')
                    print(df_divs.index.date)
                    print('- answer:')
                    print(dates)
                    raise

    def test_dailyWithEvents_bugs(self):
        # Reproduce issue #521
        tkr1 = "QQQ"
        tkr2 = "GDX"
        start_d = "2014-12-29"
        end_d = "2020-11-29"
        interval = "1d"
        actions=True

        df1, df2 = None, None
        with self.mock_get(ticker=tkr1, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df1 = yf.Ticker(tkr1).history(start=start_d, end=end_d, interval=interval, actions=actions)
        
        with self.mock_get(ticker=tkr2, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df2 = yf.Ticker(tkr2).history(start=start_d, end=end_d, interval=interval, actions=actions)

        self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
        self.assertTrue(((df2["Dividends"] > 0) | (df2["Stock Splits"] > 0)).any())
        try:
            self.assertTrue(df1.index.equals(df2.index))
        except AssertionError:
            missing_from_df1 = df2.index.difference(df1.index)
            missing_from_df2 = df1.index.difference(df2.index)
            print("{} missing these dates: {}".format(tkr1, missing_from_df1))
            print("{} missing these dates: {}".format(tkr2, missing_from_df2))
            raise

        # Test that index same with and without events:
        tkrs = [tkr1, tkr2]
        for tkr in tkrs:
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
                df1 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=actions)
        
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=False):
                df2 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=False)

            self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
            try:
                self.assertTrue(df1.index.equals(df2.index))
            except AssertionError:
                missing_from_df1 = df2.index.difference(df1.index)
                missing_from_df2 = df1.index.difference(df2.index)
                print("{}-with-events missing these dates: {}".format(tkr, missing_from_df1))
                print("{}-without-events missing these dates: {}".format(tkr, missing_from_df2))
                raise

        # Reproduce issue #1634 - 1d dividend out-of-range, should be prepended to prices
        div_dt = _pd.Timestamp(2022, 7, 21).tz_localize("America/New_York")
        df_dividends = _pd.DataFrame(data={"Dividends":[1.0]}, index=[div_dt])
        df_prices = _pd.DataFrame(data={**{c: [1.0] for c in yf.const._PRICE_COLNAMES_}, **{'Volume': 0}}, index=[div_dt+_dt.timedelta(days=1)])
        df_merged = yf.utils.safe_merge_dfs(df_prices, df_dividends, '1d')
        self.assertEqual(df_merged.shape[0], 2)
        self.assertTrue(df_merged[df_prices.columns].iloc[1:].equals(df_prices))
        self.assertEqual(df_merged.index[0], div_dt)

    def test_weeklyWithEvents(self):
        # Reproduce issue #521
        tkr1 = "QQQ"
        tkr2 = "GDX"
        start_d = "2014-12-29"
        end_d = "2020-11-29"
        interval = "1wk"
        actions=True

        df1, df2 = None, None
        with self.mock_get(ticker=tkr1, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df1 = yf.Ticker(tkr1).history(start=start_d, end=end_d, interval=interval, actions=actions)
        with self.mock_get(ticker=tkr2, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df2 = yf.Ticker(tkr2).history(start=start_d, end=end_d, interval=interval, actions=actions)
        self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
        self.assertTrue(((df2["Dividends"] > 0) | (df2["Stock Splits"] > 0)).any())
        try:
            self.assertTrue(df1.index.equals(df2.index))
        except AssertionError:
            missing_from_df1 = df2.index.difference(df1.index)
            missing_from_df2 = df1.index.difference(df2.index)
            print("{} missing these dates: {}".format(tkr1, missing_from_df1))
            print("{} missing these dates: {}".format(tkr2, missing_from_df2))
            raise

        # Test that index same with and without events:
        tkrs = [tkr1, tkr2]
        for tkr in tkrs:
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
                df1 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=actions)
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=False):
                df2 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=False)            
            
            self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
            try:
                self.assertTrue(df1.index.equals(df2.index))
            except AssertionError:
                missing_from_df1 = df2.index.difference(df1.index)
                missing_from_df2 = df1.index.difference(df2.index)
                print("{}-with-events missing these dates: {}".format(tkr, missing_from_df1))
                print("{}-without-events missing these dates: {}".format(tkr, missing_from_df2))
                raise

    def test_monthlyWithEvents(self):
        tkr1 = "QQQ"
        tkr2 = "GDX"
        start_d = "2014-12-29"
        end_d = "2020-11-29"
        interval = "1mo"
        actions = True
        with self.mock_get(ticker=tkr1, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df1 = yf.Ticker(tkr1).history(start=start_d, end=end_d, interval=interval, actions=actions)
        with self.mock_get(ticker=tkr2, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
            df2 = yf.Ticker(tkr2).history(start=start_d, end=end_d, interval=interval, actions=actions)
        self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
        self.assertTrue(((df2["Dividends"] > 0) | (df2["Stock Splits"] > 0)).any())
        try:
            self.assertTrue(df1.index.equals(df2.index))
        except AssertionError:
            missing_from_df1 = df2.index.difference(df1.index)
            missing_from_df2 = df1.index.difference(df2.index)
            print("{} missing these dates: {}".format(tkr1, missing_from_df1))
            print("{} missing these dates: {}".format(tkr2, missing_from_df2))
            raise

        # Test that index same with and without events:
        tkrs = [tkr1, tkr2]
        for tkr in tkrs:
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=actions):
                df1 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=actions)
            with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, actions=False):
                df2 = yf.Ticker(tkr, session=self.session).history(start=start_d, end=end_d, interval=interval, actions=False)     
            
            self.assertTrue(((df1["Dividends"] > 0) | (df1["Stock Splits"] > 0)).any())
            try:
                self.assertTrue(df1.index.equals(df2.index))
            except AssertionError:
                missing_from_df1 = df2.index.difference(df1.index)
                missing_from_df2 = df1.index.difference(df2.index)
                print("{}-with-events missing these dates: {}".format(tkr, missing_from_df1))
                print("{}-without-events missing these dates: {}".format(tkr, missing_from_df2))
                raise

    def test_monthlyWithEvents2(self):
        # Simply check no exception from internal merge
        tkr = "ABBB"
        period = "max"
        dfm, dfd = None, None
        with self.mock_get(ticker=tkr, function_name="history", period=period, interval="1mo"):
            dfm = yf.Ticker(tkr).history(period=period, interval="1mo")
        with self.mock_get(ticker=tkr, function_name="history", period=period, interval="1d"):
            dfd = yf.Ticker(tkr).history(period=period, interval="1d")
        dfd = dfd[dfd.index > dfm.index[0]]
        dfm_divs = dfm[dfm['Dividends'] != 0]
        dfd_divs = dfd[dfd['Dividends'] != 0]
        self.assertEqual(dfm_divs.shape[0], dfd_divs.shape[0])

    def test_tz_dst_ambiguous(self):
        # Reproduce issue #1100
        try:
            with self.mock_get(ticker="ESLT.TA", function_name="history", start="2002-10-06", end="2002-10-09", interval="1d"):
                yf.Ticker("ESLT.TA", session=self.session).history(start="2002-10-06", end="2002-10-09", interval="1d")
        except _tz.exceptions.AmbiguousTimeError:
            raise Exception("Ambiguous DST issue not resolved")

    def test_dst_fix(self):
        # Daily intervals should start at time 00:00. But for some combinations of date and timezone,
        # Yahoo has time off by few hours (e.g. Brazil 23:00 around Jan-2022). Suspect DST problem.
        # The clue is (a) minutes=0 and (b) hour near 0.
        # Obviously Yahoo meant 00:00, so ensure this doesn't affect date conversion.

        # The correction is successful if no days are weekend, and weekly data begins Monday

        tkr = "AGRO3.SA"
        dat = yf.Ticker(tkr, session=self.session)
        start = "2021-01-11"
        end = "2022-11-05"

        interval = "1d"
        with self.mock_get(ticker=tkr, function_name="history", start=start, end=end, interval=interval):
            df = dat.history(start=start, end=end, interval=interval)
            self.assertTrue(((df.index.weekday >= 0) & (df.index.weekday <= 4)).all())

        
        interval = "1wk"
        with self.mock_get(ticker=tkr, function_name="history", start=start, end=end, interval=interval):
            df = dat.history(start=start, end=end, interval=interval)
            try:
                self.assertTrue((df.index.weekday == 0).all())
            except AssertionError:
                print("Weekly data not aligned to Monday")
                raise

    def test_prune_post_intraday_us(self):
        # Half-day at USA Thanksgiving. Yahoo normally
        # returns an interval starting when regular trading closes,
        # even if prepost=False.

        # Setup
        tkr = "AMZN"
        special_day = _dt.date(2023, 11, 24)
        time_early_close = _dt.time(13)
        interval="1h"
        prepost=False
        keepna=True

        dat = yf.Ticker(tkr, session=self.session)

        # Run
        start_d = special_day - _dt.timedelta(days=7)
        end_d = special_day + _dt.timedelta(days=7)
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna):
            df = dat.history(start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna)
            tg_last_dt = df.loc[str(special_day)].index[-1]
            self.assertTrue(tg_last_dt.time() < time_early_close)

        # Test no other afternoons (or mornings) were pruned
        start_d = _dt.date(special_day.year, 1, 1)
        end_d = _dt.date(special_day.year+1, 1, 1)
        
        last_dts, dfd = None, None
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna):
            df = dat.history(start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna)
            last_dts = _pd.Series(df.index).groupby(df.index.date).last()
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval="1d", prepost=prepost, keepna=keepna):
            dfd = dat.history(start=start_d, end=end_d, interval="1d", prepost=prepost, keepna=keepna)
        self.assertTrue(_np.equal(dfd.index.date, _pd.to_datetime(last_dts.index).date).all())

    def test_prune_post_intraday_asx(self):
        # Setup
        tkr = "BHP.AX"
        # No early closes in 2023
        dat = yf.Ticker(tkr, session=self.session)

        # Test no other afternoons (or mornings) were pruned
        start_d = _dt.date(2023, 1, 1)
        end_d = _dt.date(2023+1, 1, 1)
        interval="1h"
        prepost=False
        keepna=True

        last_dts, dfd = None, None
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna):
            df = dat.history(start=start_d, end=end_d, interval=interval, prepost=prepost, keepna=keepna)
            last_dts = _pd.Series(df.index).groupby(df.index.date).last()
        with self.mock_get(ticker=tkr, function_name="history", start=start_d, end=end_d, interval="1d", prepost=prepost, keepna=keepna):
            dfd = dat.history(start=start_d, end=end_d, interval="1d", prepost=prepost, keepna=keepna)
        self.assertTrue(_np.equal(dfd.index.date, _pd.to_datetime(last_dts.index).date).all())

    def test_weekly_2rows_fix(self):
        tkr = "AMZN"
        start = _dt.date.today() - _dt.timedelta(days=14)
        start -= _dt.timedelta(days=start.weekday())

        dat = yf.Ticker(tkr)
        with self.mock_get(ticker=tkr, function_name="history", start=start, interval="1wk"):
            df = dat.history(start=start, interval="1wk")
            self.assertTrue((df.index.weekday == 0).all())

    def test_aggregate_capital_gains(self):
        # Setup
        tkr = "FXAIX"
        dat = yf.Ticker(tkr, session=self.session)
        start = "2017-12-31"
        end = "2019-12-31"
        interval = "3mo"
        
        with self.mock_get(ticker=tkr, function_name="history", start=start, end=end, interval=interval):
            dat.history(start=start, end=end, interval=interval)

if __name__ == '__main__':
    unittest.main()