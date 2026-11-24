#!/usr/bin/env bash
# ============================================================
#  客户工作台启动脚本（本地，仅监听 127.0.0.1）
#  用法：把本脚本放在「工作目录」下（与 tools/ 同级），执行即可。
#  自动定位脚本所在目录，不依赖任何硬编码路径。
# ============================================================
set -e
cd "$(dirname "$0")"

echo "正在启动本地客户工作台 ..."
echo "浏览器将自动打开 http://127.0.0.1:8610"
echo "按 Ctrl+C 停止服务。"

# 尝试自动打开浏览器（macOS / Linux 各发行版）
if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:8610" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:8610" >/dev/null 2>&1 &
fi

exec python3 tools/workbench.py
