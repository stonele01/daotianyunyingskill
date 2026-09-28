#!/usr/bin/env python3
"""Publish one report and atomically refresh the static report index."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
import subprocess
from pathlib import Path

from frame_evidence import validate_visual_evidence, validate_report_images
from transcript_reading import enrich
from progress import stage, progress


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "assets" / "templates"
ICON_ASSETS = ROOT / "assets" / "icons"
UI_ASSETS = ROOT / "assets" / "ui"
ACCOUNT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


DEFAULT_WORKSPACE = Path(os.getenv("DOUYIN_INSIGHT_WORKSPACE") or ROOT / "workspace").expanduser().resolve()
DEFAULT_SITE = DEFAULT_WORKSPACE / "site"


def date_only(value: object) -> str:
    return str(value or "")[:10].replace(".", "-")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def embed_transcripts(payload: dict, data_dir: Path) -> None:
    """Embed qualified spoken text so file:// reports can show it without fetch/CORS."""
    for analysis in payload.get("workAnalyses", []):
        value = str(analysis.get("spokenScriptPath") or "")
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = (data_dir / path).resolve()
        if path.is_file():
            analysis["spokenScript"] = path.read_text(encoding="utf-8", errors="ignore").strip()


def creator_homepage(payload: dict) -> str:
    sec_id = str(payload.get("secUserId") or payload.get("profile", {}).get("secUserId") or "")
    return f"https://www.douyin.com/user/{sec_id}" if re.fullmatch(r"[A-Za-z0-9_-]+", sec_id) else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--node", default="node", help="Node.js executable for pre-write JavaScript syntax validation")
    parser.add_argument("--preserve-layout", action="store_true", help="Keep this account's existing custom HTML shell while replacing its complete data payload")
    args = parser.parse_args()
    args.preserve_layout = False
    stage(5, f"为 {args.account} 更新详情页、首页索引和共用样式")
    if not ACCOUNT_PATTERN.fullmatch(args.account):
        raise SystemExit("账号只能包含字母、数字、下划线和连字符，长度不超过 64")
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    payload.pop("opportunities", None)
    for comment in payload.get("comments", []):
        comment.pop("opportunityId", None)
    payload["accountId"] = args.account
    output_dir = args.output_dir.resolve()
    # Publication consumes local data only; it does not load .env or fetch images.
    payload["avatar"] = payload.get("avatar") or payload.get("profile", {}).get("avatar") or ""
    errors = validate_visual_evidence(payload, output_dir)
    if errors:
        raise SystemExit("画面证据校验失败：" + "; ".join(errors))
    try:
        validate_report_images(payload, output_dir)
    except (ValueError, OSError) as error:
        raise SystemExit("报告图片校验失败：" + str(error)) from None
    embed_transcripts(payload, args.data.resolve().parent)
    enrich(payload)
    index_html = output_dir / "comment-insight-index.html"
    index_source = (TEMPLATES / "index.html").read_text(encoding="utf-8")

    existing_detail = output_dir / f"{args.account}.html"
    source = (existing_detail if args.preserve_layout and existing_detail.exists() else TEMPLATES / "report.html").read_text(encoding="utf-8")
    if args.preserve_layout and existing_detail.exists():
        match = re.search(r'const pageData=(.*?);\s*/\* INSIGHT_DATA_END', source, re.S)
        if not match or str(json.loads(match.group(1)).get('accountId')) != args.account:
            raise SystemExit("不能复用其他账号或无法核验账号的页面")
    start, end = "/* INSIGHT_DATA_START */", "/* INSIGHT_DATA_END */"
    if source.count(start) != 1 or source.count(end) != 1:
        raise SystemExit("详情页模板缺少唯一的数据注入标记")
    before, rest = source.split(start, 1)
    _, after = rest.split(end, 1)
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    detail = output_dir / f"{args.account}.html"
    rendered = before + start + f"\nconst pageData={embedded};\n" + end + after
    for html in (rendered, index_source):
        if re.search(r'<(?:script|img)\b[^>]*src=["\'](?:https?:)?//', html, re.I):
            raise SystemExit("报告模板含外链资源，拒绝发布")
        checked = subprocess.run([args.node, str(ROOT / "scripts" / "check_html_syntax.cjs")],
                                 input=html, text=True, encoding="utf-8", capture_output=True)
        if checked.returncode:
            raise SystemExit("报告 JavaScript 语法预检失败，未写盘：" + checked.stderr)
    # No report/assets/index writes until both templates and all visual references are valid.
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("icons", "ui", "vendor"):
        source_dir = ROOT / "assets" / name
        if source_dir.exists():
            shutil.copytree(source_dir, output_dir / "assets" / name, dirs_exist_ok=True)
    atomic_write(detail, rendered)
    atomic_write(index_html, index_source)

    index_path = output_dir / "comment-insight-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"updatedAt": "", "reports": []}
    previous = next((row for row in index.get("reports", []) if str(row.get("accountId")) == args.account), {})
    reports = [row for row in index.get("reports", []) if str(row.get("accountId")) != args.account]
    comment_count = len(payload.get("comments", []))
    updated_at = payload.get("updatedAt") or payload.get("run", {}).get("completedAt") or ""
    reports.append({
        "accountId": args.account,
        "displayName": payload.get("displayName") or previous.get("displayName") or args.account,
        "file": detail.name,
        "homepageUrl": creator_homepage(payload) or previous.get("homepageUrl", ""),
        "avatar": payload.get("avatar") or previous.get("avatar") or "",
        "followers": payload.get("followers", previous.get("followers", 0)),
        "works": payload.get("worksCount", len(payload.get("works", []))) if isinstance(payload.get("works"), list) else payload.get("works", previous.get("works", 0)),
        "lane": payload.get("lane") or previous.get("lane") or "未分类",
        "summary": payload.get("summary") or payload.get("bio") or previous.get("summary") or "评论分析报告",
        "commentCount": comment_count,
        "viralCount": len(payload.get("viralWorks", [])),
        "qualifiedWorkCount": len(payload.get("qualifiedWorkIds", [])),
        "collectionAt": payload.get("workWindow", {}).get("observedAt") or updated_at,
        "coverageStatus": payload.get("coverage", {}).get("status", "legacy"),
        "status": "completed" if comment_count > 0 else "pending",
        "executionAt": updated_at,
        "updatedAt": date_only(updated_at),
    })
    index["reports"] = sorted(reports, key=lambda row: str(row.get("executionAt", "")), reverse=True)
    index["updatedAt"] = date_only(updated_at) or index.get("updatedAt", "")
    readable = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    bundle = "window.COMMENT_INSIGHT_INDEX=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
    atomic_write(index_path, readable)
    atomic_write(output_dir / "comment-insight-index-data.js", bundle)
    progress("详情页与首页索引已写入", status="done")
    progress("检查页面显示、报告跳转和资源加载后完成交付", status="next")
    print(json.dumps({"accountId": args.account, "detailPage": str(detail), "indexPage": str(index_html), "status": "updated" if previous else "created"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
