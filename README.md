# Screen Guard 🖥️

盯屏幕超过 **60 分钟**，自动语音提醒你休息。傍晚光线暗了，提醒你开灯。

macOS 专用，零费用，后台静默运行。

---

## 快速开始

### 第一步：确认已安装 Python 3

打开终端（Terminal），粘贴以下命令回车：

```bash
python3 --version
```

显示版本号（如 `Python 3.x.x`）即可。没有的话先去 [python.org](https://www.python.org/downloads/) 下载安装。

### 第二步：下载 Screen Guard

```bash
git clone https://github.com/Jada-Q/screen-guard
cd screen-guard
```

### 第三步：启动

```bash
python3 screen_guard.py
```

看到以下输出说明成功运行：

```
[10:26:30] 语音：Tingting
[10:26:30] ▶ WORKING（计时开始）
[10:26:30] Screen Guard 启动，按 Ctrl+C 退出
```

60 分钟后会自动语音提醒。**窗口不要关，最小化就好。**

---

## 设为开机自动启动（推荐）

不想每次手动开，执行一次即可永久后台运行：

```bash
# 1. 创建启动配置
cat > ~/Library/LaunchAgents/com.screen-guard.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.screen-guard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>$(pwd)/screen_guard.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$(pwd)/screen_guard.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/screen_guard.log</string>
</dict>
</plist>
EOF

# 2. 启动
launchctl load ~/Library/LaunchAgents/com.screen-guard.plist
```

之后重启 Mac 也会自动运行，无需任何操作。

停止：
```bash
launchctl unload ~/Library/LaunchAgents/com.screen-guard.plist
```

---

## 功能说明

| 功能 | 详情 |
|---|---|
| 休息提醒 | 屏幕连续亮 60 分钟触发，每 10 分钟重复 |
| 计时重置 | 屏幕休眠即视为休息，唤醒后重新计时 |
| 开灯提醒 | 傍晚时段每小时提醒一次（冬天 16 点起，夏天 19 点起）|
| 语音 | macOS 自带中文语音，无需联网 |

## 自定义提醒时间

编辑 `screen_guard.py` 第 21 行：

```python
WORK_THRESHOLD = 60 * 60  # 改成 45 * 60 即 45 分钟提醒
```

---

## 系统要求

- macOS（Apple Silicon / Intel 均可）
- Python 3.9+
- 无需额外权限，无网络请求
