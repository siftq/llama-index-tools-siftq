"""SiftQ tool spec - web search API for AI agents.

SiftQ provides structured search across webpages, documents, scholarly
articles, images, videos, and podcasts. Obtain an API key at
https://siftq.com (a free tier is available without an API key).
"""

import datetime
import os
from typing import Any, cast

from llama_index.core.tools.tool_spec.base import BaseToolSpec


class SiftQToolSpec(BaseToolSpec):
    """SiftQ tool spec - precise, fresh, structured web context for AI.

    Get an API key at https://siftq.com
    """

    DEFAULT_API_KEY = "mk-1D3D81EFC32A25683B0C2C3B315F8579"

    spec_functions = [  # type: ignore[reportIncompatibleVariableOverride]
        "search",
        "current_date",
    ]

    _api_key: str
    _verbose: bool
    _max_results: int
    _timeout: float | None
    last_credits: int
    last_total: int

    SCOPE_KEY_MAP: dict[str, str] = {
        "webpage": "webpages",
        "document": "documents",
        "scholar": "scholars",
        "image": "images",
        "video": "videos",
        "podcast": "podcasts",
    }

    def __init__(
        self,
        api_key: str | None = None,
        verbose: bool = True,
        max_results: int = 5,
        timeout: float | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("SIFTQ_API_KEY") or self.DEFAULT_API_KEY
        self._verbose = verbose
        self._max_results = max_results
        self._timeout = timeout
        self.last_credits = 0
        self.last_total = 0

    def _call_api(
        self,
        query: str,
        scope: str = "webpage",
        size: int | None = None,
        include_summary: bool = False,
        include_raw_content: bool = False,
        concise_snippet: bool = False,
    ) -> dict[str, Any]:
        import httpx

        payload: dict[str, Any] = {
            "q": query,
            "scope": scope,
            "size": size if size is not None else self._max_results,
            "includeSummary": include_summary,
            "includeRawContent": include_raw_content,
            "conciseSnippet": concise_snippet,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        kwargs: dict[str, Any] = {}
        if self._timeout is not None:
            kwargs["timeout"] = self._timeout

        response = httpx.post(
            "https://api.siftq.com/v1/search",
            json=payload,
            headers=headers,
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()
        code = data.get("code", 0)
        if code == 3003:
            raise RuntimeError(
                "search failed: daily search limit reached. See: https://siftq.com/playground"
            )
        if code == 2005:
            raise RuntimeError("search failed: API key rejected. Check your SiftQ API key.")
        if code:
            raise RuntimeError(f"search failed: code={code}, message={data.get('message', '')}")
        return data

    def _extract_results(self, data: dict[str, Any], scope: str) -> list[dict[str, Any]]:
        results_key = self.SCOPE_KEY_MAP[scope]
        self.last_credits = int(data.get("credits", 0))
        self.last_total = int(data.get("total", 0))
        items = cast(list[dict[str, Any]], data.get(results_key, []))
        for item in items:
            if "link" not in item and "imageUrl" in item:
                item["link"] = item["imageUrl"]
        return items

    def search(
        self,
        query: str,
        scope: str = "webpage",
        size: int | None = None,
        include_summary: bool = False,
        include_raw_content: bool = False,
        concise_snippet: bool = False,
    ) -> list[dict[str, Any]]:
        """Search the web using SiftQ.

        Args:
            query: A natural language search query.
            scope: Search scope - "webpage", "document", "scholar", "image",
                   "video", or "podcast".
            size: Number of results to return (1-100). Defaults to max_results.
            include_summary: Enhance recall using page summaries.
            include_raw_content: Fetch raw content from source pages.
            concise_snippet: Return concise snippet with exact original text match.
        """
        if scope not in self.SCOPE_KEY_MAP:
            raise ValueError(
                f"Invalid scope '{scope}'. Must be one of: {', '.join(self.SCOPE_KEY_MAP)}"
            )
        data = self._call_api(
            query=query,
            scope=scope,
            size=size,
            include_summary=include_summary,
            include_raw_content=include_raw_content,
            concise_snippet=concise_snippet,
        )
        results = self._extract_results(data, scope)
        if self._verbose:
            print(
                f"[SiftQ Tool] Found {len(results)} results (total: {self.last_total},"
                f" credits: {self.last_credits}) for: {query}"
            )
        return results

    def current_date(self) -> str:
        """Return today's date.

        Call this before other functions that take date arguments.
        """
        return str(datetime.date.today())
