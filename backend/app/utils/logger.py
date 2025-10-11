"""
日志配置模块
支持JSON和TEXT两种格式，支持文件和控制台输出
"""
import os
import sys
import json
import logging
import time
import shutil
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """JSON格式化器，输出结构化日志"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.now().astimezone().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': str(record.getMessage()),
        }
        
        # 添加异常信息
        if record.exc_info:
            try:
                log_data['exception'] = self.formatException(record.exc_info)
            except Exception:
                log_data['exception'] = 'Failed to format exception'
        
        # 添加所有的extra字段（除了标准LogRecord属性）
        # 标准LogRecord属性列表
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName'
        }
        
        # 遍历record的所有属性，添加非标准属性到log_data
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value
             
        try:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            # 如果序列化失败，移除可能导致问题的额外字段
            filtered_data = {k: v for k, v in log_data.items()
                           if k in ['timestamp', 'level', 'logger', 'module', 'function', 'line', 'message']}
            if 'exception' in log_data:
                filtered_data['exception'] = log_data['exception']
            return json.dumps(filtered_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """文本格式化器，输出人类可读的日志"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    安全的时间轮转文件处理器，解决Windows文件锁定问题
    使用复制+截断策略替代移动策略
    """
    
    def doRollover(self):
        """
        执行日志轮转
        重写父类方法，使用复制+截断策略避免Windows文件锁定问题
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # 获取轮转时间
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        
        # 生成备份文件名 - 格式：app.日期.log
        base_dir = os.path.dirname(self.baseFilename)
        base_name = os.path.basename(self.baseFilename)
        # 移除 .log 扩展名
        if base_name.endswith('.log'):
            base_name = base_name[:-4]
        # 构建新文件名：基础名.日期.log
        dfn = self.rotation_filename(
            os.path.join(
                base_dir,
                f"{base_name}.{time.strftime(self.suffix, timeTuple)}.log"
            )
        )
        
        # 如果备份文件已存在，删除它
        if os.path.exists(dfn):
            os.remove(dfn)
        
        # 复制当前日志文件到备份文件
        if os.path.exists(self.baseFilename):
            try:
                shutil.copy2(self.baseFilename, dfn)
                # 截断原文件
                with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                    pass
            except Exception as e:
                # 如果复制失败，记录错误但继续
                print(f"日志轮转失败: {e}", file=sys.stderr)
        
        # 删除过期的备份文件
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        
        # 重新打开日志文件
        if not self.delay:
            self.stream = self._open()
        
        # 计算下次轮转时间
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        
        # 如果是夏令时，调整时间
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:
                    addend = -3600
                else:
                    addend = 3600
                newRolloverAt += addend
        
        self.rolloverAt = newRolloverAt


def setup_logger(app):
    """
    配置Flask应用的logger
    
    Args:
        app: Flask应用实例
    """
    # 防止重复初始化
    if hasattr(app, '_logger_initialized'):
        return app.logger
    
    app._logger_initialized = True
    # 从环境变量读取配置
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = os.getenv('LOG_DIR', 'logs')
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    # 验证日志格式是否有效
    if log_format not in ['json', 'text']:
        log_format = 'json'
    try:
        log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '30'))
    except (ValueError, TypeError):
        log_backup_count = 30
    log_to_console = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
    
    # 验证日志级别是否有效
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        log_level = 'INFO'
    
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
        try:
            log_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            app.logger.error(f'无法创建日志目录 {log_dir}: {e}')
            log_dir = None
        
        if log_dir:
            # 创建日志文件路径
            log_file = log_path / 'app.log'

            try:
                # 使用SafeTimedRotatingFileHandler按天轮转日志
                file_handler = SafeTimedRotatingFileHandler(
                    filename=str(log_file),
                    when='midnight',
                    interval=1,
                    backupCount=log_backup_count,
                    encoding='utf-8',
                    delay=False  # 不延迟打开，确保文件立即创建
                )
                file_handler.setLevel(numeric_level)
                file_handler.setFormatter(formatter)

                # 设置日志文件名后缀
                file_handler.suffix = '%Y-%m-%d'

                # 使用同一个handler，避免多个handler同时轮转同一个文件
                app.logger.addHandler(file_handler)
                root_logger.addHandler(file_handler)
            except (OSError, PermissionError) as e:
                app.logger.error(f'无法创建日志文件 {log_file}: {e}')
    
    # 配置控制台处理器
    if log_to_console:
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            app.logger.addHandler(console_handler)
            root_logger.addHandler(console_handler)
        except Exception as e:
            app.logger.error(f'无法创建控制台日志处理器: {e}')
    
    # 防止app.logger传播到root logger（避免重复输出）
    app.logger.propagate = False
    
    # 记录日志配置信息
    try:
        app.logger.info(
            f'日志系统已初始化 - 级别: {log_level}, 格式: {log_format}, '
            f'目录: {log_dir}, 控制台输出: {log_to_console}'
        )
    except Exception:
        # 如果日志记录失败，使用print作为后备
        print(
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
    if not name or not isinstance(name, str):
        name = 'default'
    
    logger = logging.getLogger(name)
    # 如果logger没有handlers，它会使用root logger的handlers
    # 如果logger的level是NOTSET，它会使用root logger的level
    return logger