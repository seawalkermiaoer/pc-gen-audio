# -*- coding: utf-8 -*-
"""
Gemini AI 服务
使用 OpenAI 兼容接口调用 Gemini
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv
from src.config.constants import GEMINI_MODEL, GEMINI_BASE_URL

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    """Gemini AI 服务类"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = GEMINI_BASE_URL
        self.model = GEMINI_MODEL
        
        if not self.api_key:
            logger.error("未找到 GEMINI_API_KEY 环境变量")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate_json(self, system_prompt: str, user_prompt: str) -> Optional[Any]:
        """
        调用 Gemini 生成 JSON 响应
        """
        try:
            logger.info(f"调用 Gemini API, model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Gemini 原始响应: {content}")
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Gemini API 调用失败: {e}")
            return None

    def get_word_definition(self, word: str) -> Optional[Dict[str, str]]:
        """
        获取单词释义
        """
        system_prompt = "你是一个专业的英语字典。请提供单词的中文释义和词性。必须以 JSON 格式输出。"
        user_prompt = f"请提供单词 '{word}' 的释义。格式示例: {{\"definition\": \"释义文本\", \"part_of_speech\": \"词性\"}}"
        
        return self.generate_json(system_prompt, user_prompt)

    def get_word_memory_aid(self, word: str) -> Optional[Dict[str, str]]:
        """
        获取 AI 辅助记忆
        """
        system_prompt = "你是一个创意英语老师。请提供单词的记忆辅助方法（包括发音联想、词根词缀、例句）。必须以 JSON 格式输出。"
        user_prompt = f"请为单词 '{word}' 生成记忆辅助。格式示例: {{\"pronunciation\": \"发音/谐音联想\", \"memory_method\": \"记忆法描述\", \"examples\": \"例句及翻译\"}}"
        
        return self.generate_json(system_prompt, user_prompt)

    def convert_article_to_json(self, article_text: str) -> Optional[List[Dict[str, str]]]:
        """
        将文章转换为中英对照 JSON 数组
        """
        system_prompt = "你是一个英语学习助手。请将英文文章拆分为中英对照的句子或短段落。必须以 JSON 数组格式输出。"
        user_prompt = f"请将以下文章转换为 JSON 数组，每个元素包含 'english' 和 'chinese' 字段。只返回 JSON 数组本身。\n\n文章内容:\n{article_text}"
        
        result = self.generate_json(system_prompt, user_prompt)
        # 兼容性处理：Gemini 可能返回 {"segments": [...]} 或直接返回列表
        if isinstance(result, dict):
            # 寻找可能是列表的键
            for val in result.values():
                if isinstance(val, list):
                    return val
            return [result] # 退而求其次
        return result

# 全局单例
_gemini_service = None

def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
