#!/bin/zsh
# Action -> Run Script

# 获取传入的目录路径
selected_dir="$1"

# 检查目录是否存在
if [[ -d "$selected_dir" ]]; then
  zoxide add "$selected_dir"
  code "$selected_dir"
else
  echo "$selected_dir not exist!"
fi