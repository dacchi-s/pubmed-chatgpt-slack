# Daily PubMed Search with AI Summaries - Automated Slack Notifications

This tool is for medical researchers who need daily updates on PubMed articles. It automates searches, summarizes new research, and sends results to a Slack channel using OpenAI's GPT model.

## Overview

The tool performs daily searches with specific keywords, generates AI-powered summaries in Japanese, and posts results every morning at 7 AM to a designated Slack channel. This helps researchers stay updated efficiently.

## Features

- **Automated PubMed Searches**: Define keywords for specific topics to search daily.
- **AI Summaries**: Generates concise summaries in Japanese for easy understanding.
- **Slack Integration**: Posts results to Slack via Incoming Webhook.

## Requirements

- Raspberry Pi (or other server)
- Python 3.x
- OpenAI API Key
- Slack Webhook URL

## Installation

1. **Set up Python Environment**:
    ```bash
    python -V
    python3 -m venv project_env
    source project_env/bin/activate
    ```

2. **Install Required Libraries**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Slack Webhook**: Follow Slack’s instructions to create an Incoming Webhook URL.

Please refer to the following URL:
https://api.slack.com/messaging/webhooks

4. **Set Up OpenAI API Key**: Create an OpenAI account and get your API key.

Please refer to the following URL:
https://platform.openai.com/docs/quickstart

## Usage

### Environment Variable Configuration

Create a .env file with the following content:
```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Slack Webhook URL
SLACK_WEBHOOK_URL=https://your_slack_webhook_url

# PubMed search queries, separated by commas
PUBMED_QUERIES=keyword1 keyword2, keyword3, keyword4, keyword5 keyword6 keyword7
```

### Crontab Configuration
```
crontab -e
```

add a following line:
```
0 7 * * * /home/user/hoge/venv/bin/python /home/user/fuga/huge/Pubmed_ChatGPT_Slack_multiple_keywords.py
```

This will cause the script to run every morning at 7:00 AM.
