#!/usr/bin/env python3
"""
端口清理工具

读取项目配置文件，列出所有服务所需端口，检测是否被占用，
并按需 kill 占用进程。

用法:
    python scripts/kill_ports.py          # 交互式模式，逐一询问
    python scripts/kill_ports.py -f       # 强制模式，直接 kill 全部占用进程
    python scripts/kill_ports.py -f 80    # 强制 kill 指定端口（可跟多个）
    python scripts/kill_ports.py --dry-run  # 只显示占用情况，不做任何操作
"""

import argparse
import json
import os
import sys
import signal

try:
    import psutil
except ImportError:
    print("[ERROR] 缺少依赖：psutil。请先运行: pip install psutil")
    sys.exit(1)

# ────────────────────────────────────────────────────────
# 项目根目录
# ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "config.json")


# ────────────────────────────────────────────────────────
# 从配置文件 + 已知硬编码读取端口表
# ────────────────────────────────────────────────────────
def load_ports() -> list[dict]:
    """返回 [{"name": ..., "port": ...}, ...] 列表"""
    ports = []

    # 1. 读取 config/config.json（唯一数据源）
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for svc_key, port_val in cfg.get("ports", {}).items():
                try:
                    ports.append({"name": svc_key, "port": int(port_val), "source": "config.json"})
                except (TypeError, ValueError):
                    pass
        except Exception as e:
            print(f"[WARN] 读取 config.json 失败: {e}")
    else:
        print(f"[WARN] 配置文件不存在: {CONFIG_FILE}")

    # 对 port 去重（保留先出现的）
    seen = set()
    unique = []
    for p in ports:
        if p["port"] not in seen:
            seen.add(p["port"])
            unique.append(p)

    return unique


# ────────────────────────────────────────────────────────
# 进程查询
# ────────────────────────────────────────────────────────
def find_pids_for_port(port: int) -> list[dict]:
    """返回占用该端口的所有进程信息列表"""
    result = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                pid = conn.pid
                if pid is None:
                    continue
                try:
                    proc = psutil.Process(pid)
                    result.append({
                        "pid": pid,
                        "name": proc.name(),
                        "cmdline": " ".join(proc.cmdline())[:120],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    result.append({"pid": pid, "name": "?", "cmdline": ""})
    except psutil.AccessDenied:
        # Windows 上可能需要管理员权限
        print("[WARN] 获取网络连接信息时权限不足，建议以管理员身份运行。")
    return result


def kill_pid(pid: int) -> bool:
    """Kill 一个进程，返回是否成功"""
    try:
        proc = psutil.Process(pid)
        proc.kill()
        proc.wait(timeout=5)
        return True
    except psutil.NoSuchProcess:
        return True  # 已经不存在，视为成功
    except psutil.AccessDenied:
        print(f"  [ERROR] 权限不足，无法 kill PID {pid}（请以管理员身份运行）")
        return False
    except Exception as e:
        print(f"  [ERROR] kill PID {pid} 失败: {e}")
        return False


# ────────────────────────────────────────────────────────
# 颜色（Windows 终端也支持 ANSI，Python 3.12+ 默认开启）
# ────────────────────────────────────────────────────────
def _c(text: str, code: str) -> str:
    """简单 ANSI 颜色包装，非 TTY 时降级为纯文本"""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _c(t, "32")
RED    = lambda t: _c(t, "31")
YELLOW = lambda t: _c(t, "33")
CYAN   = lambda t: _c(t, "36")
BOLD   = lambda t: _c(t, "1")


# ────────────────────────────────────────────────────────
# 核心逻辑
# ────────────────────────────────────────────────────────
def process_port(entry: dict, force: bool, dry_run: bool) -> None:
    """检测并处理单个端口"""
    port = entry["port"]
    name = entry["name"]
    source = entry.get("source", "")

    pids = find_pids_for_port(port)
    tag = f"[{source}]" if source else ""

    if not pids:
        print(f"  {GREEN('[OK]')} {BOLD(name)} (:{port}) {tag} - free")
        return

    # 有进程占用
    print(f"  {RED('[BUSY]')} {BOLD(name)} (:{port}) {tag} - {RED('occupied')}")
    for p in pids:
        print(f"      PID {p['pid']}  {p['name']}")
        if p["cmdline"]:
            print(f"      CMD {p['cmdline']}")

    if dry_run:
        return

    if force:
        # 直接 kill
        for p in pids:
            ok = kill_pid(p["pid"])
            status = GREEN("[killed]") if ok else RED("[FAILED]")
            print(f"      -> PID {p['pid']} {status}")
    else:
        # 交互式询问
        ans = input(f"  Kill the above {len(pids)} process(es)? [y/N] ").strip().lower()
        if ans == "y":
            for p in pids:
                ok = kill_pid(p["pid"])
                status = GREEN("[killed]") if ok else RED("[FAILED]")
                print(f"      -> PID {p['pid']} {status}")
        else:
            print(f"      -> skipped")


# ────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="检测并清理 Dplayer 服务所需端口的占用进程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="强制模式：直接 kill 所有占用进程，无需确认",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只列出占用情况，不执行任何 kill 操作",
    )
    parser.add_argument(
        "ports",
        nargs="*",
        type=int,
        metavar="PORT",
        help="只处理指定端口（不指定则处理配置中的全部端口）",
    )
    args = parser.parse_args()

    # ── 加载端口列表 ──
    all_ports = load_ports()

    # ── 过滤（如果用户指定了端口） ──
    if args.ports:
        port_set = set(args.ports)
        target = [p for p in all_ports if p["port"] in port_set]
        # 用户指定但不在配置里的端口也纳入
        known = {p["port"] for p in all_ports}
        for extra in port_set - known:
            target.append({"name": f"port-{extra}", "port": extra, "source": "cli"})
        target.sort(key=lambda x: x["port"])
    else:
        target = all_ports

    # ── 打印标题 ──
    mode_label = "dry-run" if args.dry_run else ("force" if args.force else "interactive")
    print(BOLD(f"\n=== Dplayer 端口清理工具 [{mode_label}] ==="))
    print(f"配置文件: {CONFIG_FILE}")
    print(f"共 {len(target)} 个端口待检测\n")

    # ── 逐一处理 ──
    for entry in target:
        process_port(entry, force=args.force, dry_run=args.dry_run)

    print(BOLD("\n=== 完成 ===\n"))


if __name__ == "__main__":
    # Windows 上启用 ANSI 颜色
    if sys.platform == "win32":
        os.system("")  # 触发 VT100 模式
    main()
