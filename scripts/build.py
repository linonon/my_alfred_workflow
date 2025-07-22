#!/usr/bin/env python3
"""
Build script for Alfred Workflow CLI

清理并构建可执行文件
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.pyc']
    
    print("🧹 清理构建文件...")
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  删除目录: {dir_name}")
    
    # 清理 __pycache__ 文件夹
    for pycache_dir in Path('.').rglob('__pycache__'):
        shutil.rmtree(pycache_dir)
        print(f"  删除缓存: {pycache_dir}")


def run_pyinstaller():
    """运行 PyInstaller"""
    print("📦 开始构建可执行文件...")
    
    try:
        result = subprocess.run(
            ['uv', 'run', 'pyinstaller', 'main.spec'],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ 构建成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print("错误输出:")
        print(e.stderr)
        return False


def check_executable():
    """检查可执行文件"""
    exe_path = Path('dist/alfred-cli')
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📁 可执行文件: {exe_path}")
        print(f"📊 文件大小: {size_mb:.1f}MB")
        
        # 测试运行
        try:
            result = subprocess.run(
                [str(exe_path), 'list'],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ 可执行文件测试通过")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 可执行文件测试失败: {e}")
            return False
    else:
        print("❌ 可执行文件不存在")
        return False


def main():
    """主函数"""
    print("🚀 Alfred CLI 构建脚本")
    print("=" * 40)
    
    # 确保在项目根目录
    if not Path('main.py').exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 清理
    clean_build()
    print()
    
    # 构建
    if not run_pyinstaller():
        sys.exit(1)
    print()
    
    # 检查
    if not check_executable():
        sys.exit(1)
    
    print()
    print("🎉 构建完成!")
    print("可执行文件位置: dist/alfred-cli")


if __name__ == "__main__":
    main()