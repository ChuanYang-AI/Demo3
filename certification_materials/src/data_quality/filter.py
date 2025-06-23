#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量筛选器

提供酒店数据质量筛选的核心功能
"""

import json
import time
import re
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from ..utils import VertexAIManager, setup_logger
from .rules import DataQualityRules, ProcessingConfig, FilterStats, FilterResult


class AIQualityEvaluator:
    """AI质量评估器"""
    
    def __init__(self, ai_manager: VertexAIManager):
        """
        初始化AI质量评估器
        
        Args:
            ai_manager: VertexAI管理器实例
        """
        self.ai_manager = ai_manager
        self.logger = setup_logger("ai_evaluator")
    
    def create_evaluation_prompt(self, entries_data: List[Tuple[str, str]]) -> str:
        """
        创建评估提示词
        
        Args:
            entries_data: 问答对列表
            
        Returns:
            评估提示词
        """
        batch_items = []
        for idx, (question, answer) in enumerate(entries_data):
            # 截断过长内容以提高处理速度
            truncated_question = question[:100] if len(question) > 100 else question
            truncated_answer = answer[:300] if len(answer) > 300 else answer
            
            batch_items.append(f"[{idx+1}] Q: {truncated_question}\nA: {truncated_answer}")
        
        prompt = f"""请评估以下{len(batch_items)}个酒店服务问答对的质量。
评分标准：1-10分，7分及以上为高质量数据。

评估要点：
1. 问题是否清晰具体且与酒店服务相关？
2. 回答是否专业准确且有实用价值？
3. 问答是否匹配且逻辑合理？

{chr(10).join(batch_items)}

