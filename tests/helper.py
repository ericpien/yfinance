from tests.context import yfinance as yf
from tests.context import session_gbl

from yfinance.data import YfData

import inspect
import contextlib
from unittest.mock import patch, Mock
import os
from typing import Union, List, Dict
import json

class MockYfData():  
    def __init__(self):
        self.current_dir = os.path.dirname(__file__)
        self.yf_data = YfData(session=session_gbl)

    def _kwargs_to_params(self, **kwargs) -> Dict:
        params = dict()
        for arg, value in kwargs.items():
            if arg == "actions":
                continue
            
            params[arg] = value
        
        return params

    def _trim_test_name(self, test_name: str) -> str:
        if test_name[:5] == "test_":
            return test_name[5:]

    def _get_mock_data(self, ticker: Union[str, List[str]], test_name: str, function_name: str, **kwargs) -> Mock:
        """Get mock data by loading or fetching."""
        
        test_id = self._trim_test_name(test_name)

        ticker_id = ticker if isinstance(ticker, str) else "_".join(ticker)
        params = self._kwargs_to_params(**kwargs)
        params_str = "_".join(f"{arg}-{value}" for arg, value in sorted(params.items()))
        file_name = f'{test_id.lower()}-{ticker_id.lower()}-{params_str}-{function_name}.json'
        file_path = os.path.join(self.current_dir, '../tests/data/test_prices', file_name)

        if not os.path.exists(file_path):
            self._fetch_and_save_raw_data(ticker, function_name, file_path, **kwargs)

        with open(file_path, 'r') as f:
            response_data = json.load(f)

        # Return the mock response object
        mock_response = Mock()
        mock_response.__class__ = dict
        mock_response.json.return_value = response_data
        mock_response.text = json.dumps(response_data)
        return mock_response

    def _get_call_args(self, ticker, function_name, file_path, **kwargs):
        args, kwargs_actual = None, None

        def raise_on_call(*args, **kwargs):
            raise StopIteration("Exiting patch scope after capturing call args.")
        
        with patch('yfinance.data.YfData.get', side_effect=raise_on_call) as mock_get:
            try:
                if function_name == "history":
                    yf.Ticker(ticker).history(**kwargs)
                elif function_name == "download":
                    yf.download(ticker, **kwargs)
                else:
                    raise ValueError(f"Unsupported function_name: {function_name}")
            except StopIteration:
                pass
            
            args, kwargs_actual = mock_get.call_args
        
        return args, kwargs_actual
    
    def _fetch_and_save_raw_data(self, ticker, function_name, file_path, **kwargs):
        """Fetch raw data using yf.data.get and save it as JSON."""
        try:
            args, kwargs_actual = self._get_call_args(ticker, function_name, file_path, **kwargs)
            response = self.yf_data.get(*args, **kwargs_actual)
            response_data = response.json()
            with open(file_path, 'w') as f:
                json.dump(response_data, f, indent=4)

            return response

        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {ticker}: {str(e)}") from e

    def mock_get(self, ticker, function_name: str, mock_targets = None, **kwargs):
        """Helper to mock and patch YfData.get with saved mock data."""
        if mock_targets is None:
            mock_targets = ['yfinance.data.YfData.get', 'yfinance.data.YfData.cache_get']

        test_name = inspect.stack()[1].function
        mock_response = self._get_mock_data(ticker, test_name, function_name, **kwargs)

        patchers = []
        for target in mock_targets:
            patcher = patch(target, wraps=self.yf_data.get)
            mock_fn = patcher.start()
            mock_fn.return_value = mock_response
            patchers.append(patcher)

        # Return a context manager to manage the patch lifecycle
        @contextlib.contextmanager
        def manage_patchers():
            try:
                yield
            finally:
                for patcher in patchers:
                    patcher.stop()

        return manage_patchers()