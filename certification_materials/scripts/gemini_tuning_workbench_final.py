#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 1.5 Pro 酒店服务微调脚本 - Vertex AI Workbench 最终版本
使用优化后的JSONL数据集进行监督微调
"""

import os
import sys
import time
import json
import subprocess
from typing import Optional, Tuple
from pathlib import Path

# 安装必要的包
def install_requirements():
    """安装必要的Python包"""
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", "--quiet", "google-cloud-aiplatform", "google-cloud-storage"
        ], check=True)
        print("✅ 必要包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 包安装失败: {e}")
        sys.exit(1)

# 导入必要的库
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from vertexai.preview.tuning import sft
    from google.cloud import storage
    from google.auth import default
except ImportError:
    print("正在安装必要的包...")
    install_requirements()
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from vertexai.preview.tuning import sft
    from google.cloud import storage
    from google.auth import default

# 项目配置 - 在Workbench中自动获取
def get_project_config():
    """获取项目配置信息"""
    try:
        # 在Workbench中自动获取项目信息
        credentials, project_id = default()
        if not project_id:
            project_id = "cy-aispeci-demo"  # 备用项目ID
        
        location = "asia-east2"
        bucket_name = "peft-model-cy-aispeci-demo"
        
        print(f"📋 项目配置:")
        print(f"   项目ID: {project_id}")
        print(f"   区域: {location}")
        print(f"   存储桶: gs://{bucket_name}")
        
        return project_id, location, bucket_name
        
    except Exception as e:
        print(f"❌ 获取项目配置失败: {e}")
        # 使用默认配置
        return "cy-aispeci-demo", "asia-east2", "peft-model-cy-aispeci-demo"

def validate_jsonl_file(file_path: str) -> Tuple[bool, int]:
    """验证JSONL文件格式"""
    print(f"🔍 验证文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False, 0
    
    try:
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line.strip())
                        
                        # 验证Gemini格式
                        if not all(key in data for key in ['systemInstruction', 'contents']):
                            print(f"❌ 第 {line_num} 行缺少必要字段")
                            return False, 0
                        
                        # 验证系统指令格式
                        sys_inst = data['systemInstruction']
                        if sys_inst.get('role') != 'system' or 'parts' not in sys_inst:
                            print(f"❌ 第 {line_num} 行系统指令格式错误")
                            return False, 0
                        
                        # 验证对话内容格式
                        contents = data['contents']
                        if len(contents) < 2:
                            print(f"❌ 第 {line_num} 行对话内容不完整")
                            return False, 0
                        
                        if contents[0].get('role') != 'user' or contents[1].get('role') != 'model':
                            print(f"❌ 第 {line_num} 行对话角色错误")
                            return False, 0
                        
                        count += 1
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ 第 {line_num} 行JSON格式错误: {e}")
                        return False, 0
        
        print(f"✅ 文件验证通过，共 {count} 条记录")
        return True, count
        
    except Exception as e:
        print(f"❌ 文件验证失败: {e}")
        return False, 0

def upload_to_gcs(local_file: str, bucket_name: str, gcs_path: str) -> bool:
    """上传文件到Google Cloud Storage"""
    try:
        print(f"📤 上传文件到GCS: {local_file} -> gs://{bucket_name}/{gcs_path}")
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        # 上传文件
        blob.upload_from_filename(local_file)
        
        print(f"✅ 文件上传成功: gs://{bucket_name}/{gcs_path}")
        return True
        
    except Exception as e:
        print(f"❌ 文件上传失败: {e}")
        return False

def check_bucket_exists(bucket_name: str) -> bool:
    """检查存储桶是否存在"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        bucket.reload()
        print(f"✅ 存储桶存在: gs://{bucket_name}")
        return True
    except Exception as e:
        print(f"❌ 存储桶不存在或无法访问: {e}")
        return False

def start_tuning_job(project_id: str, location: str, train_uri: str, validation_uri: str) -> Optional[object]:
    """启动微调任务"""
    try:
        print("🚀 启动Gemini模型微调任务...")
        
        # 初始化Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # 创建微调任务
        sft_tuning_job = sft.train(
            source_model="gemini-1.5-pro-002",
            train_dataset=train_uri,
            validation_dataset=validation_uri,
            epochs=3,
            learning_rate_multiplier=1.0,
            tuned_model_display_name="酒店服务助手 - Gemini 1.5 Pro 微调"
        )
        
        print("✅ 微调任务已启动")
        print(f"📋 任务信息:")
        print(f"   任务名称: {sft_tuning_job.resource_name}")
        print(f"   基础模型: gemini-1.5-pro-002")
        print(f"   训练轮数: 3")
        print(f"   学习率倍数: 1.0")
        
        return sft_tuning_job
        
    except Exception as e:
        print(f"❌ 启动微调任务失败: {e}")
        return None