请严格按照JSON数组格式回复：
[{{"score":8,"keep":true}},{{"score":6,"keep":false}}...]"""
        
        return prompt
    
    def parse_ai_response(self, response_text: str, entry_count: int) -> List[Dict[str, Any]]:
        """
        解析AI响应
        
        Args:
            response_text: AI响应文本
            entry_count: 条目数量
            
        Returns:
            解析后的评估结果列表
        """
        try:
            # 提取JSON数组
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                evaluations = json.loads(json_match.group(0))
            else:
                # 备用方案：创建默认评估
                evaluations = [{'score': 7, 'keep': True} for _ in range(entry_count)]
                self.logger.warning(f"无法解析AI响应，使用默认评估")
            
            # 标准化评估结果
            standardized_results = []
            for i in range(entry_count):
                if i < len(evaluations):
                    eval_result = evaluations[i]
                    score = eval_result.get('score', 7)
                    keep = eval_result.get('keep', score >= 7)
                else:
                    score = 7
                    keep = True
                
                standardized_results.append({
                    'score': score,
                    'keep': keep,
                    'reason': f'AI评估(分数:{score})'
                })
            
            return standardized_results
            
        except Exception as e:
            # 解析失败时的备用方案
            self.logger.error(f"解析AI响应失败: {e}")
            return [{'score': 7, 'keep': True, 'reason': f'解析失败: {str(e)}'} 
                   for _ in range(entry_count)]
    
    def evaluate_batch(self, entries: List[Tuple[int, Dict[str, Any]]], 
                      batch_id: int) -> List[Tuple[int, Dict[str, Any]]]:
        """
        批量评估数据质量
        
        Args:
            entries: 数据条目列表 [(原始索引, 数据)]
            batch_id: 批次ID
            
        Returns:
            评估结果列表 [(原始索引, 评估结果)]
        """
        if not entries:
            return []
        
        # 提取问答数据
        entries_data = []
        valid_entries = []
        
        for original_index, entry in entries:
            try:
                contents = entry.get('contents', [])
                if len(contents) < 2:
                    continue
                
                question = contents[0]['parts'][0]['text']
                answer = contents[1]['parts'][0]['text']
                
                entries_data.append((question, answer))
                valid_entries.append((original_index, entry))
                
            except Exception as e:
                self.logger.warning(f"跳过无效条目 {original_index}: {e}")
                continue
        
        if not entries_data:
            return [(idx, {'score': 5, 'keep': True, 'reason': '数据格式错误'}) 
                   for idx, _ in entries]
        
        try:
            # 生成评估提示词并获取AI响应
            prompt = self.create_evaluation_prompt(entries_data)
            response_text = self.ai_manager.generate_content(prompt)
            
            # 解析响应
            evaluations = self.parse_ai_response(response_text, len(valid_entries))
            
            # 构建结果
            results = []
            for i, (original_index, entry) in enumerate(valid_entries):
                evaluation = evaluations[i]
                evaluation['reason'] = f"AI评估-批次{batch_id}(分数:{evaluation['score']})"
                results.append((original_index, evaluation))
            
            return results
            
        except Exception as e:
            # 评估失败时的保守策略
            self.logger.error(f"批次{batch_id}评估失败: {e}")
            return [(idx, {'score': 6, 'keep': True, 'reason': f'评估失败-批次{batch_id}: {str(e)}'}) 
                   for idx, _ in valid_entries]


class HotelDataQualityFilter:
    """酒店数据质量筛选器主类"""
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 project_id: Optional[str] = None,
                 model_name: str = "gemini-2.5-flash",
                 log_level: str = "INFO"):
        """
        初始化筛选器
        
        Args:
            credentials_path: 服务账户密钥文件路径
            project_id: Google Cloud项目ID
            model_name: 使用的模型名称
            log_level: 日志级别
        """
        self.logger = setup_logger("hotel_data_filter", level=log_level)
        self.logger.info("🔧 正在初始化酒店数据质量筛选器...")
        
        # 初始化AI管理器
        self.ai_manager = VertexAIManager(
            credentials_path=credentials_path,
            project_id=project_id,
            model_name=model_name
        )
        
        # 初始化AI评估器
        self.ai_evaluator = AIQualityEvaluator(self.ai_manager)
        
        # 线程安全
        self.processing_lock = Lock()
        self.processed_count = 0
        self.start_time = time.time()
    
    def load_data(self, input_file: str, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        加载数据
        
        Args:
            input_file: 输入文件路径
            sample_size: 样本大小限制
            
        Returns:
            数据条目列表
        """
        self.logger.info(f"📖 正在加载数据: {input_file}")
        
        data_entries = []
        with open(input_file, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                try:
                    entry = json.loads(line.strip())
                    data_entries.append(entry)
                    
                    # 如果指定了样本大小，则限制加载数量
                    if sample_size and len(data_entries) >= sample_size:
                        self.logger.info(f"🔍 使用样本数据: {sample_size} 条目")
                        break
                        
                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ 跳过无效JSON行: {line_number}")
                    continue
        
        self.logger.info(f"📊 成功加载 {len(data_entries)} 条数据")
        return data_entries
    
    def apply_rule_filtering(self, data_entries: List[Dict[str, Any]]) -> Tuple[List[Tuple[int, Dict[str, Any]]], List[FilterResult]]:
        """
        应用规则筛选
        
        Args:
            data_entries: 数据条目列表
            
        Returns:
            (通过规则筛选的条目, 所有筛选结果)
        """
        self.logger.info("⚡ 阶段1: 规则预筛选...")
        rule_start_time = time.time()
        
        passed_entries = []
        all_results = []
        
        for index, entry in enumerate(data_entries):
            is_valid, reason, stats = DataQualityRules.validate_entry(entry)
            
            result = FilterResult(
                index=index,
                is_kept=is_valid,
                score=0 if not is_valid else 5,  # 规则筛选阶段暂时给5分
                reason=reason,
                stage='rule_filter',
                stats=stats
            )
            all_results.append(result)
            
            if is_valid:
                passed_entries.append((index, entry))
        
        rule_duration = time.time() - rule_start_time
        failed_count = len(data_entries) - len(passed_entries)
        pass_rate = len(passed_entries) / len(data_entries) * 100
        
        self.logger.info(f"✅ 规则筛选完成 ({rule_duration:.1f}秒)")
        self.logger.info(f"📊 通过: {len(passed_entries)} | 淘汰: {failed_count} | 通过率: {pass_rate:.1f}%")
        
        return passed_entries, all_results
    
    def apply_ai_evaluation(self, passed_entries: List[Tuple[int, Dict[str, Any]]], 
                           config: ProcessingConfig) -> Dict[int, Dict[str, Any]]:
        """
        应用AI评估
        
        Args:
            passed_entries: 通过规则筛选的条目
            config: 处理配置
            
        Returns:
            AI评估结果字典
        """
        if not passed_entries:
            return {}
        
        self.logger.info(f"🤖 阶段2: AI批量评估 {len(passed_entries)} 条目...")
        ai_start_time = time.time()
        
        # 分批处理
        batches = [passed_entries[i:i + config.batch_size] 
                  for i in range(0, len(passed_entries), config.batch_size)]
        self.logger.info(f"📦 分成 {len(batches)} 个批次处理")
        
        all_evaluations = {}
        
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # 提交所有批次任务
            future_to_batch = {
                executor.submit(self.ai_evaluator.evaluate_batch, batch, batch_id): (batch_id, batch)
                for batch_id, batch in enumerate(batches)
            }
            
            # 收集结果
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    for original_index, evaluation in batch_results:
                        all_evaluations[original_index] = evaluation
                    
                    # 更新进度
                    with self.processing_lock:
                        self.processed_count += len(batch_results)
                        elapsed_time = time.time() - self.start_time
                        processing_rate = self.processed_count / elapsed_time if elapsed_time > 0 else 0
                        self.logger.info(f"📊 已处理: {self.processed_count} 条目 | 速度: {processing_rate:.1f} 条目/秒")
                
                except Exception as e:
                    batch_id, batch = future_to_batch[future]
                    self.logger.error(f"❌ 批次{batch_id}处理失败: {e}")
                    # 失败时采用保守策略
                    for original_index, _ in batch:
                        all_evaluations[original_index] = {
                            'score': 6, 'keep': True, 'reason': f'批次{batch_id}处理失败'
                        }
        
        ai_duration = time.time() - ai_start_time
        self.logger.info(f"✅ AI评估完成 ({ai_duration:.1f}秒)")
        
        return all_evaluations
    
    def merge_results(self, data_entries: List[Dict[str, Any]], 
                     rule_results: List[FilterResult],
                     ai_evaluations: Dict[int, Dict[str, Any]],
                     config: ProcessingConfig) -> Tuple[List[FilterResult], List[FilterResult]]:
        """
        合并筛选结果
        
        Args:
            data_entries: 原始数据条目
            rule_results: 规则筛选结果
            ai_evaluations: AI评估结果
            config: 处理配置
            
        Returns:
            (高质量结果, 低质量结果)
        """
        self.logger.info("📋 正在合并筛选结果...")
        
        high_quality_results = []
        low_quality_results = []
        
        for index, entry in enumerate(data_entries):
            rule_result = rule_results[index]
            
            if not rule_result.is_kept:
                # 规则筛选失败
                low_quality_results.append(rule_result)
            else:
                # 获取AI评估结果
                ai_evaluation = ai_evaluations.get(index, {
                    'score': 5, 'keep': True, 'reason': '未进行AI评估'
                })
                
                final_result = FilterResult(
                    index=index,
                    is_kept=ai_evaluation.get('keep', True) and ai_evaluation.get('score', 5) >= config.min_score,
                    score=ai_evaluation.get('score', 5),
                    reason=ai_evaluation.get('reason', ''),
                    stage='ai_evaluation',
                    stats=rule_result.stats
                )
                
                if final_result.is_kept:
                    high_quality_results.append(final_result)
                else:
                    low_quality_results.append(final_result)
        
        return high_quality_results, low_quality_results
    
    def save_results(self, data_entries: List[Dict[str, Any]], 
                    high_quality_results: List[FilterResult],
                    output_file: str):
        """
        保存筛选结果
        
        Args:
            data_entries: 原始数据条目
            high_quality_results: 高质量结果
            output_file: 输出文件路径
        """
        self.logger.info("💾 正在保存筛选结果...")
        
        with open(output_file, 'w', encoding='utf-8') as file:
            for result in high_quality_results:
                entry_data = data_entries[result.index]
                json.dump(entry_data, file, ensure_ascii=False)
                file.write('\n')
        
        self.logger.info(f"✅ 结果已保存到: {output_file}")
    
    def generate_report(self, data_entries: List[Dict[str, Any]],
                       high_quality_results: List[FilterResult],
                       low_quality_results: List[FilterResult],
                       config: ProcessingConfig,
                       output_file: str) -> Dict[str, Any]:
        """
        生成详细报告
        
        Args:
            data_entries: 原始数据条目
            high_quality_results: 高质量结果
            low_quality_results: 低质量结果
            config: 处理配置
            output_file: 输出文件路径
            
        Returns:
            报告数据
        """
        total_processing_time = time.time() - self.start_time
        total_count = len(data_entries)
        high_quality_count = len(high_quality_results)
        retention_rate = high_quality_count / total_count * 100
        processing_speed = total_count / total_processing_time
        
        # 统计各阶段结果
        rule_failed_count = len([r for r in low_quality_results if r.stage == 'rule_filter'])
        ai_failed_count = len([r for r in low_quality_results if r.stage == 'ai_evaluation'])
        
        # 获取质量统计摘要
        all_results = high_quality_results + low_quality_results
        quality_summary = DataQualityRules.get_quality_summary(all_results)
        
        report = {
            'summary': {
                'total_entries': total_count,
                'high_quality_entries': high_quality_count,
                'low_quality_entries': len(low_quality_results),
                'retention_rate_percent': retention_rate,
                'processing_time_seconds': total_processing_time,
                'processing_speed_per_second': processing_speed
            },
            'configuration': {
                'minimum_score': config.min_score,
                'batch_size': config.batch_size,
                'max_workers': config.max_workers,
                'sample_size': config.sample_size,
                'model_info': self.ai_manager.get_model_info()
            },
            'stage_statistics': {
                'rule_filter_failed': rule_failed_count,
                'ai_evaluation_failed': ai_failed_count,
                'rule_filter_passed': total_count - rule_failed_count,
                'ai_evaluation_passed': high_quality_count
            },
            'quality_analysis': quality_summary
        }
        
        # 保存报告
        report_file = output_file.replace('.jsonl', '_quality_report.json')
        with open(report_file, 'w', encoding='utf-8') as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📋 详细报告已保存到: {report_file}")
        return report
    
    def filter_data(self, input_file: str, output_file: str, config: ProcessingConfig):
        """
        执行完整的数据筛选流程
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            config: 处理配置
        """
        self.logger.info(f"🚀 开始酒店数据质量筛选")
        self.logger.info(f"📁 输入文件: {input_file}")
        self.logger.info(f"📁 输出文件: {output_file}")
        self.logger.info(f"⚙️ 配置: 最低分数={config.min_score}, 批量大小={config.batch_size}, 并发数={config.max_workers}")
        
        try:
            # 1. 加载数据
            data_entries = self.load_data(input_file, config.sample_size)
            
            # 2. 规则筛选
            passed_entries, rule_results = self.apply_rule_filtering(data_entries)
            
            if not passed_entries:
                self.logger.error("❌ 没有数据通过规则筛选，程序终止")
                return
            
            # 3. AI评估
            ai_evaluations = self.apply_ai_evaluation(passed_entries, config)
            
            # 4. 合并结果
            high_quality_results, low_quality_results = self.merge_results(
                data_entries, rule_results, ai_evaluations, config
            )
            
            # 5. 保存结果
            self.save_results(data_entries, high_quality_results, output_file)
            
            # 6. 生成报告
            report = self.generate_report(
                data_entries, high_quality_results, low_quality_results, config, output_file
            )
            
            # 7. 输出总结
            self.logger.info(f"\n🎉 数据筛选完成！")
            self.logger.info(f"⏱️  总耗时: {report['summary']['processing_time_seconds']:.1f}秒")
            self.logger.info(f"🚀 处理速度: {report['summary']['processing_speed_per_second']:.1f} 条目/秒")
            self.logger.info(f"📊 原始数据: {report['summary']['total_entries']} 条目")
            self.logger.info(f"📊 高质量数据: {report['summary']['high_quality_entries']} 条目 ({report['summary']['retention_rate_percent']:.1f}%)")
            self.logger.info(f"📊 低质量数据: {report['summary']['low_quality_entries']} 条目")
            self.logger.info(f"📁 筛选结果: {output_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 数据筛选过程中出错: {e}")
            raise 