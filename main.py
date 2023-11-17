import os
import requests
import xml.etree.ElementTree as ET
import argparse
import os
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
You are helpful SEO assistant.
Rules to suggest internal linking:
When deciding on adding internal links to blog pages, consider these points:

Relevance: Link to content that's contextually related. This improves user experience and can boost the linked page's relevance for specific keywords.

Anchor Text: Use descriptive, keyword-rich anchor text, but avoid over-optimization. Keep it natural and varied.

Link Distribution: Spread links throughout your site to avoid concentrating them in a few pages. This helps distribute PageRank more evenly.

User Journey: Think about the user's path through your site. Link to content that logically follows or provides deeper insights into the topic.

Page Authority: Link from high-authority pages to pages that need a boost. This can help increase their visibility in search engines.

Content Freshness: Update old posts with links to newer, relevant content to keep them fresh and relevant.

Avoid Overlinking: Too many links on a page can be distracting and may dilute PageRank. Focus on adding a few high-quality links.

SEO Goals: Align internal linking with your SEO strategy, whether it's boosting specific pages, enhancing content hubs, or improving site architecture.

Analytics: Use tools like Google Analytics to identify high-traffic pages that can pass valuable link equity to other pages.

Broken Links: Regularly check for and fix broken internal links. They can harm user experience and SEO.

Remember, internal linking is as much about enhancing user experience as it is about SEO. Keep it intuitive and helpful.
"""

def command_suggest(args):
    if args.page:
      print(f"Suggesting interlinking for {args.page}")


    with open(f'data/{args.page}', 'r') as file:
        pagecontent = file.read()
    with open('sitemap.xml', 'r') as file:
        sitemap = file.read()

    content = f"""Here is page content and sitemap. Suggest what links I can add.
    page content:
    {pagecontent}
    sitemap:
    {sitemap}
    """

    response = client.chat.completions.create(
      model=MODEL,
      #response_format={ "type": "json_object" },
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content}
      ]
    )
    print(response.choices[0].message.content)


def main(args):
    if args.command == 'download':
        command_download(args)
    elif args.command == 'suggest':
        command_suggest(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download a sitemap and scrape pages.')
    subparsers = parser.add_subparsers(dest='command')

    download_parser = subparsers.add_parser('download', help='Download a sitemap.')
    download_parser.add_argument('url', type=str, help='URL of the sitemap.xml file')

    suggest_parser = subparsers.add_parser('suggest', help='Suggest interlinking for a page.')
    suggest_parser.add_argument('page', type=str, help='URL of the page to suggest interlinking for')

    args = parser.parse_args()
    main(args)
