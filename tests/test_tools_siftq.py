from unittest.mock import patch

import pytest
from llama_index.core.tools.tool_spec.base import BaseToolSpec

from llama_index.tools.siftq import SiftQToolSpec


def test_siftq_tool_spec_inherits_base():
    names_of_base_classes = [b.__name__ for b in SiftQToolSpec.__mro__]
    assert BaseToolSpec.__name__ in names_of_base_classes


def test_siftq_tool_spec_spec_functions():
    expected = [
        "search",
        "current_date",
    ]
    assert SiftQToolSpec.spec_functions == expected


def test_siftq_tool_spec_initialization():
    tool = SiftQToolSpec(api_key="test-key", verbose=False, max_results=10)
    assert tool._api_key == "test-key"
    assert not tool._verbose
    assert tool._max_results == 10
    assert tool.last_credits == 0
    assert tool.last_total == 0


def test_default_api_key():
    tool = SiftQToolSpec(verbose=False)
    assert tool._api_key == SiftQToolSpec.DEFAULT_API_KEY


def test_default_api_key_env_var(monkeypatch):
    monkeypatch.setenv("SIFTQ_API_KEY", "env-key")
    tool = SiftQToolSpec(verbose=False)
    assert tool._api_key == "env-key"


def test_explicit_api_key_overrides_env(monkeypatch):
    monkeypatch.setenv("SIFTQ_API_KEY", "env-key")
    tool = SiftQToolSpec(api_key="explicit-key", verbose=False)
    assert tool._api_key == "explicit-key"


def test_scope_key_map_covers_all_scopes():
    assert SiftQToolSpec.SCOPE_KEY_MAP == {
        "webpage": "webpages",
        "document": "documents",
        "scholar": "scholars",
        "image": "images",
        "video": "videos",
        "podcast": "podcasts",
    }


def test_extract_results_scope_key_lookup():
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    data = {"webpages": [{"title": "a"}], "documents": [{"title": "b"}], "total": 10, "credits": 2}
    result = tool._extract_results(data, "webpage")
    assert len(result) == 1
    assert result[0]["title"] == "a"
    assert tool.last_total == 10
    assert tool.last_credits == 2


def test_extract_results_returns_empty_list_for_empty_scope():
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    result = tool._extract_results({}, "webpage")
    assert result == []


def test_extract_results_normalizes_image_link():
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    data = {
        "images": [{"title": "img1", "imageUrl": "https://example.com/img.png"}],
        "total": 1,
        "credits": 1,
    }
    result = tool._extract_results(data, "image")
    assert result[0]["link"] == "https://example.com/img.png"


def test_extract_results_leaves_existing_link_untouched():
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    data = {"webpages": [{"title": "wp1", "link": "https://example.com"}], "total": 1, "credits": 1}
    result = tool._extract_results(data, "webpage")
    assert result[0]["link"] == "https://example.com"


@patch("httpx.post")
def test_search_uses_default_max_results(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False, max_results=7)
    mock_post.return_value.json.return_value = {"webpages": [], "total": 0, "credits": 0}
    tool.search("hello")
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["size"] == 7


@patch("httpx.post")
def test_search_passes_include_raw_content(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    mock_post.return_value.json.return_value = {"webpages": [], "total": 0, "credits": 0}
    tool.search("hello", include_raw_content=True)
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["includeRawContent"] is True


@patch("httpx.post")
def test_search_passes_size_override(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    mock_post.return_value.json.return_value = {"webpages": [], "total": 0, "credits": 0}
    tool.search("hello", size=3)
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["size"] == 3


@patch("httpx.post")
def test_search_passes_timeout(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False, timeout=15.0)
    mock_post.return_value.json.return_value = {"webpages": [], "total": 0, "credits": 0}
    tool.search("hello")
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["timeout"] == 15.0


@patch("httpx.post")
def test_search_sets_last_credits_and_total(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    mock_post.return_value.json.return_value = {"webpages": [], "total": 42, "credits": 5}
    tool.search("hello")
    assert tool.last_total == 42
    assert tool.last_credits == 5


@patch("httpx.post")
def test_error_code_2005_raises(mock_post):
    tool = SiftQToolSpec(api_key="bad-key", verbose=False)
    mock_post.return_value.json.return_value = {"code": 2005, "message": "invalid key"}

    with pytest.raises(RuntimeError, match="API key rejected"):
        tool.search("hello")


@patch("httpx.post")
def test_error_code_3003_raises(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    mock_post.return_value.json.return_value = {"code": 3003, "message": "limit reached"}

    with pytest.raises(RuntimeError, match="daily search limit reached"):
        tool.search("hello")


@patch("httpx.post")
def test_error_code_unknown_raises(mock_post):
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    mock_post.return_value.json.return_value = {"code": 9999, "message": "something else"}

    with pytest.raises(RuntimeError, match="code=9999"):
        tool.search("hello")


@patch("httpx.post")
def test_search_verbose_prints(mock_post, capsys):
    tool = SiftQToolSpec(api_key="test-key", verbose=True)
    mock_post.return_value.json.return_value = {
        "webpages": [{"title": "a"}],
        "total": 1,
        "credits": 2,
    }
    tool.search("hello world")
    captured = capsys.readouterr()
    assert "SiftQ Tool" in captured.out
    assert "hello world" in captured.out


def test_to_tool_list():
    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    tool_list = tool.to_tool_list()
    assert len(tool_list) == 2
    names = {t.metadata.name for t in tool_list}
    assert names == {"search", "current_date"}


def test_current_date():
    import datetime

    tool = SiftQToolSpec(api_key="test-key", verbose=False)
    date = tool.current_date()
    assert date == str(datetime.date.today())
