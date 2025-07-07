#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vertex AI 管理器

负责Vertex AI客户端的初始化和内容生成功能
"""

import json
import os
from typing import Optional


class VertexAIManager:
    """Vertex AI 管理器"""
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 project_id: Optional[str] = None,
                 location: str = "us-central1",
                 model_name: str = "gemini-2.0-flash"):
        """
        初始化 Vertex AI 客户端
        
        Args:
            credentials_path: 服务账户密钥文件路径
            project_id: Google Cloud项目ID
            location: Vertex AI区域
            model_name: 使用的模型名称
        """
        self.location = location
        self.model_name = model_name
        self._import_dependencies()
        self._initialize_client(credentials_path, project_id)
    
    def _import_dependencies(self):
        """延迟导入依赖库"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            from google.oauth2 import service_account
            
            self.vertexai = vertexai
            self.GenerativeModel = GenerativeModel
            self.service_account = service_account
            
        except ImportError as e:
            raise ImportError(f"无法导入 Vertex AI 库: {e}")
    
    def _initialize_client(self, credentials_path: Optional[str], 
                          project_id: Optional[str]):
        """初始化客户端"""
        try:
            # 设置认证凭证
            if credentials_path:
                credentials = self.service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
                # 如果没有提供project_id，从凭证文件中获取
                if not project_id:
                    with open(credentials_path, 'r', encoding='utf-8') as file:
                        credential_info = json.load(file)
                        project_id = credential_info['project_id']
            else:
                # 使用默认凭证
                credentials = None
                if not project_id:
                    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                    if not project_id:
                        raise ValueError("必须提供project_id或设置GOOGLE_CLOUD_PROJECT环境变量")
            
            # 初始化 Vertex AI
            self.vertexai.init(
                project=project_id, 
                location=self.location, 
                credentials=credentials
            )
            
            # 创建模型实例
            self.model = self.GenerativeModel(self.model_name)
            self.project_id = project_id
            
            print(f"✅ Vertex AI 初始化成功 (项目: {project_id}, 区域: {self.location}, 模型: {self.model_name})")
            
        except Exception as e:
            raise RuntimeError(f"Vertex AI 初始化失败: {e}")
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        生成内容
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他生成参数
            
        Returns:
            生成的文本内容
        """
        try:
            response = self.model.generate_content(prompt, **kwargs)
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"内容生成失败: {e}")
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "project_id": self.project_id,
            "location": self.location,
            "model_name": self.model_name
        } 