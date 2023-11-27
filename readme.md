# README

## Setup

This script requires Python 3.6 or later.

First, clone the repository and navigate to the project directory.

This project uses [Poetry](https://python-poetry.org/) for dependency management. If you haven't installed Poetry yet, you can do so by following the instructions on their [official documentation](https://python-poetry.org/docs/#installation).

Once Poetry is installed, you can install the project dependencies with: `poetry install`

This script uses the OpenAI API, so you'll need to set up an API key. You can do this by creating a `.env` file in the project directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key
```

Replace `your_openai_api_key` with your actual OpenAI API key.

## Usage

This script provides several commands:

- `download`: Downloads a sitemap from a given URL and saves the pages it links to.
- `suggest-all`: Suggests interlinking for all pages.
- `generate`: Generates a CSV report from the suggestions.

To run the script with Poetry, use the `poetry run` command:

To run it for website you need run commands in following order, to first download, then generate suggestions and then generate csv.

### Download

To download a sitemap, use the `download` command followed by the URL of the sitemap:
`poetry run python main.py download https://example.com`

This will download the sitemap and save the pages it links to in the `data` directory.

### Suggest All

To suggest interlinking for all pages, use the `suggest-all` command followed by the URL of the website:
`poetry run python main.py suggest-all https://example.com`

This command also accepts optional arguments:

- `--limit`: Limits the number of pages to process. If not specified, all pages will be processed. For example, to process only the first 10 pages, use: `poetry run python main.py suggest-all https://example.com --limit 10`
- `--filter`: Filters the pages to process based on a regular expression. Only pages whose names match the regular expression will be processed. For example, to process only pages whose names contain "blog", use: `poetry run python main.py suggest-all https://example.com --filter blog`

This will output the suggestions for each page to the console and save them in a JSON file in the `data` directory.

### Generate

To generate a CSV report from the suggestions, use the `generate` command followed by the URL of the website:
`poetry run python main.py generate https://example.com`

This will generate a CSV file in the `out` directory.

TODO:

- [x] rewrite to store intermediate JSON progress and track costs
- [x] remove self links
- [x] support for nested xml sitemaps
- [x] add filtering
- [x] upload to CSV
- [ ] support html cleaning to save on tokens
- [ ] RAG for sitemap?
- [ ] remove dummy diffs
- [ ] remove links to external site
- [ ] optimize cost for big website, RAG??? or maybe page by page IDK
