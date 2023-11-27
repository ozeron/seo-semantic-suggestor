import sys
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import html2text
from collections import Counter

def extract_content_from_file(file_path):
    with open(file_path, 'r') as file:
        html = file.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Remove all script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    # Get meta tags
    meta_tags = soup.findAll('meta')

    # Get title
    title = soup.title.string if soup.title else ""

    # Get text content and links
    text_content = []
    for paragraph in soup.find_all(['p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text_content.append(str(paragraph))

    return meta_tags, title, text_content


def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove all script and style elements
    for script in soup(["script", "style"]):
        script.extract()

    return str(soup)

def convert_html_to_markdown(html):
    h = html2text.HTML2Text()
    # Don't Ignore converting links from HTML
    h.ignore_links = True
    return h.handle(html)


def clean_markdown(str):
    cleaned_text = re.sub('\n{3,}', '\n\n', str)
    chunks = cleaned_text.split('\n\n')  # Split the text into chunks at each double newline
    counter = Counter(chunks)  # Count the occurrences of each chunk
    unique_chunks = [chunk for chunk, count in counter.items() if count == 1]  # Keep only unique chunks
    return '\n\n'.join(unique_chunks)  # Join the unique chunks back together with double newlines

def clean_html_to_md(html):
    cleaned_html = clean_html(html)
    markdown = md(cleaned_html)
    cleaned_md = clean_markdown(markdown)
    return cleaned_md

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, 'r') as file:
        html = file.read()

    cleaned_md = clean_html_to_md(html)
    return cleaned_md

if __name__ == "__main__":
    md = main()
    print(md)