def monitor_tuning_job(sft_tuning_job) -> bool:
    """监控微调任务进度"""
    try:
        print("⏳ 监控微调任务进度...")
        print("📝 微调通常需要 60-120 分钟，请耐心等待...")
        
        start_time = time.time()
        
        while not sft_tuning_job.refresh().has_ended:
            elapsed_time = time.time() - start_time
            elapsed_minutes = int(elapsed_time // 60)
            
            print(f"⏱️  已运行 {elapsed_minutes} 分钟，任务仍在进行中...")
            
            # 每5分钟检查一次
            time.sleep(300)
        
        # 检查任务状态
        job_state = sft_tuning_job.state
        print(f"📊 微调任务完成，状态: {job_state}")
        
        if job_state.name == 'JOB_STATE_SUCCEEDED':
            print("✅ 微调任务成功完成！")
            
            # 获取微调后的模型信息
            tuned_model_name = sft_tuning_job.tuned_model_name
            tuned_model_endpoint = sft_tuning_job.tuned_model_endpoint_name
            
            print(f"📋 微调后的模型信息:")
            print(f"   模型名称: {tuned_model_name}")
            print(f"   端点名称: {tuned_model_endpoint}")
            
            return True
        else:
            print(f"❌ 微调任务失败，状态: {job_state}")
            return False
            
    except Exception as e:
        print(f"❌ 监控微调任务失败: {e}")
        return False

def test_tuned_model(sft_tuning_job) -> bool:
    """测试微调后的模型"""
    try:
        print("🧪 测试微调后的模型...")
        
        # 获取微调后的模型端点
        tuned_model_endpoint = sft_tuning_job.tuned_model_endpoint_name
        tuned_model = GenerativeModel(tuned_model_endpoint)
        
        # 测试问题
        test_questions = [
            "如何提高酒店客房清洁效率？",
            "酒店前台如何处理客户投诉？",
            "如何优化酒店的客户体验？"
        ]
        
        print("📝 测试结果:")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 测试 {i} ---")
            print(f"问题: {question}")
            
            try:
                response = tuned_model.generate_content(question)
                answer = response.text[:300] + "..." if len(response.text) > 300 else response.text
                print(f"回答: {answer}")
                
            except Exception as e:
                print(f"❌ 生成回答失败: {e}")
        
        print("\n✅ 模型测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🏨 Gemini 1.5 Pro 酒店服务微调 - Workbench版本")
    print("=" * 60)
    
    # 获取项目配置
    project_id, location, bucket_name = get_project_config()
    
    # 数据文件路径（使用优化后的数据集）
    train_file = "./dataset/optimized_train.jsonl"
    validation_file = "./dataset/optimized_validation.jsonl"
    
    print(f"\n📂 数据文件:")
    print(f"   训练集: {train_file}")
    print(f"   验证集: {validation_file}")
    
    # 验证数据文件
    print("\n🔍 验证数据文件...")
    train_valid, train_count = validate_jsonl_file(train_file)
    validation_valid, validation_count = validate_jsonl_file(validation_file)
    
    if not train_valid or not validation_valid:
        print("❌ 数据文件验证失败，请检查文件格式")
        return
    
    print(f"✅ 数据验证通过")
    print(f"   训练数据: {train_count} 条")
    print(f"   验证数据: {validation_count} 条")
    
    # 检查存储桶
    print(f"\n🪣 检查存储桶...")
    if not check_bucket_exists(bucket_name):
        print("❌ 存储桶不可用，请检查配置")
        return
    
    # 上传数据文件到GCS
    print(f"\n📤 上传数据文件到GCS...")
    
    train_gcs_path = "hotel_tuning/optimized_train.jsonl"
    validation_gcs_path = "hotel_tuning/optimized_validation.jsonl"
    
    if not upload_to_gcs(train_file, bucket_name, train_gcs_path):
        print("❌ 训练数据上传失败")
        return
    
    if not upload_to_gcs(validation_file, bucket_name, validation_gcs_path):
        print("❌ 验证数据上传失败")
        return
    
    # 构建GCS URI
    train_uri = f"gs://{bucket_name}/{train_gcs_path}"
    validation_uri = f"gs://{bucket_name}/{validation_gcs_path}"
    
    print(f"✅ 数据文件上传完成")
    print(f"   训练数据URI: {train_uri}")
    print(f"   验证数据URI: {validation_uri}")
    
    # 启动微调任务
    print(f"\n🚀 启动微调任务...")
    sft_tuning_job = start_tuning_job(project_id, location, train_uri, validation_uri)
    
    if not sft_tuning_job:
        print("❌ 微调任务启动失败")
        return
    
    # 监控微调任务
    print(f"\n⏳ 监控微调任务...")
    if monitor_tuning_job(sft_tuning_job):
        print("✅ 微调任务成功完成")
        
        # 测试微调后的模型
        print(f"\n🧪 测试微调后的模型...")
        test_tuned_model(sft_tuning_job)
        
        print(f"\n🎉 微调流程全部完成！")
        print(f"🏨 您的酒店服务助手模型已准备就绪")
        
    else:
        print("❌ 微调任务失败")

if __name__ == "__main__":
    main() 