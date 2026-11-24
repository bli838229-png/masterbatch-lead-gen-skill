@echo off
REM ============================================================
REM  [DEPRECATED / 备用通道] External-network debug Chrome (port 9223)
REM
REM  ⚠️ 主通道已改为「用户自己的 Chrome 自动发现」：
REM     BU_NAME=mainchk browser-use （不要设 BU_CDP_URL）
REM     详见 references/browser-deep-dive.md
REM
REM  本脚本仅在主通道失效时作降级备用：独立 profile (chrome-profile-ext)
REM  需配合 BU_CDP_URL=http://127.0.0.1:9223 手动指定。
REM ============================================================
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\Users\Administrator\.browser-use\chrome-profile-ext" --remote-debugging-port=9223 --new-window https://www.google.com
