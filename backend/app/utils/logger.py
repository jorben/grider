"""
日志配置模块
支持JSON和TEXT两种格式，支持文件和控制台输出
"""
import os
import sys
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """JSON格式化器，输出结构化日志"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加额外的上下文信息
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式化器，输出人类可读的日志"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logger(app):
    """
    配置Flask应用的logger
    
    Args:
        app: Flask应用实例
    """
    # 从环境变量读取配置
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = os.getenv('LOG_DIR', 'logs')
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '30'))
    log_to_console = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
    
    # 设置日志级别
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # 配置app.logger
    app.logger.setLevel(numeric_level)
    app.logger.handlers.clear()
    
    # 同时配置root logger，这样通过get_logger()获取的logger也能正常工作
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # 屏蔽werkzeug的低级别日志
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    # 选择格式化器
    if log_format == 'json':
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()
    
    # 配置文件处理器
    if log_dir:
        # 确保日志目录存在
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件路径
        log_file = log_path / 'app.log'
        
        # 使用TimedRotatingFileHandler按天轮转日志
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # 设置日志文件名后缀
        file_handler.suffix = '%Y-%m-%d.log'
        
        app.logger.addHandler(file_handler)
        root_logger.addHandler(file_handler)
    
    # 配置控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)
        root_logger.addHandler(console_handler)
    
    # 防止app.logger传播到root logger（避免重复输出）
    app.logger.propagate = False
    
    # 记录日志配置信息
    app.logger.info(
        f'日志系统已初始化 - 级别: {log_level}, 格式: {log_format}, '
        f'目录: {log_dir}, 控制台输出: {log_to_console}'
    )
    
    return app.logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger
    
    Args:
        name: logger名称
        
    Returns:
        logging.Logger实例
    
    注意：这个函数返回的logger会继承root logger的配置
    确保在调用此函数前已经通过setup_logger配置了日志系统
    """
    logger = logging.getLogger(name)
    # 如果logger没有handlers，它会使用root logger的handlers
    # 如果logger的level是NOTSET，它会使用root logger的level
    return logger