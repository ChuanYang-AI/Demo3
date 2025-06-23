#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量规则模块

定义数据质量验证规则和相关数据结构
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class FilterStats:
    """筛选统计信息"""
    question_length: int
    answer_length: int
    has_question_mark: bool
    is_hotel_related: bool
    hotel_keywords_found: List[str]


@dataclass
class FilterResult:
    """筛选结果"""
    index: int
    is_kept: bool
    score: int
    reason: str
    stage: str
    stats: FilterStats


@dataclass
class ProcessingConfig:
    """处理配置"""
    min_score: int = 7
    batch_size: int = 12
    max_workers: int = 6
    sample_size: Optional[int] = None


class DataQualityRules:
    """数据质量规则定义"""
    
    # 酒店相关关键词
    HOTEL_KEYWORDS = [
        '酒店', '宾馆', '客房', '房间', '前台', '服务', '入住', '退房',
        '预订', '预定', '餐厅', '客人', '顾客', '住客', '管家', '清洁',
        '维修', '设施', '早餐', '会议', '活动', '投诉', '建议', '接待',
        '登记', '结账', '房卡', '钥匙', '毛巾', '床单', '空调', '电视',
        '浴室', '洗漱', '毛巾', '拖鞋', '礼宾', '行李', '叫醒', '续住'
    ]
    
    # 长度限制
    MIN_QUESTION_LENGTH = 8
    MAX_QUESTION_LENGTH = 120
    MIN_ANSWER_LENGTH = 30
    MAX_ANSWER_LENGTH = 1200
    MIN_ANSWER_CONTENT_LENGTH = 20
    
    @classmethod
    def validate_entry(cls, entry: Dict[str, Any]) -> Tuple[bool, str, FilterStats]:
        """
        验证单个数据条目
        
        Args:
            entry: 数据条目
            
        Returns:
            (是否有效, 原因, 统计信息)
        """
        try:
            # 提取内容
            contents = entry.get('contents', [])
            if len(contents) < 2:
                return False, '数据格式错误：缺少问答内容', FilterStats(0, 0, False, False, [])
            
            question = contents[0]['parts'][0]['text']
            answer = contents[1]['parts'][0]['text']
            
            # 创建统计信息
            stats = FilterStats(
                question_length=len(question),
                answer_length=len(answer),
                has_question_mark='？' in question or '?' in question,
                is_hotel_related=False,
                hotel_keywords_found=[]
            )
            
            # 检查问题
            issues = []
            
            # 长度检查
            if not (cls.MIN_QUESTION_LENGTH <= len(question) <= cls.MAX_QUESTION_LENGTH):
                issues.append(f'问题长度异常({len(question)}字符)')
            
            if not (cls.MIN_ANSWER_LENGTH <= len(answer) <= cls.MAX_ANSWER_LENGTH):
                issues.append(f'回答长度异常({len(answer)}字符)')
            
            # 格式检查
            if not stats.has_question_mark:
                issues.append('问题缺少疑问标记')
            
            # 内容质量检查
            if len(answer.strip()) < cls.MIN_ANSWER_CONTENT_LENGTH:
                issues.append('回答内容过短')
            
            # 酒店相关性检查
            combined_text = question + answer
            found_keywords = [kw for kw in cls.HOTEL_KEYWORDS if kw in combined_text]
            stats.hotel_keywords_found = found_keywords
            stats.is_hotel_related = len(found_keywords) > 0
            
            if not stats.is_hotel_related:
                issues.append('与酒店服务不相关')
            
            # 判断是否通过（允许最多1个问题，但必须与酒店相关）
            is_valid = len(issues) <= 1 and stats.is_hotel_related
            reason = '; '.join(issues) if issues else '通过规则检查'
            
            return is_valid, reason, stats
            
        except Exception as e:
            return False, f'处理错误: {str(e)}', FilterStats(0, 0, False, False, [])
    
    @classmethod
    def get_quality_summary(cls, results: List[FilterResult]) -> Dict[str, Any]:
        """
        获取质量统计摘要
        
        Args:
            results: 筛选结果列表
            
        Returns:
            质量统计摘要
        """
        if not results:
            return {}
        
        total_count = len(results)
        kept_count = len([r for r in results if r.is_kept])
        
        # 长度统计
        question_lengths = [r.stats.question_length for r in results]
        answer_lengths = [r.stats.answer_length for r in results]
        
        # 关键词统计
        all_keywords = []
        for r in results:
            all_keywords.extend(r.stats.hotel_keywords_found)
        
        keyword_counts = {}
        for kw in all_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        # 分数分布
        score_distribution = {}
        for r in results:
            score_distribution[r.score] = score_distribution.get(r.score, 0) + 1
        
        return {
            'total_entries': total_count,
            'kept_entries': kept_count,
            'retention_rate': kept_count / total_count if total_count > 0 else 0,
            'question_length': {
                'min': min(question_lengths) if question_lengths else 0,
                'max': max(question_lengths) if question_lengths else 0,
                'avg': sum(question_lengths) / len(question_lengths) if question_lengths else 0
            },
            'answer_length': {
                'min': min(answer_lengths) if answer_lengths else 0,
                'max': max(answer_lengths) if answer_lengths else 0,
                'avg': sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
            },
            'top_keywords': sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'score_distribution': score_distribution
        } 