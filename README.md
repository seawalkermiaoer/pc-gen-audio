# PC Gen Audio

一个音频生成流水线，可将中英文句子对转换为带有精确时间戳的同步音频文件。

## 项目概述
该系统使用本地 OpenAI TTS 服务生成语音，通过 ffmpeg 处理音频，并生成带有时间戳的 MP3/WAV 文件以及 JSON 元数据。

## 环境准备

### 前置条件
- Python 3.9+
- ffmpeg 和 ffprobe (用于音频处理)
- 运行在 `http://localhost:8880/v1` 的本地 OpenAI 兼容 TTS 服务

### 快速开始
1. 启动本地 TTS 服务（例如使用 Docker）：
   ```bash
   docker run -d -p 8880:8880 ghcr.m.daocloud.io/remsky/kokoro-fastapi-cpu:latest
   ```
2. 运行流水线：
   ```bash
   python3 main.py tests/pen.md
   ```

## 目录结构
- `main.py` - 主流水线脚本
- `res/` - 结果输出目录（运行后生成）
- `tmp/` - 临时文件目录（运行后生成）

## 主要功能
- 自动生成中英文语音
- 精确计算音频时长和时间戳
- 生成 Markdown 格式的对照时间线
- 归一化音频处理，确保音质一致

## 许可证
MIT
