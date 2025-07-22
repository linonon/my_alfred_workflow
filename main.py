#!/usr/bin/env python3
"""
Alfred Workflow CLI - 可扩展的工具调用入口

用法:
    python main.py <tool_name> [args...]
    python main.py list
    python main.py help [tool_name]

示例:
    python main.py chrome_bookmarks "python"
    python main.py code_with_zoxide "my project"
    python main.py ssh_launcher "server"
"""

import sys
import json
from typing import Dict, List
from src.base_tool import BaseTool
from src.tools.chrome_bookmarks_tool import ChromeBookmarksTool
from src.tools.code_with_zoxide_tool import CodeWithZoxideTool
from src.tools.ssh_launcher_tool import SSHLauncherTool


class WorkflowCLI:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()

    def _register_tools(self):
        """注册所有工具"""
        tools = [
            ChromeBookmarksTool(),
            CodeWithZoxideTool(),
            SSHLauncherTool(),
        ]

        for tool in tools:
            self.tools[tool.name] = tool

    def list_tools(self):
        """列出所有可用的工具"""
        if not self.tools:
            print("没有发现可用的工具")
            return

        print("可用的工具:")
        for name, tool in self.tools.items():
            print(f"  {name:<20} - {tool.description}")

    def get_tool_help(self, tool_name: str):
        """获取工具的帮助信息"""
        if tool_name not in self.tools:
            print(f"工具 '{tool_name}' 不存在")
            return

        tool = self.tools[tool_name]
        print(f"工具: {tool.name}")
        print(f"描述: {tool.description}")

    def run_tool(self, tool_name: str, args: List[str]):
        """运行指定的工具"""
        if tool_name not in self.tools:
            available_tools = ", ".join(self.tools.keys()) if self.tools else "无"
            error_output = {
                "items": [
                    {
                        "title": f"工具 '{tool_name}' 不存在",
                        "subtitle": f"可用工具: {available_tools}",
                        "valid": False,
                    }
                ]
            }
            print(json.dumps(error_output, ensure_ascii=False, indent=2))
            sys.exit(1)

        try:
            tool = self.tools[tool_name]
            tool.run(args)
        except Exception as e:
            error_output = {
                "items": [
                    {
                        "title": f"执行工具 '{tool_name}' 时出错",
                        "subtitle": str(e),
                        "valid": False,
                    }
                ]
            }
            print(json.dumps(error_output, ensure_ascii=False, indent=2))
            sys.exit(1)

    def show_help(self):
        """显示帮助信息"""
        print(__doc__.strip()) # type: ignore
        print()
        self.list_tools()


def main():
    cli = WorkflowCLI()

    if len(sys.argv) < 2:
        cli.show_help()
        return

    command = sys.argv[1]

    if command == "list":
        cli.list_tools()
    elif command == "help":
        if len(sys.argv) > 2:
            cli.get_tool_help(sys.argv[2])
        else:
            cli.show_help()
    else:
        # 将命令作为工具名，其余参数传递给工具
        tool_name = command
        args = sys.argv[2:]
        cli.run_tool(tool_name, args)


if __name__ == "__main__":
    main()
