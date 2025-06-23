#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块

提供统一的日志配置和管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "hotel_ai", 
                level: str = "INFO",
                log_file: Optional[str] = None,
                format_string: Optional[str] = None) -> logging.Logger:
    """
    设置并配置日志器
    
    Args:
        name: 日志器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则只输出到控制台
        format_string: 自定义日志格式
        
    Returns:
        配置好的日志器
    """
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 设置日志格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class ProgressLogger:
    """进度日志器"""
    
    def __init__(self, logger: logging.Logger, total: int, 
                 prefix: str = "进度", update_interval: int = 100):
        """
        初始化进度日志器
        
        Args:
            logger: 日志器实例
            total: 总数量
            prefix: 日志前缀
            update_interval: 更新间隔
        """
        self.logger = logger
        self.total = total
        self.prefix = prefix
        self.update_interval = update_interval
        self.current = 0
        self.last_reported = 0
    
    def update(self, count: int = 1):
        """更新进度"""
        self.current += count
        
        # 检查是否需要报告进度
        if (self.current - self.last_reported >= self.update_interval or 
            self.current >= self.total):
            
            percentage = (self.current / self.total) * 100
            self.logger.info(f"{self.prefix}: {self.current}/{self.total} ({percentage:.1f}%)")
            self.last_reported = self.current
    
    def finish(self):
        """完成进度记录"""
        if self.current < self.total:
            self.current = self.total
        
        self.logger.info(f"{self.prefix}完成: {self.total}/{self.total} (100.0%)") 