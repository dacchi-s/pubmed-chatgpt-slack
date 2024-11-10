import openai
from openai import OpenAI
import os
import requests
import xmltodict
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import json
import re

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

PUBMED_QUERIES = os.getenv("PUBMED_QUERIES").split(',')

PUBMED_PUBTYPES = [
    "Journal Article",
    "Books and Documents",
    "Clinical Trial",
    "Meta-Analysis",
    "Randomized Controlled Trial",
    "Review",
    "Systematic Review",
]
PUBMED_TERM = 1

PROMPT_PREFIX = (
    "You are a highly educated and trained researcher. Please explain the following paper in Japanese, separating the title and summary with line breaks. Be sure to write the main points in bullet-point format."
)

def main():
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    today = datetime.now()
    yesterday = today - timedelta(days=PUBMED_TERM)
    MAX_ARTICLES_PER_MESSAGE = 6

    for query in PUBMED_QUERIES:
        while True:
            try:
                ids = get_paper_ids_on(yesterday, query)
                print(f"Number of paper IDs for {query}: {len(ids)}")
                output = ""
                paper_count = 0
                message_count = 0
                for i, id in enumerate(ids):
                    summary = get_paper_summary_by_id(id)
                    pubtype_check_result = check_pubtype(summary["pubtype"])
                    print(f"ID {id} pubtype: {summary['pubtype']}, Check result: {pubtype_check_result}")
                    if not pubtype_check_result:
                        continue
                    paper_count += 1
                    abstract = get_paper_abstract_by_id(id)
                    print(f"ID {id} title: {summary['title']}")
                    print(f"ID {id} abstract: {abstract}\n")
                    input_text = f"\ntitle: {summary['title']}\nabstract: {abstract}"

                    response = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": PROMPT_PREFIX + "\n" + input_text,
                            },
                        ],
                        model="gpt-4o-mini",
                    )
                    
                    content = response.choices[0].message.content.strip()
                    
                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{id}"
                    output += f"New PubMed Article Notification ({query})\n\n{content}\n\n{pubmed_url}\n\n\n"
                    if paper_count % MAX_ARTICLES_PER_MESSAGE == 0:
                        message_count += 1
                        post_to_slack(SLACK_WEBHOOK_URL, output, query, to_yyyymmdd(yesterday), message_count)
                        output = ""
                if paper_count % MAX_ARTICLES_PER_MESSAGE != 0 or paper_count == 0:
                    message_count += 1
                    post_to_slack(SLACK_WEBHOOK_URL, output, query, to_yyyymmdd(yesterday), message_count)
                if paper_count == 0:
                    output += f"New PubMed Article Notification ({query})\n\nNo new articles\n\n"

                break
                
            except openai.RateLimitError as e:
                print("Rate limit exceeded. Waiting for 300 seconds before retrying.")
                time.sleep(300)
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(60)

def to_yyyymmdd(date):
    return date.strftime("%Y/%m/%d")

def get_paper_ids_on(date, query):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&sort=pub_date&term={query}&mindate={to_yyyymmdd(date)}&maxdate={to_yyyymmdd(date)}&retmax=1000&retstart=0"
    res = requests.get(url).json()
    return res["esearchresult"]["idlist"]

def get_paper_summary_by_id(id):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={id}"
    res = requests.get(url).json()
    return res["result"][id]

def get_paper_abstract_by_id(id):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id={id}"
    res = requests.get(url).text
    xml_dict = xmltodict.parse(res)
    abstract = xml_dict["PubmedArticleSet"]["PubmedArticle"]["MedlineCitation"]["Article"].get("Abstract", {}).get("AbstractText", "")
    return abstract if abstract else ""

def check_pubtype(pubtypes):
    return any(pubtype in PUBMED_PUBTYPES for pubtype in pubtypes)

def post_to_slack(webhook_url, text, query, search_date, message_count):
    if not webhook_url:
        print("Error: Slack webhook URL is not set. Skipping Slack notification.")
        return

    header = f"New Article Notification ({query}) - Search Date: {search_date}"
    
    if not text.strip():
        text = "No new articles"
    
    # Split the text into individual paper entries
    paper_entries = text.strip().split('\n\n\n')
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*New Article Notification - Message {message_count}*"
            }
        }
    ]
    
    for entry in paper_entries:
        if entry.strip():
            # Split each entry into title, content, and URL
            parts = entry.split('\n\n')
            if len(parts) >= 3:
                title = parts[0].replace('New PubMed Article Notification', '').strip()
                content = '\n'.join(parts[1:-1])
                url = parts[-1]
                
                # Replace bullet points with Slack-friendly format
                content = re.sub(r'^[-*]\s', '• ', content, flags=re.MULTILINE)
                
                # Replace **bold** with *bold* for Slack
                content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
                
                # Replace ### headers with *bold* for Slack
                content = re.sub(r'^###\s*(.*?)$', r'*\1*', content, flags=re.MULTILINE)
                
                blocks.extend([
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title}*\n{content}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"<{url}|PubMed URL>"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    }
                ])

    payload = {
        "blocks": blocks
    }

    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Slack: {e}")
    else:
        if response.status_code != 200:
            print(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
        else:
            print("Successfully posted to Slack")

if __name__ == "__main__":
    main()