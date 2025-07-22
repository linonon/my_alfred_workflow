import sys
from typing import List
from src.base_tool import BaseTool


class ChromeBookmarksTool(BaseTool):
    @property
    def name(self) -> str:
        return "chrome_bookmarks"

    @property
    def description(self) -> str:
        return "搜索Chrome书签"

    def run(self, args: List[str]) -> None:
        # 设置sys.argv以模拟命令行调用
        original_argv = sys.argv
        try:
            sys.argv = ["chrome_bookmarks"] + args
            from src.workflows.chrome_bookmakrs.chrome_bookmarks import main

            main()
        finally:
            sys.argv = original_argv
