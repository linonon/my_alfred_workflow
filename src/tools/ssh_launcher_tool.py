import sys
from typing import List
from src.base_tool import BaseTool


class SSHLauncherTool(BaseTool):
    @property
    def name(self) -> str:
        return "ssh_launcher"

    @property
    def description(self) -> str:
        return "SSH连接管理工具"

    def run(self, args: List[str]) -> None:
        # 设置sys.argv以模拟命令行调用
        original_argv = sys.argv
        try:
            sys.argv = ["ssh_launcher"] + args
            from src.workflows.ssh_launcher.ssh_launcher import main

            main()
        finally:
            sys.argv = original_argv
