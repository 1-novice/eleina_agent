"""全能智能体动漫角色Agent - 主入口"""

from src.tools.cli_registrar import register_cli_tools
from src.skill.cli_registrar import register_cli_intents
from src.cli.interactive_cli import run_interactive_cli


def main():
    """主函数 - 初始化并启动CLI交互"""
    print("=== 全能智能体动漫角色Agent ===")
    print("输入 'exit' 退出")
    print("输入 'status' 查看状态")
    print("输入 'reset' 重置会话")
    
    # 注册工具和意图
    register_cli_tools()
    register_cli_intents()
    
    # 启动交互式CLI
    run_interactive_cli()


if __name__ == "__main__":
    main()