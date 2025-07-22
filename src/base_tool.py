from abc import ABC, abstractmethod
from typing import List


class BaseTool(ABC):
    """工具基础类，所有工具都需要继承此类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @abstractmethod
    def run(self, args: List[str]) -> None:
        """运行工具，参数从args获取，输出到stdout"""
        pass
