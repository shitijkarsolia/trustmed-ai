#!/usr/bin/env python3
"""
Normalize scraped authoritative and forum content into text files that are ready
for ingestion into the Bedrock Knowledge Base. Outputs live under `to_upload/`.
"""
from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import typer

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data_collection" / "data"
AUTH_SRC = DATA_ROOT / "auth_src" / "medical_articles"
AUTH_METADATA_FILE = AUTH_SRC / "articles_metadata.json"
FORUM_SRC = DATA_ROOT / "forum_src"
TO_UPLOAD_ROOT = ROOT / "to_upload"
MANIFEST_PATH = TO_UPLOAD_ROOT / "manifest.json"

FORUM_FILES = [
    "diabetes_threads_combined.json",
    "heart_disease_threads_combined.json",
]

AUTHORITATIVE_NOISE_PATTERNS = [
    "there is a problem with",
    "from mayo clinic to your inbox",
    "sign up for free and stay up to date",
    "thank you for subscribing",
    "sorry something went wrong",
    "errorinclude a valid email address",
    "erroremail field is required",
]

cli = typer.Typer(help=__doc__)
_manifest_entries: List[dict] = []


def reset_manifest() -> None:
    """Clear the in-memory manifest and remove any previous file."""
    _manifest_entries.clear()
    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()


def add_manifest_entry(key: str, entry: dict) -> None:
    _manifest_entries.append({"key": key, **entry})


