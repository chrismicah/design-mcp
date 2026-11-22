from datetime import date
from urllib.error import HTTPError

from scripts.watch_design_sources import collect, print_report


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

    sources = collect(date(2026, 11, 21), unavailable)
    assert len(sources) == 4
    assert all(source["error"] == "TimeoutError" for source in sources)
