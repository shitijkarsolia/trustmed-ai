# Environment Setup Guide

This guide explains how to configure environment variables for TrustMed AI.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual credentials:**
   ```bash
   nano .env
   # or use your preferred editor
   ```

3. **Never commit `.env` to git** (it's already in `.gitignore`)

## Required Environment Variables

### AWS Configuration

#### `AWS_REGION` (Required)
The AWS region where your Bedrock resources are deployed.
- Example: `us-east-1`, `us-west-2`
- Default: None (must be set)

#### `BEDROCK_KB_ID` (Required)
Your AWS Bedrock Knowledge Base ID.
- Find this in: AWS Console → Bedrock → Knowledge Bases
- Example: `CVSWBQ5BFR`

#### `BEDROCK_MODEL_ARN` (Required)
The Amazon Bedrock model to use for generation.
- Options:
  - `meta.llama3-8b-instruct-v1:0` (recommended)
  - `mistral.mistral-small-2402-v1:0`
  - `anthropic.claude-v2`

#### `BEDROCK_DATA_SOURCE_ID` (For sync operations)
Your Bedrock Knowledge Base data source ID.
- Find this in: AWS Console → Bedrock → Knowledge Bases → Data Sources

### Reddit API Configuration (For Data Collection)

#### `REDDIT_CLIENT_ID` (Required for scraping)
Your Reddit application client ID.

**How to get it:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Copy the string under "personal use script"

#### `REDDIT_CLIENT_SECRET` (Required for scraping)
Your Reddit application secret key.

**How to get it:**
1. Same process as client ID
2. Copy the "secret" value

#### `REDDIT_USER_AGENT` (Optional)
A descriptive string identifying your application.
- Default: `TrustMedAI Health Forum Collector v1.0`

## AWS Credentials Setup

### Option 1: AWS CLI (Recommended)

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### Option 2: Environment Variables (Less Secure)

Add to your `.env` file:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
```

⚠️ **Security Warning:** Never commit AWS credentials to git!

## Loading Environment Variables

### For Python Scripts

The application automatically loads environment variables using `os.getenv()`.

### Manual Loading (if needed)

Install python-dotenv:
```bash
pip install python-dotenv
```

Load in your script:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Verification

### Test AWS Connection
```bash
cd CODE/app
python -c "import boto3; print(boto3.client('bedrock-agent', region_name='us-east-1'))"
```

### Test Environment Variables
```bash
python -c "import os; print('AWS_REGION:', os.getenv('AWS_REGION'))"
```

## Troubleshooting

### "Environment variable is required" Error
Make sure you've:
1. Created a `.env` file from `.env.example`
2. Set all required variables
3. Are running commands from the correct directory

### AWS Credentials Not Found
- Check that `aws configure` has been run
- Or verify `.env` has AWS credentials set
- Ensure your AWS IAM user has necessary permissions:
  - `bedrock:InvokeModel`
  - `bedrock:RetrieveAndGenerate`
  - `s3:PutObject` (for data upload)

### Reddit API Errors
- Verify your Reddit app is set to "script" type
- Check that credentials are correctly copied
- Ensure no extra spaces in the `.env` file

## Security Best Practices

1. ✅ **DO:** Keep `.env` in `.gitignore`
2. ✅ **DO:** Use AWS IAM roles when possible
3. ✅ **DO:** Rotate credentials regularly
4. ❌ **DON'T:** Commit `.env` to version control
5. ❌ **DON'T:** Share credentials in chat/email
6. ❌ **DON'T:** Use production credentials for development

## Example `.env` File

```bash
# AWS
AWS_REGION=us-east-1
BEDROCK_KB_ID=CVSWBQ5BFR
BEDROCK_MODEL_ARN=meta.llama3-8b-instruct-v1:0
KB_VECTOR_RESULTS=8

# Reddit (only needed for data collection)
REDDIT_CLIENT_ID=abc123def456
REDDIT_CLIENT_SECRET=xyz789uvw012
REDDIT_USER_AGENT=TrustMedAI Health Forum Collector v1.0
```

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

