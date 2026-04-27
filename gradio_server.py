#!/usr/bin/env python
'''
A bare-bones web interface for conversations with LLMs served from openai-compatible endpoints.
'''

import argparse
import gradio as gr
from openai import OpenAI
parser = argparse.ArgumentParser()
parser.add_argument("--url")
parser.add_argument("--apikey")
parser.add_argument("--model", default='llama-3.1-8b-instant')
parser.add_argument("--port", type=int, default=7860)
args = parser.parse_args()

client = OpenAI(base_url=args.url, api_key=args.apikey)

def chat(message, history):
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    completion = client.chat.completions.create(
        model=args.model,
        messages=messages
    )
    return completion.choices[0].message.content

gr.ChatInterface(chat).launch(server_port=args.port)
