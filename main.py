"""全能智能体动漫角色Agent - 主入口"""

import argparse
import sys

from src.tools.cli_registrar import register_cli_tools
from src.skill.cli_registrar import register_cli_intents
from src.cli.interactive_cli import run_interactive_cli
from src.api.app import run_api_server
from src.config.config import settings


def main():
    """主函数 - 根据参数启动CLI或API服务"""
    parser = argparse.ArgumentParser(description="全能智能体动漫角色Agent")
    parser.add_argument(
        "--mode", 
        choices=["cli", "api"], 
        default="cli",
        help="运行模式: cli (交互式命令行) 或 api (API服务)"
    )
    parser.add_argument(
        "--host", 
        default=settings.api_host,
        help="API服务绑定地址"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=settings.api_port,
        help="API服务端口"
    )
    
    args = parser.parse_args()
    
    if args.mode == "api":
        start_api_server(args.host, args.port)
    else:
        start_cli()


def start_cli():
    """启动交互式CLI"""
    print("=== 全能智能体动漫角色Agent ===")
    print("输入 'exit' 退出")
    print("输入 'status' 查看状态")
    print("输入 'reset' 重置会话")
    
    register_cli_tools()
    register_cli_intents()
    
    run_interactive_cli()


def start_api_server(host: str, port: int):
    """启动API服务"""
    print(f"=== 启动 Eleina Agent API 服务 ===")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    print(f"API说明: http://{host}:{port}/redoc")
    
    register_cli_tools()
    register_cli_intents()
    
    run_api_server(host, port)


if __name__ == "__main__":
    main()