def write_manifest() -> None:
    ensure_dir(TO_UPLOAD_ROOT)
    MANIFEST_PATH.write_text(
        json.dumps(_manifest_entries, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def collapse_blank_lines(lines: Iterable[str]) -> List[str]:
    cleaned: List[str] = []
    previous_blank = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
        else:
            cleaned.append(stripped)
            previous_blank = False
    return cleaned


def remove_noise(lines: Iterable[str]) -> List[str]:
    cleaned: List[str] = []
    for line in lines:
        lower = line.lower().strip()
        if any(pattern in lower for pattern in AUTHORITATIVE_NOISE_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def sanitize_authoritative_text(raw_text: str) -> str:
    lines = raw_text.splitlines()
    lines = remove_noise(lines)
    lines = collapse_blank_lines(lines)
    return "\n".join(lines).strip()


@dataclass
class ArticleMetadata:
    title: str
    source: str
    url: str
    filename: str
    collected_at: Optional[str] = None
    topic: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ArticleMetadata":
        return cls(
            title=data.get("title", "Untitled"),
            source=data.get("source", "Unknown Source"),
            url=data.get("url", "Unknown URL"),
            filename=data["filename"],
            collected_at=data.get("collected_at"),
            topic=data.get("topic"),
        )

    def header_block(self) -> str:
        header_lines = [
            f"Title: {self.title}",
            f"Source: {self.source}",
            f"URL: {self.url}",
            f"Canonical URL: {self.url}",
            f"Filename: {self.filename}",
        ]
        if self.collected_at:
            header_lines.append(f"Collected: {self.collected_at}")
        if self.topic:
            header_lines.append(f"Topic: {self.topic}")
        header_lines.append("=" * 79)
        return "\n".join(header_lines)


def load_article_metadata() -> List[ArticleMetadata]:
    if not AUTH_METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file missing: {AUTH_METADATA_FILE}")

    with AUTH_METADATA_FILE.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [ArticleMetadata.from_dict(item) for item in raw]


def process_authoritative_articles() -> int:
    metadata_entries = load_article_metadata()
    written = 0
    for entry in metadata_entries:
        source_slug = slugify(entry.source)
        dst_dir = TO_UPLOAD_ROOT / "authoritative" / source_slug
        ensure_dir(dst_dir)

        src_path = AUTH_SRC / entry.filename
        if not src_path.exists():
            typer.echo(f"[auth] Missing file: {src_path}")
            continue

        raw_text = src_path.read_text(encoding="utf-8")
        cleaned_body = sanitize_authoritative_text(raw_text)
        if not cleaned_body:
            typer.echo(f"[auth] Skipping empty article: {src_path}")
            continue

        output_text = entry.header_block() + "\n\n" + cleaned_body + "\n"
        dst_path = dst_dir / entry.filename
        dst_path.write_text(output_text, encoding="utf-8")

        rel_key = dst_path.relative_to(TO_UPLOAD_ROOT).as_posix()
        add_manifest_entry(
            rel_key,
            {
                "type": "authoritative",
                "canonical_url": entry.url,
                "title": entry.title,
                "source": entry.source,
                "collected_at": entry.collected_at,
                "topic": entry.topic,
            },
        )
        written += 1
    return written


def sanitize_block(text: Optional[str]) -> str:
    if not text:
        return ""
    text = textwrap.dedent(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_forum_thread(thread: dict) -> str:
    fields = [
        f"Thread ID: {thread.get('id')}",
        f"Subreddit: {thread.get('subreddit')}",
        f"Title: {thread.get('title')}",
        f"Author: {thread.get('author')}",
        f"Created UTC: {thread.get('created_utc')}",
        f"Score: {thread.get('score')}",
        f"Num Comments: {thread.get('num_comments')}",
        f"URL: {thread.get('url')}",
        f"Canonical URL: {thread.get('url')}",
        f"Collected: {thread.get('collected_at')}",
        "=" * 79,
    ]
    header = "\n".join(fields)
    body = sanitize_block(thread.get("selftext")) or "(No selftext provided.)"

    comments = thread.get("comments") or []
    lines = ["## Comments"]
    if not comments:
        lines.append("No comments captured.")
    else:
        for idx, comment in enumerate(comments, start=1):
            comment_text = sanitize_block(comment.get("body"))
            lines.append(
                f"{idx}. u/{comment.get('author')} "
                f"[score={comment.get('score')}, created={comment.get('created_utc')}]: "
                f"{comment_text or '(empty comment)'}"
            )

    comments_block = "\n".join(lines)
    return f"{header}\n\n{body}\n\n---\n{comments_block}\n"


def process_forum_file(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    written = 0
    for thread in data:
        subreddit = thread.get("subreddit", "unknown")
        dst_dir = TO_UPLOAD_ROOT / "forums" / slugify(subreddit)
        ensure_dir(dst_dir)

        thread_id = thread.get("id") or f"thread-{written}"
        dst_path = dst_dir / f"{thread_id}.txt"
        dst_path.write_text(format_forum_thread(thread), encoding="utf-8")

        rel_key = dst_path.relative_to(TO_UPLOAD_ROOT).as_posix()
        add_manifest_entry(
            rel_key,
            {
                "type": "forum",
                "canonical_url": thread.get("url"),
                "title": thread.get("title"),
                "source": thread.get("subreddit"),
                "collected_at": thread.get("collected_at"),
                "thread_id": thread.get("id"),
            },
        )
        written += 1
    return written


def process_forum_threads() -> int:
    written = 0
    for filename in FORUM_FILES:
        src_path = FORUM_SRC / filename
        if not src_path.exists():
            typer.echo(f"[forum] Missing file: {src_path}")
            continue
        written += process_forum_file(src_path)
    return written


@cli.command("run")
def run() -> None:
    """Generate cleaned content under `to_upload/`."""
    ensure_dir(TO_UPLOAD_ROOT)
    reset_manifest()
    typer.echo(f"[init] Writing outputs to {TO_UPLOAD_ROOT}")

    auth_written = process_authoritative_articles()
    typer.echo(f"[auth] Wrote {auth_written} cleaned articles.")

    forum_written = process_forum_threads()
    typer.echo(f"[forum] Wrote {forum_written} forum threads.")
    write_manifest()
    typer.echo(f"[manifest] Recorded {len(_manifest_entries)} entries at {MANIFEST_PATH}")


if __name__ == "__main__":
    cli()

