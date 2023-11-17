import os
import requests
import xml.etree.ElementTree as ET
import argparse
import os
from tqdm import tqdm
import time
import json
from dotenv import load_dotenv

from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

MODEL = "gpt-4-1106-preview"



# Get the OpenAI key


def download_sitemap(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content  # Return the raw byte content
    except requests.RequestException as e:
        print(f"Error downloading the sitemap: {e}")
        return None

def save_sitemap(content, filepath):
    with open(filepath, 'wb') as file:
        file.write(content)

def parse_sitemap(xml_content):
    try:
        root = ET.fromstring(xml_content)
        # Define the namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Find all 'url' elements and extract the 'loc' text
        urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]
        return urls
    except ET.ParseError as e:
        print(f"Error parsing the XML content: {e}")
        return []

def scrape_and_save(url, folder):
    try:
        response = requests.get(url)
        response.raise_for_status()
        filename = url.split('/')[-1] or "index.html"
        path = os.path.join(folder, filename)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(response.text)
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")


def command_download(args):
    xml_content = download_sitemap(args.url)
    if xml_content:
        sitemap_path = 'sitemap.xml'
        save_sitemap(xml_content, sitemap_path)
        print(f"Sitemap saved as {sitemap_path}")

        urls = parse_sitemap(xml_content)
        data_folder = "data"
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        print(f"Found urls: {len(urls)}")
        for url in urls:
            scrape_and_save(url, data_folder)
            print(f"Saved content from {url}")


SYSTEM_PROMPT = """
You are helpful SEO assistant. Skip filler words, provide actionable advice.
Rules to suggest internal linking:
Consider this groups of pages:
- Legal Terms Pages
- Examples Section
- Articles
- Main Pages
- Other Legal Terms

Avoid linking page to itself.

Write a reason why you think page is good fit, suggest place in text what to change.
Output schema in JSON format:
Return list of suggestions.
- suggestions - root element, a list:
- action: str what to do
- reason: str what to do
- from: str in html
- to: str to change it with

Example response:
{
  "suggestions": [{'action': 'Add internal link', 'reason': "The term 'breach of contract' is mentioned as an example of a cause of action, and a corresponding page on 'breach' exists in the sitemap.", 'from': 'if someone broke a contract with you, your cause of action would be breach of contract.', 'to': 'if someone broke a contract with you, your cause of action would be <a href="https://detangle.ai/legal-terms/breach">breach of contract</a>.'}]
}
"""

def suggest_interlink_for_page(page):
    with open(f'data/{page}', 'r') as file:
        pagecontent = file.read()
    with open('sitemap.xml', 'r') as file:
        sitemap = file.read()

    content = f"""Here is page content and sitemap. Suggest what links I can add.
    page content:
    {pagecontent}
    sitemap:
    {sitemap}
    """
    # print(f"debug model: {content}")
    response = client.chat.completions.create(
      model=MODEL,
      response_format={ "type": "json_object" },
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
      ]
    )
    json_response = response.choices[0].message.content
    dict_response = json.loads(json_response)
    return dict_response['suggestions']

def suggest_and_prepare_report(page):
    try:
      suggestions = suggest_interlink_for_page(page)
      # print(suggestions)
      list_of_suggestion = [f"### {suggestion['action']}\n{suggestion['reason']}\nDiff:\n```diff\n-{suggestion['from']}\n+{suggestion['to']}\n```\n" for suggestion in suggestions]

      text = f"""
  ## Page {page}
  List of suggestions:
  """ + '\n\n'.join(list_of_suggestion)
      return text
    except:
        print(suggestions)


def command_suggest(args):
    if args.page:
      print(f"Suggesting interlinking for {args.page}")

    text = suggest_and_prepare_report(args.page)
    data_folder = "out"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    with open(f"out/{args.page}.md", 'w') as file:
        file.write(text)
    print(text)


def command_suggest_all(args):
    print("suggesting-all")
    for file in tqdm(os.listdir('data')):
        # suggest_interlink_for_page(file)
        text = suggest_and_prepare_report(file)
        with open('out/report.md', 'a') as report_file:
            report_file.write(text + '\n')

def main(args):
    if args.command == 'download':
        command_download(args)
    elif args.command == 'suggest':
        command_suggest(args)
    elif args.command == 'suggest-all':
        command_suggest_all(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download a sitemap and scrape pages.')
    subparsers = parser.add_subparsers(dest='command')

    download_parser = subparsers.add_parser('download', help='Download a sitemap.')
    download_parser.add_argument('url', type=str, help='URL of the sitemap.xml file')

    suggest_parser = subparsers.add_parser('suggest', help='Suggest interlinking for a page.')
    suggest_parser.add_argument('page', type=str, help='URL of the page to suggest interlinking for')

    suggest_parser = subparsers.add_parser('suggest-all', help='Suggest interlinking for all pages.')

    args = parser.parse_args()
    main(args)
