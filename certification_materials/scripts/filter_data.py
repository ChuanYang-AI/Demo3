#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据筛选脚本

提供命令行接口用于执行酒店数据质量筛选
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_quality import HotelDataQualityFilter, ProcessingConfig


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="酒店数据质量筛选工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/filter_data.py --input dataset/raw/hotel_train_data.jsonl --output dataset/processed/filtered_data.jsonl
  python scripts/filter_data.py -i data.jsonl -o filtered.jsonl --min-score 8 --batch-size 10 --max-workers 4
  python scripts/filter_data.py -i data.jsonl -o filtered.jsonl --sample-size 100 --credentials /path/to/key.json
        """
    )
    
    # 必需参数
    parser.add_argument(
        "-i", "--input", 
        required=True,
        help="输入数据文件路径 (JSONL格式)"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True, 
        help="输出文件路径 (JSONL格式)"
    )
    
    # 可选参数
    parser.add_argument(
        "--credentials",
        help="Google Cloud服务账户密钥文件路径 (默认使用环境变量)"
    )
    
    parser.add_argument(
        "--project-id",
        help="Google Cloud项目ID (默认从凭证文件获取)"
    )
    
    parser.add_argument(
        "--model-name",
        default="gemini-2.5-flash",
        help="使用的模型名称 (默认: gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--min-score",
        type=int,
        default=7,
        help="最低质量分数 (1-10, 默认: 7)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=12,
        help="批处理大小 (默认: 12)"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=6,
        help="最大并发数 (默认: 6)"
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        help="样本大小限制 (用于测试, 默认处理全部数据)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """验证命令行参数"""
    errors = []
    
    # 检查输入文件
    if not os.path.exists(args.input):
        errors.append(f"输入文件不存在: {args.input}")
    
    # 检查输出目录
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"无法创建输出目录: {e}")
    
    # 检查凭证文件
    if args.credentials and not os.path.exists(args.credentials):
        errors.append(f"凭证文件不存在: {args.credentials}")
    
    # 检查参数范围
    if not (1 <= args.min_score <= 10):
        errors.append("最低分数必须在1-10之间")
    
    if args.batch_size <= 0:
        errors.append("批处理大小必须大于0")
    
    if args.max_workers <= 0:
        errors.append("最大并发数必须大于0")
    
    if args.sample_size is not None and args.sample_size <= 0:
        errors.append("样本大小必须大于0")
    
    return errors


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()
    
    # 验证参数
    errors = validate_arguments(args)
    if errors:
        print("❌ 参数验证失败:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # 创建处理配置
    config = ProcessingConfig(
        min_score=args.min_score,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        sample_size=args.sample_size
    )
    
    try:
        # 创建筛选器
        filter_instance = HotelDataQualityFilter(
            credentials_path=args.credentials,
            project_id=args.project_id,
            model_name=args.model_name,
            log_level=args.log_level
        )
        
        # 执行筛选
        filter_instance.filter_data(args.input, args.output, config)
        
        print(f"\n✅ 数据筛选完成！")
        print(f"📁 输出文件: {args.output}")
        print(f"📋 报告文件: {args.output.replace('.jsonl', '_quality_report.json')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 