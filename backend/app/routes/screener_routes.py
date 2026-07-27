"""网格标的筛选器路由

GET /api/screener            批量评估候选池并按适宜度排序返回（同步，~18s，结果缓存1小时）
GET /api/screener?refresh=1  强制忽略缓存重新评估
GET /api/screener/candidates 仅返回候选池清单（不评分）
"""

from flask import Blueprint, request, jsonify

from app.services.screener_service import ScreenerService
from app.services.ma_screener_service import MAScreenerService
from app.services.fish_basin_service import FishBasinService, FISH_BASIN_INDICES, FISH_BASIN_SECTORS
from app.constants import (
    SCREENER_CANDIDATES, HTTP_OK, HTTP_INTERNAL_SERVER_ERROR, HTTP_BAD_REQUEST
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('screener_routes', __name__)

_service = ScreenerService()
_ma_service = MAScreenerService()
_fish_basin_service = FishBasinService()


@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def run_screener():
    """批量筛选适合网格交易的标的。"""
    try:
        force = request.args.get('refresh') in ('1', 'true', 'yes')
        payload = _service.screen(SCREENER_CANDIDATES, force_refresh=force)
        return jsonify({'success': True, 'data': payload}), HTTP_OK
    except Exception as e:
        logger.error(f"筛选执行失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': '筛选执行失败，请稍后重试'}), HTTP_INTERNAL_SERVER_ERROR


@bp.route('/candidates', methods=['GET'])
def list_candidates():
    """返回候选池清单。"""
    return jsonify({'success': True, 'data': SCREENER_CANDIDATES}), HTTP_OK


@bp.route('/ma', methods=['GET'])
def run_ma_screener():
    """均线策略批量筛选：对候选池每只标的用同一组均线参数回测，按超额收益排序。

    Query 参数：
      period: 均线周期（默认20）
      maType: SMA|EMA（默认SMA）
      capital: 投资金额（默认100000）
      refresh: 1 强制重算
    """
    try:
        try:
            period = int(request.args.get('period', 20))
        except (TypeError, ValueError):
            period = 20
        if period < 2 or period > 500:
            return jsonify({'success': False, 'message': '均线周期应在2-500之间'}), HTTP_BAD_REQUEST

        ma_type = (request.args.get('maType', 'SMA') or 'SMA').upper()
        if ma_type not in ('SMA', 'EMA'):
            ma_type = 'SMA'
        try:
            capital = float(request.args.get('capital', 100000))
        except (TypeError, ValueError):
            capital = 100000.0

        force = request.args.get('refresh') in ('1', 'true', 'yes')
        start_date = (request.args.get('startDate', '') or '').strip()
        end_date = (request.args.get('endDate', '') or '').strip()
        payload = _ma_service.screen(
            SCREENER_CANDIDATES, period=period, ma_type=ma_type,
            total_capital=capital,
            start_date=start_date, end_date=end_date, force_refresh=force,
        )
        return jsonify({'success': True, 'data': payload}), HTTP_OK
    except Exception as e:
        logger.error(f"均线筛选执行失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': '均线筛选执行失败，请稍后重试'}), HTTP_INTERNAL_SERVER_ERROR


@bp.route('/fish-basin', methods=['GET'])
def run_fish_basin():
    """鱼盆模型（市场风向标）：对主流宽基指数以20日线为临界值判断 YES/NO + 趋势强度。

    Query 参数：
      buffer: 临界值上下浮动百分比（默认0=纯20日线，可填 1~3）
      refresh: 1 强制重算
    """
    try:
        try:
            buffer_pct = float(request.args.get('buffer', 0))
        except (TypeError, ValueError):
            buffer_pct = 0.0
        # 合理区间限制：-5% ~ +5%
        buffer_pct = max(-5.0, min(5.0, buffer_pct))
        force = request.args.get('refresh') in ('1', 'true', 'yes')
        board = (request.args.get('board', 'index') or 'index').strip().lower()
        if board == 'sector':
            indices = FISH_BASIN_SECTORS
        else:
            board = 'index'
            indices = FISH_BASIN_INDICES
        payload = _fish_basin_service.evaluate(
            indices, buffer_pct=buffer_pct, force_refresh=force, board=board
        )
        return jsonify({'success': True, 'data': payload}), HTTP_OK
    except Exception as e:
        logger.error(f"鱼盆模型执行失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': '鱼盆模型执行失败，请稍后重试'}), HTTP_INTERNAL_SERVER_ERROR
