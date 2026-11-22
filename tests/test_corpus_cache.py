"""Exercise corpus acquisition with tiny, offline snapshots."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
import hashlib
import json
from threading import Event

import httpx
import pytest

from design_mcp import corpus, resources
from design_mcp.database import DesignDatabase


@pytest.fixture
def snapshot(tmp_path, monkeypatch, curated_pattern_data):
    low = dict(curated_pattern_data, id="low", quality_score=1)
    high = dict(curated_pattern_data, id="high", quality_score=9)
    payload = json.dumps([low, high]).encode()
    bundled = tmp_path / "package" / "data" / "patterns.json"
    bundled.parent.mkdir(parents=True)
    cached = tmp_path / "cache" / "patterns-test.json"
    monkeypatch.setattr(resources, "files", lambda package: bundled.parent.parent)
    monkeypatch.setattr(corpus, "SIZE", len(payload))
    monkeypatch.setattr(corpus, "SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(corpus, "cache_path", lambda: cached)
    monkeypatch.setattr(httpx, "stream", lambda *a, **kw: pytest.fail("Unexpected corpus request"))
    return payload, bundled, cached


def serve(monkeypatch, body, *, status=200, headers=None):
    @contextmanager
    def stream(method, url, **kwargs):
        assert method == "GET" and url == corpus.URL
        assert kwargs["follow_redirects"] is False and kwargs["timeout"] > 0
        with closing(httpx.Response(status, request=httpx.Request(method, url), headers=headers,
                                    stream=httpx.ByteStream(body))) as response:
            yield response
    monkeypatch.setattr(httpx, "stream", stream)


def test_source_and_old_install_keep_their_path_and_ranking(snapshot, monkeypatch):
    payload, bundled, cached = snapshot
    bundled.write_bytes(payload)
    original = DesignDatabase(bundled)
    lazy = DesignDatabase()
    assert lazy.path == original.path == bundled
    calls = []
    read = corpus.read_corpus

    def counted_read():
        calls.append(True)
        return read()

    monkeypatch.setattr(corpus, "read_corpus", counted_read)
    assert lazy.count() == 2
    assert [p.model_dump() for p in lazy.search(query="dashboard")] == [
        p.model_dump() for p in original.search(query="dashboard")
    ]
    assert [p.id for p in lazy.search()] == ["high", "low"]
    assert lazy.get("high") == original.get("high")
    assert len(calls) == 1 and not cached.exists()


def test_lazy_fetch_then_reopen_offline(snapshot, monkeypatch):
    payload, _, cached = snapshot
    db = DesignDatabase()
    assert not cached.parent.exists()
    with monkeypatch.context() as patch:
        serve(patch, payload)
        assert db.count() == 2
    assert cached.read_bytes() == payload
    assert [p.id for p in DesignDatabase().search(query="dashboard")] == ["high", "low"]
    with pytest.raises(ValueError, match="read-only"):
        db.save()


@pytest.mark.parametrize(("response", "message"), [
    ("html", "SHA-256"), ("short", "wrong size"), ("long", "exceeds"),
    ("length", "Content-Length"), ("redirect", "302"), ("offline", "unavailable"),
])
def test_failed_fetch_never_publishes(snapshot, monkeypatch, response, message):
    payload, _, cached = snapshot
    if response == "offline":
        def offline(*args, **kwargs):
            raise httpx.ConnectError("unavailable")
        monkeypatch.setattr(httpx, "stream", offline)
    else:
        body = {"html": b"x" * len(payload), "short": payload[:-1], "long": payload + b"! "}.get(response, payload)
        headers = {"Content-Length": str(len(payload) + 1)} if response == "length" else {}
        if response == "redirect":
            headers["Location"] = "https://example.invalid/latest"
        serve(monkeypatch, body, status=302 if response == "redirect" else 200, headers=headers)
    with pytest.raises(corpus.CorpusError, match=message) as error:
        corpus.read_corpus()
    assert "doctor --repair" in str(error.value)
    assert not cached.exists()


def test_corruption_needs_explicit_repair(snapshot, monkeypatch):
    payload, bundled, cached = snapshot
    cached.parent.mkdir()
    damaged = b"x" * len(payload)
    cached.write_bytes(damaged)
    sibling = cached.with_name("other-version.json")
    sibling.write_bytes(b"leave this alone")
    with pytest.raises(corpus.IntegrityError, match="doctor --repair"):
        corpus.read_corpus()
    serve(monkeypatch, payload[:-1])
    with pytest.raises(corpus.CorpusError):
        corpus.ensure_cache(repair=True)
    assert cached.read_bytes() == damaged
    bundled.write_bytes(payload)
    assert corpus.ensure_cache(repair=True) == payload
    assert bundled.read_bytes() == cached.read_bytes() == payload
    assert sibling.read_bytes() == b"leave this alone"
    bundled.write_bytes(damaged)
    with pytest.raises(corpus.IntegrityError, match="Restore the bundled file"):
        corpus.read_corpus()


def test_readers_see_only_complete_snapshots_during_repair(snapshot, monkeypatch):
    payload, bundled, cached = snapshot
    bundled.write_bytes(payload)
    cached.parent.mkdir()
    cached.write_bytes(b"old")
    publish, resume = Event(), Event()
    replace = corpus.os.replace

    def pause_before_replace(staged, target):
        assert staged.parent == target.parent and staged.read_bytes() == payload
        publish.set()
        assert resume.wait(5)
        replace(staged, target)

    monkeypatch.setattr(corpus.os, "replace", pause_before_replace)
    with ThreadPoolExecutor(max_workers=1) as worker:
        repair = worker.submit(corpus.ensure_cache, repair=True)
        try:
            assert publish.wait(5)
            with cached.open("rb") as old_reader:
                with pytest.raises(corpus.IntegrityError):
                    corpus.read_cached()
                resume.set()
                assert repair.result(timeout=5) == payload
                assert old_reader.read() == b"old"
        finally:
            resume.set()
    assert corpus.read_cached() == payload
    assert list(cached.parent.iterdir()) == [cached]


def test_interrupted_publication_leaves_the_existing_file(snapshot, monkeypatch):
    payload, bundled, cached = snapshot
    bundled.write_bytes(payload)
    cached.parent.mkdir()
    cached.write_bytes(b"old")

    def interrupted(staged, target):
        raise OSError("interrupted")

    monkeypatch.setattr(corpus.os, "replace", interrupted)
    with pytest.raises(corpus.CorpusError, match="interrupted"):
        corpus.ensure_cache(repair=True)
    assert cached.read_bytes() == b"old" and list(cached.parent.iterdir()) == [cached]


def test_repair_refuses_a_link_to_an_unrelated_file(snapshot):
    payload, bundled, cached = snapshot
    bundled.write_bytes(payload)
    unrelated = bundled.with_name("unrelated")
    unrelated.write_bytes(b"preserve")
    cached.parent.mkdir()
    cached.symlink_to(unrelated)
    with pytest.raises(corpus.CorpusError, match="symlink"):
        corpus.ensure_cache(repair=True)
    assert cached.is_symlink() and unrelated.read_bytes() == b"preserve"
