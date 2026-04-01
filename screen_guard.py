#!/usr/bin/env python3
"""
Screen Guard
- 屏幕连续亮 60 分钟 → 语音提醒休息
- 环境光太暗 → 语音提醒开灯

用法:
  python3 screen_guard.py
  nohup python3 screen_guard.py > screen_guard.log 2>&1 &
"""

import argparse
import ctypes
import os
import subprocess
import sys
import time
import signal
from datetime import datetime
from enum import Enum, auto

# ── 配置（可自行修改）────────────────────────────────────────────
WORK_THRESHOLD      = 60 * 60   # 连续在场多久触发休息提醒（秒）
REMIND_INTERVAL     = 10 * 60   # 提醒后还未休息，多久再提醒（秒）
POLL_INTERVAL       = 5         # 主循环轮询间隔（秒）
LIGHT_REMIND_CD     = 60 * 60   # 开灯提醒冷却时间（秒，每小时最多一次）

# 东京日落时间（按月，开始提醒的小时）
# 冬短夏长，12月最早16点，6-7月最晚19点
_LIGHT_START_BY_MONTH = {
    1: 17, 2: 17, 3: 17, 4: 18,
    5: 18, 6: 19, 7: 19, 8: 18,
    9: 17, 10: 17, 11: 16, 12: 16,
}
VOICE               = None      # 自动检测，无需修改
# ────────────────────────────────────────────────────────────────


# ── 语音 ────────────────────────────────────────────────────────

