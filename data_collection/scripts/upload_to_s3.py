#!/usr/bin/env python3
"""
Upload the normalized contents under `to_upload/` into an S3 bucket so the
Bedrock Knowledge Base can ingest them directly.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import typer

ROOT = Path(__file__).resolve().parents[2]
TO_UPLOAD_DIR = ROOT / "to_upload"

cli = typer.Typer(help=__doc__)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def build_s3_key(path: Path, prefix: str) -> str:
    rel_path = path.relative_to(TO_UPLOAD_DIR).as_posix()
    if not prefix:
        return rel_path
    cleaned_prefix = prefix.strip("/")
    return f"{cleaned_prefix}/{rel_path}"


def upload_file(client, bucket: str, key: str, path: Path) -> None:
    content_type, _ = mimetypes.guess_type(path.name)
    extra_args = {"ContentType": content_type or "text/plain"}
    client.upload_file(str(path), bucket, key, ExtraArgs=extra_args)


@cli.command()
def run(
    bucket: str = typer.Option(..., "--bucket", help="Destination S3 bucket."),
    prefix: str = typer.Option(
        "",
        "--prefix",
        help="Optional S3 key prefix, e.g., 'trustmed-ai/'.",
    ),
    region: str = typer.Option(
        os.getenv("AWS_REGION", "us-east-1"),
        "--region",
        help="AWS region for the S3 client (defaults to AWS_REGION env var).",
    ),
) -> None:
    """
    Upload every file in `to_upload/` to the specified bucket/prefix.
    """
    if not TO_UPLOAD_DIR.exists():
        raise typer.Exit(f"No `to_upload/` directory found at {TO_UPLOAD_DIR}")

    client = boto3.client("s3", region_name=region)
    uploaded = 0
    failed = 0

    for file_path in iter_files(TO_UPLOAD_DIR):
        key = build_s3_key(file_path, prefix)
        try:
            upload_file(client, bucket, key, file_path)
            uploaded += 1
            typer.echo(f"[upload] s3://{bucket}/{key}")
        except (ClientError, BotoCoreError) as err:
            failed += 1
            typer.echo(f"[error] {file_path} -> {key}: {err}")

    typer.echo(
        f"[summary] Uploaded: {uploaded}, Failed: {failed}, Bucket: {bucket}, Prefix: {prefix or '(root)'}"
    )


if __name__ == "__main__":
    cli()

