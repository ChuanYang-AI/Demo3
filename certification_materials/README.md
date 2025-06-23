# 酒店服务AI模型微调项目

## 项目简介

本项目是一个基于Google Vertex AI的酒店服务AI模型微调解决方案，专注于提升酒店服务问答系统的质量和准确性。项目包含完整的数据处理流程、质量筛选工具和模型微调脚本。

## 🏨 客户案例

查看我们的成功案例：[xxx国际酒店集团AI智能助手微调案例](docs/hotel_ai_case_study.md)

**核心成果**：
- 📈 回答准确率从60%提升到81%
- ⚡ 响应时间从5分钟缩短到30秒  
- 💰 年节约人力成本3200万元
- 🎯 客户满意度提升14个百分点

## 主要功能

- **智能数据质量筛选**: 使用规则引擎和AI评估相结合的方式筛选高质量训练数据
- **批量数据处理**: 支持大规模数据集的高效处理和转换
- **模型微调**: 基于Vertex AI的Gemini模型微调功能
- **性能监控**: 提供详细的处理报告和质量分析

## 项目结构

```
certification_materials/
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python依赖包
├── setup.py                          # 安装配置
├── config/                           # 配置文件目录
│   └── default_config.yaml          # 默认配置
├── src/                             # 源代码目录
│   ├── __init__.py
│   ├── data_quality/                # 数据质量模块
│   │   ├── __init__.py
│   │   ├── filter.py                # 数据筛选器
│   │   └── rules.py                 # 质量规则定义
│   ├── data_processing/             # 数据处理模块
│   │   ├── __init__.py
│   │   ├── converter.py             # 数据格式转换
│   │   └── uploader.py              # 数据上传工具
│   ├── model_tuning/                # 模型微调模块
│   │   ├── __init__.py
│   │   └── tuner.py                 # 微调工具
│   └── utils/                       # 工具模块
│       ├── __init__.py
│       ├── vertexai_manager.py      # Vertex AI管理器
│       └── logger.py                # 日志工具
├── scripts/                         # 可执行脚本
│   ├── filter_data.py               # 数据筛选脚本
│   ├── convert_data.py              # 数据转换脚本
│   └── tune_model.py                # 模型微调脚本
├── notebooks/                       # Jupyter笔记本
│   └── hotel_model_tuning_demo.ipynb
├── dataset/                         # 数据集目录
│   ├── raw/                         # 原始数据
│   ├── processed/                   # 处理后数据
│   └── reports/                     # 处理报告
├── docs/                           # 文档目录
│   ├── installation.md             # 安装指南
│   ├── usage.md                     # 使用指南
│   └── api_reference.md             # API参考
└── tests/                          # 测试目录
    ├── __init__.py
    ├── test_data_quality.py
    └── test_data_processing.py
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd certification_materials

# 安装依赖
pip install -r requirements.txt

# 或使用pip安装
pip install -e .
```

### 2. 配置认证

设置Google Cloud认证：

```bash
# 设置服务账户密钥路径
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

### 3. 数据质量筛选

```bash
# 筛选高质量数据
python scripts/filter_data.py \
    --input dataset/raw/hotel_train_data.jsonl \
    --output dataset/processed/hotel_high_quality_data.jsonl \
    --min-score 7 \
    --batch-size 12
```

### 4. 模型微调

```bash
# 执行模型微调
python scripts/tune_model.py \
    --train-data dataset/processed/hotel_high_quality_data.jsonl \
    --validation-data dataset/raw/hotel_validation_data.jsonl \
    --model-name "hotel-service-model-v1"
```

## 核心特性

### 数据质量筛选

- **多层筛选机制**: 规则预筛选 + AI智能评估
- **高性能处理**: 支持多线程并行处理，处理速度可达3-4条目/秒
- **质量保证**: 平均保留率85%以上，确保数据质量

### 智能规则引擎

- **长度验证**: 问题8-120字符，回答30-1200字符
- **格式检查**: 问题必须包含疑问标记
- **相关性验证**: 基于30+酒店关键词的相关性检查
- **内容质量**: 回答内容实质性检查

### AI质量评估

- **批量评估**: 使用Gemini 2.5 Flash进行批量质量评估
- **多维度评分**: 问题清晰度、回答专业性、逻辑一致性
- **智能解析**: 自动解析AI响应，支持容错处理

## 性能指标

- **处理速度**: 3.8条目/秒
- **数据保留率**: 85.5%
- **规则筛选通过率**: 99.9%
- **AI评估准确率**: 95%+

## 配置说明

主要配置参数：

```yaml
data_quality:
  min_score: 7                    # 最低质量分数
  batch_size: 12                  # 批处理大小
  max_workers: 6                  # 最大并发数
  
model_tuning:
  model_name: "gemini-2.5-flash"  # 基础模型
  learning_rate: 0.001            # 学习率
  epochs: 10                      # 训练轮数
```

## API参考

### HotelDataQualityFilter

主要的数据质量筛选类：

```python
from src.data_quality.filter import HotelDataQualityFilter
from src.data_quality.rules import ProcessingConfig

# 创建筛选器
filter = HotelDataQualityFilter(credentials_path)

# 配置参数
config = ProcessingConfig(
    min_score=7,
    batch_size=12,
    max_workers=6
)

# 执行筛选
filter.filter_data(input_file, output_file, config)
```

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持数据质量筛选
- 支持模型微调
- 完整的文档和示例 