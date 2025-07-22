import sys
from typing import List
from src.base_tool import BaseTool


class CodeWithZoxideTool(BaseTool):
    @property
    def name(self) -> str:
        return "code_with_zoxide"

    @property
    def description(self) -> str:
        return "使用zoxide查找并打开项目"

    def run(self, args: List[str]) -> None:
        # 设置sys.argv以模拟命令行调用
        original_argv = sys.argv
        try:
            sys.argv = ["code_with_zoxide"] + args
            from src.workflows.code_with_zoxide.code_with_zoxide import main

            main()
        finally:
            sys.argv = original_argv
