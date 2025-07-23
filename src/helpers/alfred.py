"""Alfred Script Filter 模型定义"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class AlfredIcon:
    """Alfred 图标配置类"""

    type: Optional[str] = None
    """图标类型: 'fileicon','filetype' """
    path: Optional[str] = None
    """图标路径"""


@dataclass
class AlfredMod:
    """Alfred 修饰键配置类"""

    valid: bool = True
    """是否可操作"""
    arg: Optional[str] = None
    """传递的参数"""
    subtitle: Optional[str] = None
    """副标题"""


@dataclass
class AlfredText:
    """Alfred 文本配置类"""

    copy: Optional[str] = None
    """复制文本"""
    largetype: Optional[str] = None
    """大字体显示文本"""


@dataclass
class AlfredItem:
    """Alfred 结果项类"""

    title: str
    """结果标题 (必需)"""
    uid: Optional[str] = None
    """唯一标识符，用于学习和排序"""
    subtitle: Optional[str] = None
    """副标题描述"""
    arg: Optional[str] = None
    """传递给输出动作的参数"""
    icon: Optional[AlfredIcon] = None
    """自定义图标"""
    valid: bool = True
    """是否可操作，默认为 True"""
    match: Optional[str] = None
    """自定义匹配文本用于过滤"""
    autocomplete: Optional[str] = None
    """自动完成文本"""
    type: str = "default"
    """结果类型，默认为 'default'"""
    mods: Optional[Dict[str, AlfredMod]] = None
    """修饰键行为"""
    action: Optional[str] = None
    """通用动作配置"""
    text: Optional[AlfredText] = None
    """复制/大字体文本"""
    quicklookurl: Optional[str] = None
    """预览 URL 或路径"""
    variables: Optional[Dict[str, Any]] = None
    """项目特定变量"""

    def to_dict(self) -> Dict[str, Any]:
        """将 AlfredItem 转换为字典格式"""
        result = {"title": self.title, "valid": self.valid, "type": self.type}

        if self.uid:
            result["uid"] = self.uid
        if self.subtitle:
            result["subtitle"] = self.subtitle
        if self.arg:
            result["arg"] = self.arg
        if self.icon:
            icon_dict = {}
            if self.icon.type:
                icon_dict["type"] = self.icon.type
            if self.icon.path:
                icon_dict["path"] = self.icon.path
            if icon_dict:
                result["icon"] = icon_dict
        if self.match:
            result["match"] = self.match
        if self.autocomplete:
            result["autocomplete"] = self.autocomplete
        if self.mods:
            mods_dict = {}
            for key, mod in self.mods.items():
                mod_dict: dict[str, Any] = {"valid": mod.valid}
                if mod.arg:
                    mod_dict["arg"] = mod.arg
                if mod.subtitle:
                    mod_dict["subtitle"] = mod.subtitle
                mods_dict[key] = mod_dict
            result["mods"] = mods_dict
        if self.action:
            result["action"] = self.action
        if self.text:
            text_dict = {}
            if self.text.copy:
                text_dict["copy"] = self.text.copy
            if self.text.largetype:
                text_dict["largetype"] = self.text.largetype
            if text_dict:
                result["text"] = text_dict
        if self.quicklookurl:
            result["quicklookurl"] = self.quicklookurl
        if self.variables:
            result["variables"] = self.variables

        return result


@dataclass
class AlfredScriptFilter:
    """Alfred Script Filter 主类"""

    items: List[AlfredItem] = field(default_factory=list)
    """结果项数组 (必需)"""
    variables: Optional[Dict[str, Any]] = None
    """会话变量传递给工作流"""
    rerun: Optional[float] = None
    """自动重新运行脚本间隔 (0.1-5.0 秒)"""
    cache: Optional[Dict[str, Any]] = None
    """脚本结果缓存配置"""
    skipknowledge: Optional[bool] = None
    """保持原始项目顺序"""

    def add_item(self, item: AlfredItem) -> None:
        """添加结果项"""
        self.items.append(item)

    def add_simple_item(
        self,
        title: str,
        subtitle: Optional[str] = None,
        arg: Optional[str] = None,
        uid: Optional[str] = None,
        autocomplete: Optional[str] = None,
    ) -> AlfredItem:
        """添加简单结果项的便捷方法"""
        item = AlfredItem(
            title=title, subtitle=subtitle, arg=arg, uid=uid, autocomplete=autocomplete
        )
        self.add_item(item)
        return item

    def to_dict(self) -> Dict[str, Any]:
        """将 AlfredScriptFilter 转换为字典格式"""
        result: dict[str, Any] = {"items": [item.to_dict() for item in self.items]}

        if self.variables:
            result["variables"] = self.variables
        if self.rerun is not None:
            result["rerun"] = self.rerun
        if self.cache:
            result["cache"] = self.cache
        if self.skipknowledge is not None:
            result["skipknowledge"] = self.skipknowledge

        return result

    def to_json(self) -> str:
        """将 AlfredScriptFilter 转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
