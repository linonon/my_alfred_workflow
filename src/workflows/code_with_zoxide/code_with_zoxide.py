import json
import os
import subprocess
import sys
from collections import defaultdict
from difflib import SequenceMatcher

HOME = os.path.expanduser("~")
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

    result = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
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


def main():
    # 获取传入的搜索关键词
    input_query = sys.argv[1] if len(sys.argv) > 1 else ""

    # 使用 zoxide 查询所有路径
    paths = get_zoxide_paths()
    zoxide_result = get_zoxide_result(input_query)

    # 检查是否有结果
    if not paths:
        # 输出一个自定义的 Alfred 项目，提示无匹配结果
        no_results = {
            "items": [
                {
                    "title": "No results found",
                    "subtitle": "Try a different search term",
                    "valid": False,
                }
            ]
        }
        print(json.dumps(no_results, indent=2))
        sys.exit(0)

    # 使用自定义算法找出最佳匹配项
    matches = calculate_matching_scores(zoxide_result, paths, input_query)

    # 构建 Alfred 所需的 JSON 格式
    items = []
    for i, match in enumerate(matches):
        if i > 10:
            break
        items.append(
            {
                "title": match,
                "subtitle": "Open with VSCode",
                "arg": match,
                "mods": {
                    "cmd": {
                        "valid": True,
                        "arg": match,
                        "subtitle": "Copy path to clipboard",
                    },
                    "alt": {
                        "valid": True,
                        "arg": match,
                        "subtitle": "Reveal in Finder",
                    },
                },
            }
        )

    # 如果没有匹配项，提供一个默认提示
    if not items:
        items.append(
            {
                "title": "No results found",
                "subtitle": "Try a different search term",
                "valid": False,
            }
        )

    output = {"items": items}

    # 输出 JSON 供 Alfred 使用
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
