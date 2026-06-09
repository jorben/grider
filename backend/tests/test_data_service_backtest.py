"""
数据服务相关功能单元测试

覆盖：
- DataService 各业务方法的返回值结构与边界行为
- ``TickFlowProvider`` 通过 ``patch.object`` 替换为 mock，避免真实网络调用
- 日历、5 分钟 K 线、日线、最新价、模糊搜索等接口
"""

import pytest
from unittest.mock import patch
from app.services.data_service import DataService
from app.algorithms.backtest.models import KBar
from datetime import datetime


@pytest.fixture
def data_service():
    return DataService()


def test_get_5min_kline_etf(data_service):
    """测试获取ETF 5分钟K线数据。"""
    mock_data = [
        {
            'date': '2025-01-10 09:30:00',
            'open': 3.500,
            'high': 3.510,
            'low': 3.490,
            'close': 3.505,
            'volume': 10000,
        },
        {
            'date': '2025-01-10 09:35:00',
            'open': 3.505,
            'high': 3.520,
            'low': 3.500,
            'close': 3.515,
            'volume': 12000,
        },
    ]

    mock_response = {'code': 200, 'data': mock_data}
    # 510300 + XSHG 会被转换为 510300.SH
    with patch.object(data_service.provider, 'get_5min', return_value=mock_response) as mock_call:
        result = data_service.get_5min_kline('510300', 'XSHG', '2025-01-10', '2025-01-10')

        # 确认 provider 收到的是 TickFlow 格式 symbol（provider 签名：get_5min(symbol, start_date, end_date, adjust)）
        mock_call.assert_called_once()
        args, _ = mock_call.call_args
        assert args[0] == '510300.SH'
        assert args[1] == '2025-01-10'
        assert args[2] == '2025-01-10'

        assert len(result) == 2
        assert isinstance(result[0], KBar)
        assert result[0].time == datetime(2025, 1, 10, 9, 30)
        assert result[0].open == 3.500
        assert result[0].high == 3.510
        assert result[0].low == 3.490
        assert result[0].close == 3.505
        assert result[0].volume == 10000


def test_get_5min_kline_stock(data_service):
    """测试获取股票5分钟K线数据，验证 SSE/SH/SZSE 等交易所别名归一化。"""
    mock_data = [
        {
            'date': '2025-01-10 09:30:00',
            'open': 10.00,
            'high': 10.10,
            'low': 9.90,
            'close': 10.05,
            'volume': 5000,
        }
    ]

    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_5min', return_value=mock_response) as mock_call:
        result = data_service.get_5min_kline('000001', 'SZSE', '2025-01-10', '2025-01-10')

        args, _ = mock_call.call_args
        assert args[0] == '000001.SZ'

        assert len(result) == 1
        assert isinstance(result[0], KBar)
        assert result[0].time == datetime(2025, 1, 10, 9, 30)
        assert result[0].open == 10.00


def test_get_trading_calendar(data_service):
    """测试交易日历：DataService 调用 provider.get_calendar 并展开 date 字段。"""
    mock_data = [
        {'date': '2025-01-16'},
        {'date': '2025-01-15'},
        {'date': '2025-01-14'},
        {'date': '2025-01-13'},
        {'date': '2025-01-10'},
    ]

    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_calendar', return_value=mock_response) as mock_call:
        result = data_service.get_trading_calendar('SSE', 5)

        # 验证参数透传
        mock_call.assert_called_once()
        kwargs = mock_call.call_args.kwargs
        assert kwargs['exchange_code'] == 'SSE'
        assert kwargs['limit'] == 5

        assert len(result) == 5
        assert result[0] == '2025-01-16'
        assert result[1] == '2025-01-15'
        assert result[4] == '2025-01-10'


def test_get_5min_kline_empty_data(data_service):
    """测试空数据情况。"""
    mock_response = {'code': 200, 'data': []}
    with patch.object(data_service.provider, 'get_5min', return_value=mock_response):
        result = data_service.get_5min_kline('510300', 'SSE', '2025-01-10', '2025-01-10')

        assert result == []


def test_get_trading_calendar_empty_data(data_service):
    """测试交易日历空数据。"""
    mock_response = {'code': 200, 'data': []}
    with patch.object(data_service.provider, 'get_calendar', return_value=mock_response):
        result = data_service.get_trading_calendar('SSE', 5)

        assert result == []


