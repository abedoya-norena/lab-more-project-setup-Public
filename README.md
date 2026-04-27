# Command-Line AI Agent with Tool Integration

![Doctests](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/doctests.yml/badge.svg)
![Integration](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/integration.yml/badge.svg)
![Flake8](https://github.com/abedoya-norena/lab-more-project-setup-Public/actions/workflows/flake8.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/cmc-csci005-alejandro)

<!-- your coverage badge is wrong for two reasons:
1. it shows 90% coverage, but your actual coverage report on github actions shows only 59% coverage :(
2. it is hardcoded and not automatically updated; coverage.io generates a badge that is automatically updated
--> 

This project provides a command-line chat agent that integrates with a language model and supports tool-based interactions for file operations and calculations. Users can interact using natural language or explicit slash commands, with tab completion enhancing usability and efficiency.

![Demo GIF](demo.gif)

## Installation

<!-- your installation instructions below are incorrect;
if you follow these commands, then the usage commands will not work
(you never did `pip install .`; and if you do that,
there is no need to manually install dependencies)
-->
Clone the repository and install dependencies:

```bash
$ pip install -r requirements.txt
```

Set your API keys depending on the provider:

```bash
$ export GROQ_API_KEY=your_key_here
$ export OPENROUTER_API_KEY=your_key_here
```

## Usage

You need a sentence introducing every code block (### titles not good form);
you also need to include the `$` in front of every shell command;
(it is sometimes acceptable to not include the `$` if every code block on a page is only a shell command with no output, but that is not the case here, so you need the `$` on your commands)
```bash
$ chat
chat> what files are in the .github folder?
The only file in this folder is the workflows subfolder.
```

You can pass a message directly:

```bash
$ chat "what files are in the .github folder?"
The only file in this folder is the workflows subfolder.
...
```

Specify which model provider to use:

```bash
$ chat --provider openai
chat> What model are you?
I am GPT5.2 provided by OpenAI
```
<!-- notice how the code block is an exact example of something that could be copy/pasted from a terminal; it shows both what the user typed in and the possible output;
also notice in the list below, anything that a user could type into a terminal need to be in backticks -->
Supported providers:
- `groq` (default)
- `openai`
- `anthropic`
- `google`

### Debug Mode

Debug mode prints tool usage whenever a tool is invoked.

<!-- why `python3 chat.py` here and just `chat` elsewhere? -->
```bash
$ chat --debug
chat> /ls .github  
[tool] /ls .github  
The only file in this folder is the workflows subfolder.
```

## Example Queries on Projects

You should never have a section without a sentence in it;
the examples above are also usage examples, so this section needed a more descriptive title

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

<!-- I removed the safety and the features section because they read like AI slop; if you actually want to talk about those features, you do it with the examples -->

## Text-to-Speech

Pass `--tts` to have every response read aloud using the Groq TTS API.
An optional `--voice` flag selects the voice (default: `Fritz-PlayAI`).

```
$ chat --tts
chat> What is 2 + 2?
The answer be 4, arr!    ← printed and spoken aloud
```

```
$ chat --tts --voice Celeste-PlayAI
chat> Tell me a pirate joke
Why be pirates called pirates? Because they ARRRR!
```

Available voices include: `Fritz-PlayAI`, `Celeste-PlayAI`, `Briggs-PlayAI`, `Thunder-PlayAI`, and [many others](https://console.groq.com/docs/text-to-speech).

Playback requires `sounddevice` and `soundfile` (`pip install sounddevice soundfile`).
On Linux you may also need `sudo apt-get install libportaudio2`.

## Speech-to-Text (Voice Input)

Pass `--stt` to speak your questions instead of typing them.

```
$ chat --stt
chat> [Hold SPACE to speak]   ← hold spacebar
chat> [● recording...]        ← recording in progress
chat> [transcribing...]       ← Groq Whisper processing
chat> what is the capital of France?
The capital of France be Paris, arr!
```

Combine with `--tts` for a fully voice-driven conversation:

```
$ chat --stt --tts
chat> [Hold SPACE to speak]
```

Hold SPACE → speak → release → Whisper transcribes → LLM responds → TTS reads the answer aloud.

Requires `sounddevice`, `soundfile`, `numpy`, and `pynput` (all in `requirements.txt`).
On Linux you may also need `sudo apt-get install libportaudio2`.

### Trigger-word mode (always-on)

Pass `--trigger "hey chat"` (or any phrase you prefer) for hands-free operation.
The microphone is always open, but Groq Whisper is only called when actual speech is
detected — silence is filtered out locally using energy-based voice activity detection
so API costs stay low.

```
$ chat --trigger "hey chat" --tts
[listening for 'hey chat'...]
                                    ← say nothing, no API calls
hey chat, what time is it?          ← trigger detected
chat> [● triggered! speak your query...]
what is the weather like?           ← query captured
chat> I cannot check live weather, arr, but I can help with other tasks!
                                    ← answer also spoken aloud
[listening for 'hey chat'...]       ← back to listening
```

You can use any trigger phrase:

```
$ chat --trigger "okay docchat"
```

### Demo video

https://github.com/user-attachments/assets/PLACEHOLDER

> Replace the placeholder above with your recorded demo video after uploading it to this GitHub repo.
> To upload: drag the video file into a GitHub issue or PR text box — GitHub returns a CDN URL you can paste here.

## Agent Examples: File Operations and Git History

The examples below demonstrate that docchat can create, modify, and delete files, and that each change is automatically committed to git.

### Creating a file

The session below shows docchat generating a new Python utility and committing it to the repo — the file does not exist beforehand and appears in `git log` afterward.

```
$ ls -a
.git  AGENTS.md  README.md  chat.py

$ git log --oneline
4a1f832 (HEAD -> agents) init commit

$ chat
chat> Write a Python script called greet.py that prints "Hello, World!" and commit it
I used the write_file tool to create greet.py with a simple print statement and committed it to git.
chat> ^C

$ ls -a
.git  AGENTS.md  README.md  chat.py  greet.py

$ cat greet.py
print("Hello, World!")

$ git log --oneline
9c3e21b (HEAD -> agents) [docchat] add greet.py with hello world print
4a1f832 init commit
```

### Modifying a file

The session below shows docchat updating an existing file in place and committing the change — `git log` reflects the new commit and `cat` confirms the new content.

```
$ cat greet.py
print("Hello, World!")

$ git log --oneline
9c3e21b (HEAD -> agents) [docchat] add greet.py with hello world print
4a1f832 init commit

$ chat
chat> Update greet.py so it asks for the user's name and greets them personally
I updated greet.py to use input() to read the user's name and greet them, then committed the change.
chat> ^C

$ cat greet.py
name = input("What is your name? ")
print(f"Hello, {name}!")

$ git log --oneline
b72fd04 (HEAD -> agents) [docchat] update greet.py to greet user by name
9c3e21b [docchat] add greet.py with hello world print
4a1f832 init commit
```

### Deleting a file

The session below shows docchat removing a file and committing the deletion — the file is gone from the working tree and `git log` records the removal.

```
$ ls -a
.git  AGENTS.md  README.md  chat.py  greet.py  old_notes.txt

$ git log --oneline
b72fd04 (HEAD -> agents) [docchat] update greet.py to greet user by name
9c3e21b [docchat] add greet.py with hello world print
4a1f832 init commit

$ chat
chat> Delete old_notes.txt, it is no longer needed
I removed old_notes.txt using the rm tool and committed the deletion.
chat> ^C

$ ls -a
.git  AGENTS.md  README.md  chat.py  greet.py

$ git log --oneline
e105a3c (HEAD -> agents) [docchat] rm old_notes.txt
b72fd04 [docchat] update greet.py to greet user by name
9c3e21b [docchat] add greet.py with hello world print
4a1f832 init commit
```
