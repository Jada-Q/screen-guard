#!/bin/bash
# Screen Guard 安装脚本
# 把 Screen Guard.app 拖到应用程序文件夹后，运行此脚本设置开机自启

set -e

APP_PATH="/Applications/Screen Guard.app"
PLIST="$HOME/Library/LaunchAgents/com.screen-guard.plist"
BINARY="$APP_PATH/Contents/MacOS/Screen Guard"

echo "Screen Guard 安装程序"
echo "──────────────────────"

# 检查 .app 是否存在
if [ ! -f "$BINARY" ]; then
    echo "❌ 找不到 Screen Guard.app"
    echo "   请先把 Screen Guard.app 拖到「应用程序」文件夹，再运行此脚本。"
    exit 1
fi

# 停止旧版本
launchctl unload "$PLIST" 2>/dev/null || true

# 写入 LaunchAgent
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.screen-guard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BINARY</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/screen-guard.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/screen-guard.log</string>
</dict>
</plist>
EOF

# 启动
launchctl load "$PLIST"
sleep 2

echo "✅ 安装完成！Screen Guard 已在后台运行。"
echo ""
echo "配置文件（可修改语音）："
echo "  ~/Library/Application Support/ScreenGuard/config.txt"
echo ""
echo "停止运行："
echo "  launchctl unload ~/Library/LaunchAgents/com.screen-guard.plist"
