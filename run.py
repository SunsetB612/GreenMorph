#!/usr/bin/env python3
"""
GreenMorph 启动脚本
提供便捷的启动和配置选项
"""

import os
import sys
import argparse
import uvicorn
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


def setup_logging(debug: bool = False):
    """设置日志配置"""
    log_level = "DEBUG" if debug else "INFO"
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        "logs/greenmorph.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )


def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")
    
    # 检查必要的目录
    os.makedirs(settings.input_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 检查API密钥
    api_keys_available = []
    if settings.openai_api_key:
        api_keys_available.append("OpenAI")
    if settings.anthropic_api_key:
        api_keys_available.append("Anthropic")
    if settings.replicate_api_token:
        api_keys_available.append("Replicate")
    
    if not api_keys_available:
        logger.warning("未检测到任何API密钥，某些功能可能不可用")
        logger.info("请配置以下环境变量之一：")
        logger.info("- OPENAI_API_KEY (推荐)")
        logger.info("- ANTHROPIC_API_KEY")
        logger.info("- REPLICATE_API_TOKEN")
    else:
        logger.info(f"检测到API密钥: {', '.join(api_keys_available)}")
    
    # 检查CUDA可用性
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"CUDA可用，GPU设备: {torch.cuda.get_device_name()}")
        else:
            logger.info("CUDA不可用，将使用CPU")
    except ImportError:
        logger.warning("PyTorch未安装，图像生成功能可能不可用")
    
    logger.info("环境检查完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GreenMorph - AI驱动的旧物再设计平台")
    parser.add_argument("--host", default=settings.host, help="服务器地址")
    parser.add_argument("--port", type=int, default=settings.port, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.debug)
    
    # 检查环境
    check_environment()
    
    # 启动信息
    logger.info("=" * 60)
    logger.info("🚀 启动 GreenMorph 服务")
    logger.info("=" * 60)
    logger.info(f"服务地址: http://{args.host}:{args.port}")
    logger.info(f"API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"调试模式: {'开启' if args.debug else '关闭'}")
    logger.info(f"自动重载: {'开启' if args.reload else '关闭'}")
    logger.info("=" * 60)
    
    try:
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers if not args.reload else 1,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("GreenMorph 服务已停止")


if __name__ == "__main__":
    main()
