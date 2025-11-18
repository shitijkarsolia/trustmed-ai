"""
TrustMed AI - Chainlit Application wired to AWS Bedrock Knowledge Base.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import chainlit as cl

BANNER_AUTHOR = "banner"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_KB_ID = os.getenv("BEDROCK_KB_ID","CVSWBQ5BFR")
BEDROCK_MODEL_ARN = "meta.llama3-8b-instruct-v1:0"
# BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN")

_bedrock_client = None

_default_manifest_path = (
    Path(os.getenv("CONTENT_MANIFEST_PATH"))
    if os.getenv("CONTENT_MANIFEST_PATH")
    else Path(__file__).resolve().parent.parent / "to_upload" / "manifest.json"
)
CONTENT_PREFIX = os.getenv("CONTENT_PREFIX", "to_upload/")


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    lookup = {}
    prefix = CONTENT_PREFIX.rstrip("/")
    for entry in entries:
        key = entry.get("key")
        if not key:
            continue
        lookup[key] = entry
        if prefix:
            lookup[f"{prefix}/{key}"] = entry
    return lookup


MANIFEST_LOOKUP = load_manifest(_default_manifest_path)


def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            "bedrock-agent-runtime",
            region_name=AWS_REGION,
        )
    return _bedrock_client


def format_citations(citations: List[dict]) -> Tuple[str, List[cl.Text]]:
    """
    Convert the citations returned by Bedrock into a markdown block and Chainlit elements.
    """
    if not citations:
        return "", []

    citation_lines = []
    source_elements: List[cl.Text] = []
    source_idx = 1

    for citation in citations:
        for ref in citation.get("retrievedReferences", []):
            snippet = ref.get("content", {}).get("text") or "No snippet available."
            s3_uri = ref.get("location", {}).get("s3Location", {}).get("uri")
            filename = s3_uri.split("/")[-1] if s3_uri else f"source_{source_idx}"

            manifest_entry = None
            if s3_uri:
                parsed = urlparse(s3_uri)
                if parsed.scheme == "s3":
                    manifest_entry = MANIFEST_LOOKUP.get(parsed.path.lstrip("/"))

            display_name = (
                manifest_entry.get("title") if manifest_entry else filename
            ) or filename
            canonical_url = (
                manifest_entry.get("canonical_url") if manifest_entry else s3_uri
            ) or s3_uri

            if canonical_url:
                link_text = f"[{display_name}]({canonical_url})"
            else:
                link_text = display_name

            citation_lines.append(f"{source_idx}. {link_text}")
            source_elements.append(
                cl.Text(
                    name=f"Source {source_idx}",
                    content=snippet,
                    display="inline",
                )
            )
            source_idx += 1

    citation_block = "\n\n**Sources:**\n" + "\n".join(citation_lines)
    return citation_block, source_elements


@cl.on_chat_start
async def on_chat_start():
    """
    Called when a new chat session starts.
    """
    # Read the chainlit.md file and send it as welcome message
    chainlit_md_path = Path(__file__).parent / "chainlit.md"
    if chainlit_md_path.exists():
        welcome_content = chainlit_md_path.read_text(encoding="utf-8")
    else:
        welcome_content = """
# Welcome to TrustMed AI! 

Ask about Type II Diabetes, Heart Disease, medications, or symptoms to see the
RAG pipeline retrieve citations from both authoritative and forum sources.
        """
    
    await cl.Message(
        content=welcome_content,
        author=BANNER_AUTHOR,
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Called when a user sends a message. Streams the prompt through Bedrock's
    retrieve_and_generate API and returns the grounded answer with citations.
    """
    response_msg = cl.Message(author=BANNER_AUTHOR, content="")
    await response_msg.send()

    missing_configs = []
    if not BEDROCK_KB_ID:
        missing_configs.append("BEDROCK_KB_ID")
    if not BEDROCK_MODEL_ARN:
        missing_configs.append("BEDROCK_MODEL_ARN")

    if missing_configs:
        response_msg.content = (
            "⚠️ Missing configuration: "
            + ", ".join(missing_configs)
            + ". Please export these environment variables and restart Chainlit."
        )
        await response_msg.update()
        return

    try:
        # Provide a minimal delay so the UI shows a spinner even for fast responses.
        await asyncio.sleep(0.2)

        client = get_bedrock_client()
        bedrock_response = client.retrieve_and_generate(
            input={"text": message.content},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": BEDROCK_KB_ID,
                    "modelArn": BEDROCK_MODEL_ARN,
                },
            },
        )

        answer_text = bedrock_response.get("output", {}).get(
            "text",
            "No response text was returned by Bedrock.",
        )
        citation_block, source_elements = format_citations(
            bedrock_response.get("citations", [])
        )

        response_msg.content = answer_text + citation_block
        response_msg.elements = source_elements
    except (ClientError, BotoCoreError) as aws_err:
        response_msg.content = f"⚠️ Bedrock error: {aws_err}"
    except Exception as unexpected_err:  # pragma: no cover
        response_msg.content = f"⚠️ Unexpected error: {unexpected_err}"

    await response_msg.update()


@cl.on_stop
async def on_stop():
    """
    Called when the user stops the conversation.
    """
    await cl.Message(
        content="Session ended. Thank you for using TrustMed AI!",
        author=BANNER_AUTHOR,
    ).send()

