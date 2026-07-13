#!/usr/bin/env python3
"""
离线舆情监控执行脚本
无需HTTP服务，直接调用Agent执行舆情监控任务。
用于GitHub Actions、Crontab等离线自动执行场景。

用法:
    python scripts/run_monitor.py                     # 默认监控
    python scripts/run_monitor.py --brands 小牛看房    # 指定品牌
    python scripts/run_monitor.py --prompt "搜索舆情"  # 自定义提示词
"""

import os
import sys
import json
import argparse
import logging

# 设置工作路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ.setdefault('COZE_WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def run_monitor(brands: list = None, custom_prompt: str = None, timeout: int = 600):
    """
    直接调用Agent执行舆情监控
    
    Args:
        brands: 品牌列表，默认 ["小牛看房", "常居地产"]
        custom_prompt: 自定义提示词
        timeout: 超时时间（秒）
    """
    if brands is None:
        brands = ["小牛看房", "常居地产"]
    
    brands_str = "和".join(brands)
    
    if custom_prompt is None:
        prompt = (
            f"请搜索{brands_str}的最新舆情，"
            "使用data-analysis-plus的方法进行深度分析（趋势分析、情感量化评分、竞品对比），"
            "生成详细的舆情报告，包括正面、中性、负面舆情统计，"
            "如有负面舆情请发送到飞书和企业微信。"
        )
    else:
        prompt = custom_prompt
    
    logger.info("=" * 60)
    logger.info("离线舆情监控任务开始")
    logger.info(f"监控品牌: {brands}")
    logger.info(f"任务提示词: {prompt[:100]}...")
    logger.info("=" * 60)
    
    try:
        # 动态导入，避免循环依赖
        from agents.agent import build_agent
        
        # 构建Agent
        agent = build_agent()
        
        # 配置：使用agent的唯一配置key
        config = {"configurable": {"thread_id": "offline_monitor"}}
        
        # 构建消息
        messages = [{"role": "user", "content": prompt}]
        
        # 执行
        logger.info("正在调用Agent...")
        result = agent.invoke({"messages": messages}, config=config)
        
        # 提取最后一条AI消息
        if result and "messages" in result:
            last_msg = result["messages"][-1]
            content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            
            # 只输出摘要（避免输出过长）
            lines = content.split('\n') if isinstance(content, str) else [str(content)]
            logger.info("=" * 60)
            logger.info("任务执行完成！")
            logger.info(f"输出行数: {len(lines)}")
            
            # 输出前20行作为摘要
            for line in lines[:20]:
                print(line)
            if len(lines) > 20:
                print(f"... (共 {len(lines)} 行，仅显示前20行)")
            
            logger.info("=" * 60)
            return True
        else:
            logger.error("Agent未返回有效结果")
            return False
            
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="离线舆情监控执行脚本")
    parser.add_argument(
        "--brands", 
        nargs="+", 
        default=["小牛看房", "常居地产"],
        help="监控品牌列表"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        default=None,
        help="自定义提示词"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=600,
        help="超时时间（秒）"
    )
    
    args = parser.parse_args()
    
    success = run_monitor(
        brands=args.brands,
        custom_prompt=args.prompt,
        timeout=args.timeout
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
