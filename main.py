import asyncio
import os
import csv
import re
import requests
import xml.etree.ElementTree as ET
import argparse
from urllib.parse import urlparse
import os
from tqdm.asyncio import tqdm as async_tqdm
import time
import json
from dotenv import load_dotenv
import backoff
from openai import AsyncOpenAI, RateLimitError

from aiolimiter import AsyncLimiter

# Load environment variables from .env file
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
limiter = AsyncLimiter(5, 1)
MODEL = "gpt-4-1106-preview"

DATA_FOLDER = "data"

# Get the OpenAI key


def download_sitemap(url, sitemap_folder):
    print(f"donwloading sitemap {url} {sitemap_folder}")
    try:
        # Construct the sitemap URL
        sitemap_url = url if url.endswith('.xml') else url + '/sitemap.xml'

        # Define headers for the request
        headers = {'Accept': 'application/html', 'User-Agent': 'insomnia/8.3.0'}

        # Send a GET request to the sitemap URL
        response = requests.get(sitemap_url, headers=headers)
        response.raise_for_status()

        content = response.content
        root = ET.fromstring(content)

        # Define the namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Check if xml has nested sitemaps
        sitemaps = [sitemap.find('ns:loc', namespace).text for sitemap in root.findall('ns:sitemap', namespace)]
        if sitemaps:
            # If yes, call download_sitemap recursively for each nested sitemap
            for sitemap in sitemaps:
                sitemaps = download_sitemap(sitemap, sitemap_folder)

        filename = '__'.join(filter(None, urlparse(sitemap_url).path.split('/'))) or  "sitemap.xml"
        sitemap_path = os.path.join(sitemap_folder, filename)
        save_sitemap(content, sitemap_path)

        return content  # Return the raw byte content
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
        headers = {'Accept': 'application/html', 'User-Agent': 'insomnia/8.3.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        parsed_url = urlparse(url)
        filename = '__'.join(filter(None, parsed_url.path.split('/'))) or  "index.html"
        path = os.path.join(folder, filename)
        print(f"Saved content from {url} in {path}")
        with open(path, 'w', encoding='utf-8') as file:
            file.write(response.text)
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")


def command_download(args):
    hostname = urlparse(args.url).hostname
    sitemap_folder = os.path.join(DATA_FOLDER, hostname)
    if not os.path.exists(sitemap_folder):
        os.makedirs(sitemap_folder)
    download_sitemap(args.url, sitemap_folder)

    metadata = {}
    metadata['hostname'] = hostname
    metadata['urls'] = []
    xml_files = [f for f in os.listdir(sitemap_folder) if f.endswith(".xml")]
    for file in xml_files:
        with open(os.path.join(sitemap_folder, file), "r") as f:
            xml_content = f.read()
        urls = parse_sitemap(xml_content)
        print(f"Found urls: {len(urls)}")
        metadata['urls'].extend(urls)

    # save metadata json to sitemap_folder
    with open(os.path.join(sitemap_folder, 'metadata.json'), 'w') as json_file:
        json.dump(metadata, json_file)

    for url in metadata['urls']:
        scrape_and_save(url, sitemap_folder)



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
- to_url: url to add link to

Possible actions:
- Link to existing page - put it, when you have found a good candidate for existing page
- Content idea - use it when you have found an idea for new page, or it would be goot to add new page
- Other - user it, if you have other idea how to improve internal linking

Example response:
{
  "suggestions": [{'action': 'Add internal link', 'reason': "The term 'breach of contract' is mentioned as an example of a cause of action, and a corresponding page on 'breach' exists in the sitemap.", 'from': 'if someone broke a contract with you, your cause of action would be breach of contract.', 'to': 'if someone broke a contract with you, your cause of action would be <a href="https://detangle.ai/legal-terms/breach">breach of contract</a>.'}]
}
"""
@backoff.on_exception(backoff.expo, RateLimitError)
async def suggest_interlink_for_page(page, path):
    with open(f'{path}/{page}', 'r') as file:
        pagecontent = file.read()
    with open(f'{path}/metadata.json', 'r') as file:
        sitemap = file.read()

    content = f"""Here is page content and sitemap. Suggest what links I can add.
    page content:
    {pagecontent}
    sitemap:
    {sitemap}
    """
    # print(f"debug model: {content}")
    response = await client.chat.completions.create(
      model=MODEL,
      response_format={ "type": "json_object" },
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
      ]
    )
    json_response = response.choices[0].message.content
    dict_response = json.loads(json_response)
    return {
        "suggestions": dict_response['suggestions'],
        "usage": response.usage.model_dump()
    }
    # dict_response = json.loads(json_response)
    # return dict_response['suggestions']

async def suggest_and_prepare_report(page, path, hostname):
    try:
        async with limiter:
            suggestions = await suggest_interlink_for_page(page, path)
            # print(suggestions)
#             list_of_suggestion = [f"### {suggestion['action']}\n{suggestion['reason']}\nDiff:\n```diff\n-{suggestion['from']}\n+{suggestion['to']}\n```\n" for suggestion in suggestions]

#             text = f"""
# ## Page {page}
# List of suggestions:
#         """ + '\n\n'.join(list_of_suggestion)
#             with open(f"out/{hostname}.md", 'a') as report_file:
#                 report_file.write(text + '\n')
#             return text
        return (page, suggestions)
    except Exception as e:
        print(f"Error: {e}")
        print(suggestions)


async def command_suggest(args):
    print("suggesting")
    # if args.page:
    #   print(f"Suggesting interlinking for {args.page}")

    # text = await suggest_and_prepare_report(args.page, '', '')
    # data_folder = "out"
    # if not os.path.exists(data_folder):
    #     os.makedirs(data_folder)
    # with open(f"out/{args.page}.md", 'w') as file:
    #     file.write(text)
    # print(text)


async def command_suggest_all(args):
    print("suggesting-all")
    hostname = urlparse(args.url).hostname
    sitemap_folder = os.path.join(DATA_FOLDER, hostname)
    tasks = []

    # Open and parse the metadata JSON file
    with open(os.path.join(sitemap_folder, 'metadata.json'), 'r') as file:
        metadata = json.load(file)

    files_to_process = [f for f in os.listdir(sitemap_folder) if not f.endswith(('.xml', '.json'))]
    if args.filter:
        pattern = re.compile(args.filter)
        files_to_process = [f for f in files_to_process if pattern.search(f)]
    if args.limit != -1:
        files_to_process = files_to_process[:args.limit]
    for file in files_to_process:
        task = suggest_and_prepare_report(file, sitemap_folder, metadata)
        tasks.append(task)
    for future in async_tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        (url, suggestion) = await future
        metadata['suggestions'][url] = suggestion

    # write metadata.json with pretty print
    with open(os.path.join(sitemap_folder, 'metadata.json'), 'w') as file:
        json.dump(metadata, file, indent=4)

async def command_generate(args):
    print("generate")
    hostname = urlparse(args.url).hostname
    sitemap_folder = os.path.join(DATA_FOLDER, hostname)
    tasks = []

    # Open and parse the metadata JSON file
    with open(os.path.join(sitemap_folder, 'metadata.json'), 'r') as file:
        metadata = json.load(file)

    # Prepare data for CSV
    csv_data = []
    for page, data in metadata["suggestions"].items():
        suggestions = [suggestion for suggestion in data['suggestions'] if 'to_url' not in suggestion or (page not in suggestion['to_url'] and page != '')]
        for suggestion in suggestions:
            csv_row = {
                'Page': page,
                'Action': suggestion['action'],
                'Reason': suggestion['reason'],
                'From': suggestion['from'],
                'To': suggestion['to']
            }
            csv_data.append(csv_row)

    # Write data to CSV
    with open(f"out/{hostname}.csv", 'w', newline='') as csvfile:
        fieldnames = ['Page', 'Action', 'Reason', 'From', 'To']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
def init_parser():
    parser = argparse.ArgumentParser(description='Download a sitemap and scrape pages.')
    subparsers = parser.add_subparsers(dest='command')

    download_parser = subparsers.add_parser('download', help='Download a sitemap.')
    download_parser.add_argument('url', type=str, help='URL of the sitemap.xml file')

    suggest_parser = subparsers.add_parser('suggest', help='Suggest interlinking for a page.')
    suggest_parser.add_argument('page', type=str, help='URL of the page to suggest interlinking for')

    suggest_parser_all = subparsers.add_parser('suggest-all', help='Suggest interlinking for all pages.')
    suggest_parser_all.add_argument('url', type=str, help='hostname for website to process')
    suggest_parser_all.add_argument('--limit', type=int, default=-1, help='limit of pages to process')
    suggest_parser_all.add_argument('--filter', type=str, default=None, help='optional filter for pages to process')

    generate_parser = subparsers.add_parser('generate', help='Generate json to markdown')
    generate_parser.add_argument('url', type=str, help='hostname for website to process')
    return parser


async def main():
    parser = init_parser()
    args = parser.parse_args()
    if args.command == 'download':
        command_download(args)
    elif args.command == 'suggest':
        command_suggest(args)
    elif args.command == 'suggest-all':
        await command_suggest_all(args)
    elif args.command == 'generate':
        await command_generate(args)

if __name__ == "__main__":
    asyncio.run(main())
