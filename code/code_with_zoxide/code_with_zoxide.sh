#!/bin/zsh
# input -> Script Filter
export _ZO_DATA_DIR="$HOME/.zoxide_data"

# 获取传入的搜索关键词
query="$1"

# 使用 zoxide 查找匹配的路径，获取所有匹配结果
results=$(zoxide query `echo $query` --list)

# 检查是否有结果
if [[ -z "$results" ]]; then
  # 输出一个自定义的 Alfred 项目，提示无匹配结果
  echo '{
    "items": [
      {
        "title": "No results found",
        "subtitle": "Try a different search term",
        "valid": false
      }
    ]
  }'
  exit 0
fi

# 构建 Alfred 需要的 JSON 格式
output='{"items":['

# 遍历每个结果，添加到 JSON 中
for dir in ${(f)results}; do
  # Escape JSON special characters in directory paths
  escaped_dir=$(printf '%s' "$dir" | jq -R . | sed 's/^"//' | sed 's/"$//')
  output+='{
    "title": "'"$escaped_dir"'",
    "subtitle": "Open with VSCode",
    "arg": "'"$escaped_dir"'"
  },'
done

# 移除最后一个逗号并关闭 JSON
output=${output%,}
output+=']}'

echo "$output"