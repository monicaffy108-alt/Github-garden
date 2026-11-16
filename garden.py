#!/usr/bin/env python3
"""Explicitly synthetic GitHub contribution garden; never rewrites history."""

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

# ========== 你的配置 ==========
OWNER = "monicaffy108-alt"                     # 你的 GitHub 用户名
REMOTE = f"git@github.com:{OWNER}/github-garden.git"
EMAIL = "285931751+monicaffy108-alt@users.noreply.github.com"  # GitHub noreply 邮箱
USER_NAME = "monicaffy108-alt"                 # git 提交显示的名字
TZ = dt.timezone(dt.timedelta(hours=8))        # 时区：北京时间
COLOR_SEED = "github-garden-colors-v1"         # 随机种子（改这个会改变每天提交数量的分布）
# ===============================


def noise(label):
    """用 SHA256 生成稳定的 0~1 随机数，同一个 label 永远返回同一个值。"""
    digest = hashlib.sha256(f"{COLOR_SEED}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def daily_target(day):
    """每天生成 1~12 条合成提交，包含周级波动、周末减少、偶尔高峰。"""
    week = day - dt.timedelta(days=day.weekday())
    weekly = noise(f"week:{week}")
    count = 1 + int(1.8 * weekly + 4 * noise(f"jitter:{day}"))
    if day.weekday() >= 5:
        count = max(1, int(count * 0.65))       # 周末减少 35%
    if noise(f"burst:{day}") < 0.09:
        count += 4 + int(4 * weekly)            # 9% 概率出现小高峰
    return min(12, count)                        # 最多 12 条


def git(repo, *args, env=None):
    """执行 git 命令并返回输出。"""
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        text=True, capture_output=True, env=env,
    ).stdout.strip()


def dates(days, today):
    """生成从今天往前 days 天的日期列表。"""
    if not 1 <= days <= 366:
        raise ValueError("days must be between 1 and 366")
    return [today - dt.timedelta(days=i) for i in reversed(range(days))]


def run(repo, days, push=True):
    repo = repo.resolve()
    if repo == Path("/") or repo == Path.home():
        raise ValueError("Use a dedicated worktree, not a home/root directory")
    if not (repo / ".git").is_dir():
        raise ValueError("Clone the dedicated github-garden repository first")
    if git(repo, "rev-parse", "--show-toplevel") != str(repo):
        raise ValueError("Not the worktree root")
    if git(repo, "remote", "get-url", "origin") != REMOTE:
        raise ValueError("Refusing to touch a different repository")
    if git(repo, "branch", "--show-current") != "main":
        raise ValueError("Expected the dedicated repository main branch")
    if git(repo, "status", "--porcelain"):
        raise ValueError("Worktree has uncommitted changes; refusing to proceed")

    git(repo, "config", "user.name", USER_NAME)
    git(repo, "config", "user.email", EMAIL)

    created = 0
    today = dt.datetime.now(TZ).date()
    generated_at = dt.datetime.now(TZ).isoformat()

    for day in dates(days, today):
        for slot in range(1, daily_target(day) + 1):
            # 第1条放在 days/，其余放在 entries/日期/
            relative = (f"days/{day.isoformat()}.json" if slot == 1 else
                        f"entries/{day.isoformat()}/{slot:02d}.json")
            target = repo / relative

            if target.exists():
                # 文件已存在且已提交 → 跳过（幂等）
                git(repo, "ls-files", "--error-unmatch", relative)
                continue

            # 创建 JSON 记录文件
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({
                "kind": "synthetic-contribution-garden",
                "calendar_date": day.isoformat(),
                "slot": slot,
                "color_seed": COLOR_SEED,
                "generated_at": generated_at,
                "notice": "Automatically generated; not genuine development activity.",
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            # 伪造提交时间（上午9点开始，每条间隔15分钟）
            timestamp = (dt.datetime.combine(day, dt.time(9), TZ) +
                         dt.timedelta(minutes=15 * slot)).isoformat()
            env = dict(os.environ, GIT_AUTHOR_DATE=timestamp, GIT_COMMITTER_DATE=timestamp)

            git(repo, "add", "--", relative)
            git(repo, "commit", "-m", f"chore(garden): synthetic record {slot} for {day}", env=env)
            created += 1

    if push:
        git(repo, "push", "origin", "main")

    print(json.dumps({"created": created, "days": days, "pushed": push}))
    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path, required=True,
                        help="github-garden 仓库的本地路径")
    parser.add_argument("--days", type=int, default=1,
                        help="1 = 只跑今天（日常运行）；365 = 补一整年历史")
    parser.add_argument("--no-push", action="store_true",
                        help="只本地生成，不推送（用于测试）")
    args = parser.parse_args()

    try:
        dates(args.days, dt.datetime.now(TZ).date())
    except ValueError as exc:
        parser.error(str(exc))

    if not (args.worktree / ".git").is_dir():
        parser.error("The dedicated repository must already be cloned")

    # 文件锁，防止重复运行
    with (args.worktree / ".git" / "garden.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            run(args.worktree, args.days, not args.no_push)
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"Git operation failed (exit {exc.returncode}); inspect the worktree.") from None
        except ValueError as exc:
            parser.error(str(exc))


if __name__ == "__main__":
    main()
