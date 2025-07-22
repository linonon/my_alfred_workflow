import os
import sys
import json
import re
from difflib import SequenceMatcher


def parse_ssh_config(config_path):
    hosts = []
    current_host = {}
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            host_match = re.match(r"^Host\s+(.+)", line, re.I)
            if host_match:
                if current_host:
                    hosts.append(current_host)
                    current_host = {}
                current_host["Host"] = host_match.group(1)
            else:
                key_value = line.split(None, 1)
                if len(key_value) == 2 and current_host:
                    key, value = key_value
                    current_host[key] = value
        if current_host:
            hosts.append(current_host)
    return hosts


def similarity(a, b):
    """计算两个字符串的相似度，使用 SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def generate_feedback(hosts, query=None):
    """生成 Alfred 的反馈结果，包括 mods 字段."""
    items = []
    if query:
        # 计算每个 host 的相似度
        for host in hosts:
            host_name = host.get("Host", "Unknown")
            sim = similarity(query, host_name)
            host["similarity"] = sim
        # 根据相似度排序
        hosts = sorted(hosts, key=lambda x: x.get("similarity", 0), reverse=True)
        # 过滤出相似度较高的结果（阈值可根据需要调整）
        hosts = [host for host in hosts if host.get("similarity", 0) > 0.3]
    for host in hosts:
        host_name = host.get("Host", "Unknown")
        hostname = host.get("HostName", "N/A")
        port = host.get("Port", "22")  # 默认SSH端口为22
        user = host.get("User", "")
        display_title = host_name
        display_subtitle = f"{hostname}:{port}"
        ssh_command = f"ssh {host_name}"
        if user:
            ssh_command = f"ssh {host_name}"
        item = {
            "title": display_title,
            "subtitle": display_subtitle,
            "arg": ssh_command,
            # "icon": {
            #     "path": "icon.png"  # 可选：添加一个图标
            # },
            "mods": {
                "cmd": {
                    "subtitle": f"Copy {display_subtitle} to clipboard",
                    "arg": display_subtitle,
                }
            },
        }
        items.append(item)
    feedback = {"items": items}
    print(json.dumps(feedback))


def main():
    config_path = os.path.expanduser("~/.ssh/config")
    if not os.path.exists(config_path):
        print(json.dumps({"items": []}))
        sys.exit(0)
    hosts = parse_ssh_config(config_path)

    # 获取用户输入的查询参数
    query = ""
    if len(sys.argv) > 1:
        query = sys.argv[1].strip()

    generate_feedback(hosts, query)


if __name__ == "__main__":
    main()