def _load_config_voice() -> str | None:
    """读取同目录 config.txt 中的 voice 设置"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
    if not os.path.exists(config_path):
        return None
    for line in open(config_path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("voice") and "=" in line:
            return line.split("=", 1)[1].strip()
    return None

def _detect_voice() -> str:
    for v in ("Tingting", "Ting-Ting"):
        r = subprocess.run(["say", "-v", v, ""], capture_output=True)
        if r.returncode == 0:
            return v
    return "Alex"  # 最终回退

def _validate_voice(name: str) -> bool:
    r = subprocess.run(["say", "-v", name, ""], capture_output=True)
    return r.returncode == 0

def say(text: str):
    subprocess.Popen(["say", "-v", VOICE, text])

BREAK_MESSAGES = [
    "你已经工作了一个小时，该休息一下了。",
    "记得起来动一动，保护好你的眼睛和身体。",
    "休息一下吧，喝点水，活动活动身体。",
]

LIGHT_MESSAGE = "天色渐暗，记得开灯，保护眼睛。"


# ── 屏幕状态检测 ─────────────────────────────────────────────────

class DisplayDetector:
    def __init__(self):
        cg = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cg.CGMainDisplayID.restype = ctypes.c_uint32
        cg.CGDisplayIsAsleep.argtypes = [ctypes.c_uint32]
        cg.CGDisplayIsAsleep.restype = ctypes.c_int
        self._cg = cg
        self._display = cg.CGMainDisplayID()

    def is_asleep(self) -> bool:
        return bool(self._cg.CGDisplayIsAsleep(self._display))

    def is_awake(self) -> bool:
        return not self.is_asleep()


# ── 环境光检测（时间段代理）────────────────────────────────────────
# M4 MacBook 不通过公开 API 暴露环境光传感器原始值；
# 用时间段判断：18:00-23:00 视为可能光线不足，提醒用户开灯。

def is_dim_hours() -> bool:
    now   = datetime.now()
    start = _LIGHT_START_BY_MONTH[now.month]
    return start <= now.hour < 23


# ── 状态机 ───────────────────────────────────────────────────────

class State(Enum):
    BREAK    = auto()   # 屏幕休眠
    WORKING  = auto()   # 屏幕亮，未到提醒时间
    REMINDED = auto()   # 已提醒，屏幕仍亮


class ScreenGuard:
    def __init__(self, display: DisplayDetector):
        self.display        = display
        self.state          = State.BREAK
        self.work_start     = None
        self.last_reminded  = None
        self.remind_count   = 0
        self.last_light_check   = 0.0
        self.last_light_remind  = 0.0

    # ── 主循环 ──

    def run(self):
        now = time.monotonic()
        if self.display.is_awake():
            self._enter_working(now)
        _log("Screen Guard 启动，按 Ctrl+C 退出")

        while True:
            now = time.monotonic()
            self._tick_screen(now)
            self._tick_light(now)
            time.sleep(POLL_INTERVAL)

    # ── 屏幕状态 tick ──

    def _tick_screen(self, now: float):
        awake = self.display.is_awake()

        if self.state == State.BREAK:
            if awake:
                self._enter_working(now)

        elif self.state == State.WORKING:
            if not awake:
                self._enter_break()
            elif now - self.work_start >= WORK_THRESHOLD:
                self._remind(now)
                self.state = State.REMINDED

        elif self.state == State.REMINDED:
            if not awake:
                self._enter_break()
            elif now - self.last_reminded >= REMIND_INTERVAL:
                self._remind(now)

    def _enter_working(self, now: float):
        self.state        = State.WORKING
        self.work_start   = now
        self.remind_count = 0
        self.last_reminded = None
        elapsed = _fmt(now - self.work_start) if self.work_start else "—"
        _log("▶ WORKING（计时开始）")

    def _enter_break(self):
        self.state = State.BREAK
        _log("⏸ BREAK（屏幕休眠，计时暂停）")

    def _remind(self, now: float):
        msg = BREAK_MESSAGES[self.remind_count % len(BREAK_MESSAGES)]
        self.remind_count  += 1
        self.last_reminded  = now
        say(msg)
        elapsed = _fmt(now - self.work_start)
        _log(f"🔔 提醒 #{self.remind_count}（在场 {elapsed}）：{msg}")

    # ── 环境光 tick ──

    def _tick_light(self, now: float):
        if now - self.last_light_check < 60:   # 每分钟检查一次时间
            return
        self.last_light_check = now

        if is_dim_hours() and now - self.last_light_remind >= LIGHT_REMIND_CD:
            self.last_light_remind = now
            say(LIGHT_MESSAGE)
            month = datetime.now().month
            start = _LIGHT_START_BY_MONTH[month]
            _log(f"💡 傍晚时段（{month}月，{start}点后），提醒开灯")


# ── 工具函数 ─────────────────────────────────────────────────────

def _log(msg: str):
    ts = datetime.now().strftime("[%H:%M:%S]")
    print(f"{ts} {msg}", flush=True)

def _fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}分{s:02d}秒"


# ── 入口 ─────────────────────────────────────────────────────────

def main():
    global VOICE

    parser = argparse.ArgumentParser(description="Screen Guard")
    parser.add_argument("--voice", help="指定语音名称，例如 --voice Kyoko")
    parser.add_argument("--list-voices", action="store_true", help="列出常用中文/英文语音")
    args = parser.parse_args()

    if args.list_voices:
        print("常用语音（在系统设置 → 辅助功能 → 朗读内容 中可免费下载更多）：")
        print()
        voices = [
            ("Tingting",  "中文（普通话，女声）"),
            ("Ting-Ting", "中文（普通话，女声，旧版）"),
            ("Kyoko",     "日语（女声）"),
            ("Samantha",  "英语（美式，女声）"),
            ("Daniel",    "英语（英式，男声）"),
            ("Karen",     "英语（澳式，女声）"),
            ("Siri",      "Siri 语音（需在系统设置中启用）"),
        ]
        for name, desc in voices:
            ok = "✅" if _validate_voice(name) else "❌ 未安装"
            print(f"  {ok}  {name:<12} {desc}")
        print()
        print("使用方法：python3 screen_guard.py --voice Kyoko")
        print("或在 config.txt 中写入：voice = Kyoko")
        return

    # 优先级：命令行 > config.txt > 自动检测
    if args.voice:
        if _validate_voice(args.voice):
            VOICE = args.voice
        else:
            print(f"⚠ 语音 '{args.voice}' 不可用，回退到自动检测")
            VOICE = _detect_voice()
    else:
        config_voice = _load_config_voice()
        if config_voice:
            if _validate_voice(config_voice):
                VOICE = config_voice
            else:
                print(f"⚠ config.txt 中的语音 '{config_voice}' 不可用，回退到自动检测")
                VOICE = _detect_voice()
        else:
            VOICE = _detect_voice()

    _log(f"语音：{VOICE}")

    display = DisplayDetector()
    guard   = ScreenGuard(display)

    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    try:
        guard.run()
    except SystemExit:
        _log("Screen Guard 已退出")


if __name__ == "__main__":
    main()
