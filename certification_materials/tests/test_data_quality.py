#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量模块测试
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_quality.rules import DataQualityRules, FilterStats, ProcessingConfig


class TestDataQualityRules(unittest.TestCase):
    """测试数据质量规则"""
    
    def test_validate_entry_valid(self):
        """测试有效数据条目验证"""
        entry = {
            "contents": [
                {"parts": [{"text": "酒店的早餐时间是什么时候？"}]},
                {"parts": [{"text": "我们酒店的早餐供应时间是每天早上6:30到10:00，周末延长到10:30。早餐在一楼餐厅提供，包含中西式各种选择。"}]}
            ]
        }
        
        is_valid, reason, stats = DataQualityRules.validate_entry(entry)
        
        self.assertTrue(is_valid)
        self.assertIn("通过规则检查", reason)
        self.assertTrue(stats.has_question_mark)
        self.assertTrue(stats.is_hotel_related)
        self.assertIn("酒店", stats.hotel_keywords_found)
    
    def test_validate_entry_no_question_mark(self):
        """测试缺少疑问标记的数据条目"""
        entry = {
            "contents": [
                {"parts": [{"text": "酒店的早餐时间"}]},
                {"parts": [{"text": "我们酒店的早餐供应时间是每天早上6:30到10:00，包含中西式各种选择。"}]}
            ]
        }
        
        is_valid, reason, stats = DataQualityRules.validate_entry(entry)
        
        # 缺少疑问标记是一个问题，但与酒店相关，所以应该不通过（因为有超过1个问题）
        self.assertFalse(is_valid)
        self.assertFalse(stats.has_question_mark)
        self.assertTrue(stats.is_hotel_related)
        self.assertIn("问题缺少疑问标记", reason)
    
    def test_validate_entry_not_hotel_related(self):
        """测试与酒店无关的数据条目"""
        entry = {
            "contents": [
                {"parts": [{"text": "今天天气怎么样？"}]},
                {"parts": [{"text": "今天天气晴朗，温度适宜，是个出门的好日子。"}]}
            ]
        }
        
        is_valid, reason, stats = DataQualityRules.validate_entry(entry)
        
        self.assertFalse(is_valid)
        self.assertIn("与酒店服务不相关", reason)
        self.assertFalse(stats.is_hotel_related)
        self.assertEqual(len(stats.hotel_keywords_found), 0)
    
    def test_validate_entry_too_short(self):
        """测试内容过短的数据条目"""
        entry = {
            "contents": [
                {"parts": [{"text": "好？"}]},
                {"parts": [{"text": "好的"}]}
            ]
        }
        
        is_valid, reason, stats = DataQualityRules.validate_entry(entry)
        
        self.assertFalse(is_valid)
        self.assertIn("问题长度异常", reason)
        self.assertIn("回答长度异常", reason)
    
    def test_validate_entry_hotel_related_with_question_mark(self):
        """测试与酒店相关且有疑问标记的数据条目（应该通过）"""
        entry = {
            "contents": [
                {"parts": [{"text": "客房服务怎么样？"}]},
                {"parts": [{"text": "我们的客房服务非常专业，24小时为您提供贴心服务，包括清洁、维修、送餐等各种需求。"}]}
            ]
        }
        
        is_valid, reason, stats = DataQualityRules.validate_entry(entry)
        
        self.assertTrue(is_valid)
        self.assertTrue(stats.has_question_mark)
        self.assertTrue(stats.is_hotel_related)
        self.assertIn("客房", stats.hotel_keywords_found)
        self.assertIn("服务", stats.hotel_keywords_found)
    
    def test_processing_config_defaults(self):
        """测试处理配置默认值"""
        config = ProcessingConfig()
        
        self.assertEqual(config.min_score, 7)
        self.assertEqual(config.batch_size, 12)
        self.assertEqual(config.max_workers, 6)
        self.assertIsNone(config.sample_size)
    
    def test_processing_config_custom(self):
        """测试自定义处理配置"""
        config = ProcessingConfig(
            min_score=8,
            batch_size=10,
            max_workers=4,
            sample_size=100
        )
        
        self.assertEqual(config.min_score, 8)
        self.assertEqual(config.batch_size, 10)
        self.assertEqual(config.max_workers, 4)
        self.assertEqual(config.sample_size, 100)


class TestFilterStats(unittest.TestCase):
    """测试筛选统计信息"""
    
    def test_filter_stats_creation(self):
        """测试筛选统计信息创建"""
        stats = FilterStats(
            question_length=20,
            answer_length=100,
            has_question_mark=True,
            is_hotel_related=True,
            hotel_keywords_found=["酒店", "客房"]
        )
        
        self.assertEqual(stats.question_length, 20)
        self.assertEqual(stats.answer_length, 100)
        self.assertTrue(stats.has_question_mark)
        self.assertTrue(stats.is_hotel_related)
        self.assertEqual(len(stats.hotel_keywords_found), 2)


if __name__ == "__main__":
    unittest.main() 