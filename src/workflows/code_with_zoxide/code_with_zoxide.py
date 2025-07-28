import os
import subprocess
import sys
from collections import defaultdict
from difflib import SequenceMatcher

try:
    # Add project root to path
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from helpers.alfred import AlfredScriptFilter, AlfredItem, AlfredMod

except ImportError:
    sys.exit(
        "Error: Could not import Alfred models. Ensure the project structure is correct."
    )

HOME = os.path.expanduser("~")+ "/"
WORKSPACE = os.path.join(HOME, "Workspace/")
COMPANY = os.path.join(WORKSPACE, "company/")
PART_MATCH_SCORE = 100
FULL_MATCH_SCORE = 1000
ZOXIDE_RESULT_SCORE = 10000
MATCH_PATH_DEPTH = 5

EXCLUDE_FOLDERS_PREFIX = [
    "/Applications",
]



def calculate_matching_scores(
    zoxide_result: str, paths: list[str], query: str
) -> dict[str, int]:
    """Main entry point of the script.

    key: path, value: score
    """
    split_query = query.split(" ")
    result: dict[str, int] = defaultdict(int)
    for path in paths:
        folders = path.split("/")
        for q in split_query:
            for i, folder_name in enumerate(reversed(folders)):
                if i >= MATCH_PATH_DEPTH:
                    break
                if folder_name == "":
                    continue
                ratio = SequenceMatcher(None, q.lower(), folder_name.lower()).ratio()
                if ratio >= 0.8:
                    score = FULL_MATCH_SCORE
                else:
                    score = PART_MATCH_SCORE * ratio
                result[path] += int(score * (MATCH_PATH_DEPTH - i) / MATCH_PATH_DEPTH)

    if zoxide_result:
        result[zoxide_result] += ZOXIDE_RESULT_SCORE

    # 先按分數排序
    result = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
    
    # 特殊處理：只讓以 /src 結尾的路徑排在其父目錄前面
    sorted_paths = list(result.keys())
    final_order = []
    processed = set()
    
    for path in sorted_paths:
        if path in processed:
            continue
            
        # 找到與當前路徑有父子關係的所有路徑
        related_paths = [path]
        processed.add(path)
        
        # 查找所有子路徑
        for other_path in sorted_paths:
            if other_path != path and other_path not in processed:
                if other_path.startswith(path + "/"):
                    related_paths.append(other_path)
                    processed.add(other_path)
        
        # 特殊排序：只有以 /src 結尾的路徑排在父路徑前面
        def src_priority_sort_key(p):
            if p.endswith("/src"):
                return (0, -result[p])  # src 路徑優先，然後按分數排序
            else:
                return (1, -result[p])  # 其他路徑按分數排序
        
        related_paths.sort(key=src_priority_sort_key)
        final_order.extend(related_paths)
    
    # 重新構建結果字典
    result = {path: result[path] for path in final_order}
    return result


def get_zoxide_result(input: str) -> str:
    try:
        args = ["zoxide", "query"] + input.split(" ")
        result = subprocess.check_output(args, text=True).strip()
    except subprocess.CalledProcessError:
        result = ""
    return result


def get_zoxide_paths() -> list[str]:
    try:
        paths = []
        zoxide_query_list = subprocess.check_output(
            ["zoxide", "query", "--list"], text=True
        ).splitlines()
        for item in zoxide_query_list:
            if any(item.startswith(prefix) for prefix in EXCLUDE_FOLDERS_PREFIX):
                continue
            paths.append(item)
    except subprocess.CalledProcessError:
        paths = []

    return paths

def replace_str_in_match(match: str)-> str:
    """Replace HOME in match with ~."""

    if match.startswith(COMPANY) and match != COMPANY:
        return match.replace(COMPANY, "[company] ", 1)
    if match.startswith(WORKSPACE) and match != WORKSPACE:
        return match.replace(WORKSPACE, "[workspace] ", 1)
    if match.startswith(HOME) and match != HOME:
        return match.replace(HOME, "[home] ", 1)
    return match


def main():
    # 获取传入的搜索关键词
    input_query = sys.argv[1] if len(sys.argv) > 1 else ""

    # 使用 zoxide 查询所有路径
    paths = get_zoxide_paths()
    zoxide_result = get_zoxide_result(input_query)

    # 检查是否有结果
    if not paths:
        script_filter = AlfredScriptFilter()
        script_filter.add_simple_item(
            title="No results found", subtitle="Try a different search term"
        ).valid = False
        print(script_filter.to_json())
        sys.exit(0)

    # 使用自定义算法找出最佳匹配项
    matches = calculate_matching_scores(zoxide_result, paths, input_query)

    # 构建 Alfred 所需的 JSON 格式
    script_filter = AlfredScriptFilter()

    for i, match in enumerate(matches):
        if i > 10:
            break

        replace_match = replace_str_in_match(match)

        mods = {
            "cmd": AlfredMod(valid=True, arg=match, subtitle="Copy path to clipboard"),
            "alt": AlfredMod(valid=True, arg=match, subtitle="Reveal in Finder"),
        }


        item = AlfredItem(
            title=replace_match, subtitle="Open with VSCode", arg=match, mods=mods
        )
        script_filter.add_item(item)

    # 如果没有匹配项，提供一个默认提示
    if not script_filter.items:
        script_filter.add_simple_item(
            title="No results found", subtitle="Try a different search term"
        ).valid = False

    # 输出 JSON 供 Alfred 使用
    print(script_filter.to_json())


if __name__ == "__main__":
    main()
