"""
数据服务回测相关功能单元测试
"""

import pytest
from unittest.mock import Mock, patch
from app.services.data_service import DataService
from app.algorithms.backtest.models import KBar
from datetime import datetime


@pytest.fixture
def data_service():
    return DataService()


def test_get_5min_kline_etf(data_service):
    """测试获取ETF 5分钟K线数据"""
    mock_data = [
        {
            'date': '2025-01-10 09:30:00',
            'open': 3.500,
            'high': 3.510,
            'low': 3.490,
            'close': 3.505,
            'volume': 10000
        },
        {
            'date': '2025-01-10 09:35:00',
            'open': 3.505,
            'high': 3.520,
            'low': 3.500,
            'close': 3.515,
            'volume': 12000
        }
    ]

    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_etf_5min', return_value=mock_response):
        result = data_service.get_5min_kline('510300', 'SSE', '2025-01-10', '2025-01-10')

        assert len(result) == 2
        assert isinstance(result[0], KBar)
        assert result[0].time == datetime(2025, 1, 10, 9, 30)
        assert result[0].open == 3.500
        assert result[0].high == 3.510
        assert result[0].low == 3.490
        assert result[0].close == 3.505
        assert result[0].volume == 10000


def test_get_5min_kline_stock(data_service):
    """测试获取股票5分钟K线数据"""
    mock_data = [
        {
            'date': '2025-01-10 09:30:00',
            'open': 10.00,
            'high': 10.10,
            'low': 9.90,
            'close': 10.05,
            'volume': 5000
        }
    ]

    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_stock_5min', return_value=mock_response):
        result = data_service.get_5min_kline('000001', 'SZSE', '2025-01-10', '2025-01-10')

        assert len(result) == 1
        assert isinstance(result[0], KBar)
        assert result[0].time == datetime(2025, 1, 10, 9, 30)
        assert result[0].open == 10.00


def test_get_trading_calendar(data_service):
    """测试获取交易日历"""
    mock_data = [
        {'date': '2025-01-16'},
        {'date': '2025-01-15'},
        {'date': '2025-01-14'},
        {'date': '2025-01-13'},
        {'date': '2025-01-10'}
    ]

    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_calendar', return_value=mock_response):
        result = data_service.get_trading_calendar('SSE', 5)

        assert len(result) == 5
        assert result[0] == '2025-01-16'
        assert result[1] == '2025-01-15'
        assert result[4] == '2025-01-10'


def test_get_5min_kline_empty_data(data_service):
    """测试空数据情况"""
    mock_response = {'code': 200, 'data': []}
    with patch.object(data_service.provider, 'get_etf_5min', return_value=mock_response):
        result = data_service.get_5min_kline('510300', 'SSE', '2025-01-10', '2025-01-10')

        assert result == []


def test_get_trading_calendar_empty_data(data_service):
    """测试交易日历空数据"""
    mock_response = {'code': 200, 'data': []}
    with patch.object(data_service.provider, 'get_calendar', return_value=mock_response):
        result = data_service.get_trading_calendar('SSE', 5)

        assert result == []