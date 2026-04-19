# Chat CLI with Tool Use

This project implements a command-line chat agent that interacts with a language model and supports tool use for working with files and performing calculations.

The system allows both natural language interaction and explicit slash commands for direct tool execution.


## Badges

![Doctests](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/doctests.yml/badge.svg)
![Integration](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/integration.yml/badge.svg)
![Flake8](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/flake8.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/cmc-csci005-alejandro)
![Coverage](https://img.shields.io/badge/coverage-%3E90%25-brightgreen)


## Demo

![Demo GIF](demo.gif)

## Features

- Chat with a language model in a REPL interface  
- Tool integration:
  - `/ls` list directory contents  
  - `/cat` display file contents  
  - `/grep` search within files  
  - `/calculate` evaluate expressions  
  - `/compact` summarize and compress chat history  
- Automatic tool calling by the model  
- Debug mode for visualizing tool usage  
- Support for multiple model providers  
- Command-line message execution  
- Tab completion for commands and file paths  

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

Set your API keys depending on the provider:

```bash
export GROQ_API_KEY=your_key_here
export OPENROUTER_API_KEY=your_key_here
```

## Usage

### Interactive Mode (REPL)

```bash
chat

chat> what files are in the .github folder?
The only file in this folder is the workflows subfolder.
```

### Command-Line Mode

You can pass a message directly:

```bash
chat "what files are in the .github folder?"
[tool] /ls .github
The only file in this folder is the workflows subfolder.
...
```

### Provider Selection

Specify which model provider to use:

```bash
chat --provider openai
chat --provider anthropic
chat --provider google
chat --provider groq
...
```
Supported providers:

- groq (default)
- openai
- anthropic
- google

## Usage Examples

### Markdown Compiler

This example demonstrates how the chat tool can analyze a codebase by searching for specific patterns across files.

```bash
cd test_projects/Markdown-to-HTML-compiler
chat
chat> does this project use regular expressions?
No. I grepped the project files and did not find any use of the `re` library.
```
This example is useful because it demonstrates how the agent uses the grep tool to analyze code structure across files.

### Ebay Scraper

This example demonstrates how the agent can summarize a project and answer higher-level questions about its purpose and implications.

```bash
cd test_projects/Ebay_webscrapping
chat
chat> tell me about this project
The project is designed to scrape product information from eBay listings.

chat> is this legal?
In general, scraping public webpages is often legal, although using an official API is usually more reliable and efficient.
```

This example is useful because it shows the agent can summarize a project and reason about broader implications.

### Personal Website

This example demonstrates how the tool can interpret and summarize the contents of a non-Python project.

```bash
cd test_projects/abedoya-norena.github.io
chat
chat> what does this project contain?
This project contains the files for a personal website, including HTML and related assets.

```
This example is useful because it demonstrates that the agent can interpret non-Python projects using file inspection.
