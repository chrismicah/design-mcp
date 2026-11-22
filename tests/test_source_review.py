from datetime import date
from urllib.error import HTTPError

from scripts.watch_design_sources import CROSSREF_INTERVAL_SECONDS, collect, print_report


def test_source_review_survives_rate_limiting_and_escapes_source_text(capsys):
    def fetch(url):
        if "USWDS" in url:
            raise HTTPError(url, 429, "limited", {}, None)
        if "github.com" in url:
            return {"html_url": "https://github.com/remorses/playwriter/releases/tag/v1",
                    "tag_name": "<script> & test", "published_at": "2026-11-19T10:00:00Z"}
        if "visual+critique" in url:
            return {"results": []}
        assert "from_publication_date%3A2026-08-23" in url
        return {"results": [
            {"id": "javascript:void(0)", "title": "Invalid", "publication_date": "2026-11-19"},
            {"id": "https://openalex.org/W123", "title": "UI repair", "publication_date": "2026-11-19"},
        ]}

    print_report(collect(date(2026, 11, 21), fetch))
    report = capsys.readouterr().out
    assert "HTTP 429" in report
    assert "&lt;script&gt; &amp; test" in report and "<script>" not in report
    assert "https://openalex.org/W123" in report and "javascript:" not in report
    assert "No results in the current search." in report


def test_source_review_exposes_a_complete_outage():
    def unavailable(url):
        raise TimeoutError

    sources = collect(date(2026, 11, 21), unavailable, lambda _: None)
    assert len(sources) == 4
    assert all(source["error"] == "TimeoutError" for source in sources)


def test_paper_search_falls_back_once_per_query_and_keeps_verified_doi_links(capsys):
    requests = []
    waits = []
    paper = {
        "DOI": "10.1234/UI.42",
        "title": ["Screenshot <analysis> & code"],
        "published": {"date-parts": [[2026, 10]]},
        "type": "proceedings-article",
    }

    def fetch(url):
        requests.append(url)
        if "api.github.com" in url:
            raise TimeoutError
        if "api.openalex.org" in url:
            raise HTTPError(url, 429, "limited", {}, None)
        assert "api.crossref.org/works" in url
        assert "from-pub-date%3A2026-08-23" in url
        return {"message": {"items": [
            None,
            {**paper, "DOI": None},
            {**paper, "DOI": "javascript:void(0)"},
            {**paper, "DOI": "10.1234/old", "published": {"date-parts": [[2026, 7, 30]]}},
            {**paper, "DOI": "10.1234/bad-date", "published": {"date-parts": [[2026, 13]]}},
            {**paper, "DOI": "10.1234/review", "type": "peer-review"},
            paper,
            {**paper, "DOI": "10.1234/ui.42"},
        ]}}

    sources = collect(date(2026, 11, 21), fetch, waits.append)
    assert sum("api.openalex.org" in url for url in requests) == 1
    assert sum("api.crossref.org" in url for url in requests) == 2
    assert waits == [CROSSREF_INTERVAL_SECONDS]
    for source in sources[-2:]:
        assert source["provider"] == "Crossref"
        assert source["openalex_error"] == "HTTP 429"
        assert source["leads"] == [{
            "title": "Screenshot <analysis> & code", "date": "2026-10", "url": "https://doi.org/10.1234/ui.42",
        }]
    print_report(sources)
    report = capsys.readouterr().out
    assert "&lt;analysis&gt; &amp; code" in report and "javascript:" not in report