def test_get_5min_kline_skips_invalid_rows(data_service):
    """测试遇到非法行（如缺字段、值不可解析）时跳过而不抛出。"""
    mock_data = [
        {
            'date': '2025-01-10 09:30:00',
            'open': 'bad-value',  # 不可转 float
            'high': 3.510,
            'low': 3.490,
            'close': 3.505,
            'volume': 10000,
        },
        {
            'date': '2025-01-10 09:35:00',
            'open': 3.505,
            'high': 3.520,
            'low': 3.500,
            'close': 3.515,
            'volume': 12000,
        },
    ]
    mock_response = {'code': 200, 'data': mock_data}
    with patch.object(data_service.provider, 'get_5min', return_value=mock_response):
        result = data_service.get_5min_kline('510300', 'SSE', '2025-01-10', '2025-01-10')

        # 非法行被跳过，只剩一条
        assert len(result) == 1
        assert result[0].close == 3.515


def test_get_daily_data_returns_dataframe(data_service):
    """日线数据返回 DataFrame，amount 缺失时按 OHLC+volume 估算。"""
    rows = [
        {'date': '2025-01-10', 'open': 3.5, 'high': 3.55, 'low': 3.45, 'close': 3.50, 'volume': 1000},
        {'date': '2025-01-09', 'open': 3.4, 'high': 3.5, 'low': 3.35, 'close': 3.45, 'volume': 1200, 'amount': 4180.0},
    ]
    with patch.object(data_service.provider, 'get_daily', return_value={'code': 200, 'data': rows}):
        df = data_service.get_daily_data('510300', 'XSHG', 'STOCK', '2025-01-09', '2025-01-10')

    assert df is not None
    assert len(df) == 2
    # 第一行 amount 应被估算补齐
    expected = ((3.5 + 3.55 + 3.45 + 3.50) / 4) * 1000
    assert float(df.iloc[0]['amount']) == pytest.approx(expected, rel=1e-6)
    # 第二行 amount 保持原值
    assert float(df.iloc[1]['amount']) == pytest.approx(4180.0, rel=1e-6)


def test_get_latest_price_returns_normalized_row(data_service):
    """最新价：mock 返回 provider 已标准化后的行（close / pre_close / change_pct / date）。"""
    normalized = {
        'symbol': '510300.SH',
        'ticker': '510300',
        'exchange_code': 'XSHG',
        'name': '沪深300ETF',
        'date': '2025-01-10 15:00:00',
        'open': 3.5,
        'high': 3.65,
        'low': 3.48,
        'close': 3.6,
        'pre_close': 3.5,
        'volume': 10000,
        'amount': None,  # 测试 amount 估算
        'change_pct': 2.857,
    }
    with patch.object(data_service.provider, 'get_realtime', return_value={'code': 200, 'data': [normalized]}) as mock_call:
        row = data_service.get_latest_price('510300', 'XSHG', 'ETF')

    # provider 收到的 symbol 必须是 TickFlow 格式
    args, _ = mock_call.call_args
    assert args[0] == '510300.SH'

    assert row is not None
    assert row['ticker'] == '510300'
    assert row['exchange_code'] == 'XSHG'
    assert row['type'] == 'ETF'
    assert row['change_pct'] == pytest.approx(2.857, rel=1e-2)
    # amount 估算：((3.5+3.6+3.65+3.48)/4) * 10000 = 35575.0
    assert row['amount'] == pytest.approx(35575.0, rel=1e-6)


def test_search_by_ticker_returns_first_match(data_service):
    """搜索：返回首条匹配且包含兼容字段。"""
    search_resp = {
        'code': 200,
        'data': [
            {'ticker': '510300', 'symbol': '510300.SH', 'exchange_code': 'XSHG',
             'name': '', 'type': 'ETF'},
            {'ticker': '510500', 'symbol': '510500.SH', 'exchange_code': 'XSHG',
             'name': '', 'type': 'ETF'},
        ],
    }
    with patch.object(data_service.provider, 'search_by_ticker', return_value=search_resp):
        first = data_service.search_by_ticker('510', 'CHN')

    assert first is not None
    assert first['ticker'] == '510300'
    assert first['exchange_code'] == 'XSHG'
    assert first['type'] == 'ETF'
    assert first['symbol'] == '510300.SH'


def test_search_by_ticker_no_match(data_service):
    """搜索无结果时返回 None。"""
    with patch.object(data_service.provider, 'search_by_ticker', return_value={'code': 200, 'data': []}):
        assert data_service.search_by_ticker('999999', 'CHN') is None
