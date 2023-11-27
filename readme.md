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
- `suggest`: Suggests interlinking for a specific page.
- `suggest-all`: Suggests interlinking for all pages.

To run the script with Poetry, use the `poetry run` command:

### Download

To download a sitemap, use the `download` command followed by the URL of the sitemap:
`poetry run python main.py download https://example.com/sitemap.xml`

This will download the sitemap and save the pages it links to in the `data` directory.

### Suggest

To suggest interlinking for a specific page, use the `suggest` command followed by the name of the page:
`poetry run python main.py suggest page`

This will output the suggestions to the console and save them in a Markdown file in the `out` directory.

### Suggest All

To suggest interlinking for all pages, use the `suggest-all` command:
`poetry run python main.py suggest-all`

This will output the suggestions for each page to the console and append them to a Markdown file in the `out` directory.

TODO:

- [ ] rewrite to store intermediate JSON progress and track costs
- [x] remove self links
- [ ] remove dummy diffs
- [ ] remove linkst to external site
- [x] support for nested xml sitemaps
- [ ] support html cleaning to save on tokens
- [ ] RAG for sitemap?
