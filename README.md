# LlamaIndex Tools Integration: SiftQ

This tool connects to [SiftQ](https://siftq.com), a web search API that
provides precise, fresh, structured web context for AI agents across
webpages, documents, scholarly articles, images, videos, and podcasts.

A free tier is available — no API key required. You can also set the
`SIFTQ_API_KEY` environment variable or pass an `api_key` explicitly.
Get an API key at [siftq.com](https://siftq.com).

## Installation

```bash
pip install llama-index-tools-siftq
```

## Usage

### Free Tier (no API key)

```python
from llama_index.tools.siftq import SiftQToolSpec

tool = SiftQToolSpec()
results = tool.search("latest AI research papers")
```

### With API Key

```python
import asyncio
import os

from llama_index.core.agent import FunctionAgent
from llama_index.llms.openai import OpenAI

from llama_index.tools.siftq import SiftQToolSpec

siftq_tool = SiftQToolSpec(
    api_key=os.environ["SIFTQ_API_KEY"],
)
agent = FunctionAgent(
    tools=siftq_tool.to_tool_list(),
    llm=OpenAI(model="gpt-4.1"),
)

async def main():
    response = await agent.run(
        "What are the latest developments in AI?"
    )
    print(response)


asyncio.run(main())
```

### Basic Search

```python
from llama_index.tools.siftq import SiftQToolSpec

tool = SiftQToolSpec(api_key=os.environ["SIFTQ_API_KEY"])

results = tool.search("latest AI research papers", size=5)
for r in results:
    print(r["title"], r.get("link"))
```

### Search by Scope

```python
# Search scholarly articles
results = tool.search("transformer architecture", scope="scholar", size=10)
for r in results:
    print(r["title"], r["authors"], r.get("citationCount"))

# Search images
results = tool.search("machine learning diagram", scope="image")
for r in results:
    print(r["title"], r.get("imageUrl"))

# Search videos
results = tool.search("Python tutorial", scope="video")
for r in results:
    print(r["title"], r.get("link"), r.get("duration"))

# Search podcasts
results = tool.search("data science", scope="podcast")
for r in results:
    print(r["title"], r.get("podcastName"), r.get("audioUrl"))

# Search documents
results = tool.search("quarterly report", scope="document")
for r in results:
    print(r["title"], r.get("source"))
```

## Available Tools

- `search`: Search using SiftQ for a list of results matching a natural
  language query, across multiple scopes (webpage, document, scholar, image,
  video, podcast).

- `current_date`: Utility for the agent to get today's date (useful for
  time-filtered searches).

## Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|---|
| `api_key` | `str` | `None` (uses free tier) | SiftQ API key, or `SIFTQ_API_KEY` env var, or free tier default |
| `verbose` | `bool` | `True` | Print search metadata |
| `max_results` | `int` | `5` | Default number of results |
| `timeout` | `float` | `None` | Request timeout in seconds |

### Per-query Parameters

| Parameter | Type | Description |
|---|---|---|
| `query` | `str` | Natural language search query |
| `scope` | `str` | Search scope: `webpage`, `document`, `scholar`, `image`, `video`, or `podcast` |
| `size` | `int` | Number of results (overrides default, max 100) |
| `include_summary` | `bool` | Enhance recall using page summaries |
| `include_raw_content` | `bool` | Fetch raw content from source pages |
| `concise_snippet` | `bool` | Return concise snippet with exact original text match |
