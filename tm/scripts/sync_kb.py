#!/usr/bin/env python3
"""
Utility for kicking off and optionally monitoring a Bedrock Knowledge Base
ingestion job (a.k.a. “sync”). Set the same IDs that Chainlit uses via
environment variables, or pass them with CLI flags.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trigger a Bedrock Knowledge Base ingestion job."
    )
    parser.add_argument(
        "--kb-id",
        default=os.getenv("BEDROCK_KB_ID"),
        help="Knowledge Base ID (default: BEDROCK_KB_ID env var).",
    )
    parser.add_argument(
        "--data-source-id",
        default=os.getenv("BEDROCK_DATA_SOURCE_ID"),
        help="Data Source ID attached to the KB (default: BEDROCK_DATA_SOURCE_ID env var).",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION", "us-east-1"),
        help="AWS Region for Bedrock (default: AWS_REGION env var or us-east-1).",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll the ingestion job until it finishes.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=15,
        help="Delay between status checks when --wait is enabled.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    missing = []
    if not args.kb_id:
        missing.append("BEDROCK_KB_ID or --kb-id")
    if not args.data_source_id:
        missing.append("BEDROCK_DATA_SOURCE_ID or --data-source-id")

    if missing:
        raise SystemExit(
            "Missing required configuration: " + ", ".join(missing)
        )


def start_ingestion_job(client, kb_id: str, data_source_id: str) -> dict:
    response = client.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=data_source_id,
    )
    return response.get("ingestionJob", {})


def wait_for_job_completion(
    client, kb_id: str, data_source_id: str, job_id: str, poll_seconds: int
) -> str:
    terminal_states = {"FAILED", "COMPLETE", "STOPPED"}
    status = "UNKNOWN"

    while status not in terminal_states:
        time.sleep(poll_seconds)
        job = client.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            ingestionJobId=job_id,
        ).get("ingestionJob", {})
        status = job.get("status", "UNKNOWN")
        print(f"[sync_kb] Job {job_id} status: {status}")

    return status


def main():
    args = parse_args()
    validate_args(args)

    client = boto3.client("bedrock-agent", region_name=args.region)
    try:
        job = start_ingestion_job(client, args.kb_id, args.data_source_id)
    except (ClientError, BotoCoreError) as aws_err:
        print(f"[sync_kb] Failed to start ingestion job: {aws_err}", file=sys.stderr)
        raise SystemExit(1) from aws_err

    job_id = job.get("ingestionJobId")
    status = job.get("status", "UNKNOWN")
    print(f"[sync_kb] Started ingestion job {job_id} (status: {status})")

    if args.wait and job_id:
        try:
            terminal_status = wait_for_job_completion(
                client,
                args.kb_id,
                args.data_source_id,
                job_id,
                args.poll_seconds,
            )
        except (ClientError, BotoCoreError) as aws_err:
            print(
                f"[sync_kb] Failed while polling ingestion job: {aws_err}",
                file=sys.stderr,
            )
            raise SystemExit(1) from aws_err

        if terminal_status != "COMPLETE":
            print(
                f"[sync_kb] Job {job_id} finished with status {terminal_status}",
                file=sys.stderr,
            )
            raise SystemExit(1)

        print(f"[sync_kb] Job {job_id} completed successfully.")


if __name__ == "__main__":
    main()

