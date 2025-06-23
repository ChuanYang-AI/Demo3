"""
酒店服务AI模型微调项目

主要模块：
- data_quality: 数据质量筛选
- utils: 工具函数
"""

__version__ = "1.0.0"
__author__ = "Hotel AI Development Team"

from .data_quality import HotelDataQualityFilter, ProcessingConfig
from .utils import VertexAIManager, setup_logger

__all__ = [
    "HotelDataQualityFilter",
    "ProcessingConfig", 
    "VertexAIManager",
    "setup_logger"
] 