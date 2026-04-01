# Screen Guard

macOS 环境感知提醒工具。零依赖，纯 Python。

## 功能

- 屏幕连续亮 **60 分钟** → 中文语音提醒休息
- 每 10 分钟重复提醒，直到屏幕休眠
- 屏幕休眠视为休息，计时自动重置
- 环境光过暗 → 语音提醒开灯（每 10 分钟最多一次）

## 运行

```bash
# 前台运行（可看日志）
python3 screen_guard.py

# 后台运行
nohup python3 screen_guard.py > screen_guard.log 2>&1 &

# 停止后台进程
kill $(pgrep -f screen_guard.py)
```

## 验证

快速测试提醒是否正常：

```python
# 临时改 screen_guard.py 第 33 行
WORK_THRESHOLD = 10  # 10秒后触发提醒
```

## 配置

编辑 `screen_guard.py` 顶部的配置区：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `WORK_THRESHOLD` | 3600 | 多少秒触发休息提醒 |
| `REMIND_INTERVAL` | 600 | 重复提醒间隔（秒）|
| `LIGHT_THRESHOLD` | 800 | 低于此值触发开灯提醒 |
| `LIGHT_REMIND_CD` | 600 | 开灯提醒冷却时间（秒）|

## 语音定制

查看可用语音：`say -v '?'`

修改 `VOICE` 变量（脚本会自动检测 Tingting / Ting-Ting）。

## 系统要求

- macOS（Apple Silicon / Intel 均可）
- Python 3.9+
- 无需额外权限
