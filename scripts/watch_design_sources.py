"""Collect public design and browser source leads for review."""

from datetime import date, timedelta
from html import escape
import json
import re
from time import sleep
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


RELEASES = ("USWDS/uswds", "remorses/playwriter")
RESEARCH = ("screenshot to code UI generation", "visual critique user interface design")
MAX_BYTES = 256_000
CROSSREF_TYPES = {"journal-article", "proceedings-article", "posted-content"}
CROSSREF_INTERVAL_SECONDS = 1.25


def fetch_json(url):
    request = Request(url, headers={"User-Agent": "Design-MCP-source-review", "Accept": "application/json"})
    with urlopen(request, timeout=10) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Response exceeded the source review byte limit")
    return json.loads(body)


def lead(title, published, url):
    return {"title": " ".join(title.split())[:220], "date": date.fromisoformat(published).isoformat(), "url": url}


def read_release(repo, fetch):
    api = f"https://api.github.com/repos/{repo}/releases/latest"
    result = fetch(api)
    link = result["html_url"]
    parsed = urlsplit(link)
    if (parsed.scheme, parsed.netloc) != ("https", "github.com") or not parsed.path.lower().startswith(
        f"/{repo.lower()}/releases/tag/"
    ):
        raise ValueError("Unexpected release link")
    return [lead(result["tag_name"], result["published_at"][:10], link)]


def read_papers(query, since, fetch):
    params = urlencode({"search": query, "filter": f"from_publication_date:{since}",
                        "per_page": 5, "select": "id,title,publication_date"})
    result = fetch(f"https://api.openalex.org/works?{params}")
    return [lead(item["title"], item["publication_date"], item["id"])
            for item in result["results"]
            if re.fullmatch(r"https://openalex\.org/W[0-9]+", item["id"])]


def read_crossref(query, since, fetch):
    params = urlencode({"query.bibliographic": query, "filter": f"from-pub-date:{since}",
                        "rows": 8, "select": "DOI,title,published,type"})
    result = fetch(f"https://api.crossref.org/works?{params}")
    leads = []
    seen = set()
    for item in result["message"]["items"]:
        if not isinstance(item, dict) or item.get("type") not in CROSSREF_TYPES:
            continue
        identifier = item.get("DOI")
        if not isinstance(identifier, str):
            continue
        doi = identifier.lower()
        if doi in seen or not re.fullmatch(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", doi):
            continue
        try:
            parts = item["published"]["date-parts"][0]
            titles = item["title"]
            if len(parts) not in (2, 3) or not isinstance(titles, list):
                continue
            has_day = len(parts) == 3
            earliest = date(parts[0], parts[1], parts[2] if has_day else 1)
            title = titles[0].strip()
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            continue
        if earliest < since or not title:
            continue
        record = lead(title, earliest.isoformat(), f"https://doi.org/{quote(doi, safe='/')}")
        if not has_day:
            record["date"] = record["date"][:7]
        leads.append(record)
        seen.add(doi)
    return leads


def source_result(name, read, *arguments):
    try:
        return {"source": name, "leads": read(*arguments)}
    except HTTPError as error:
        return {"source": name, "error": f"HTTP {error.code}"}
    except (OSError, AttributeError, KeyError, TypeError, ValueError) as error:
        return {"source": name, "error": type(error).__name__}


def collect(today, fetch=fetch_json, pause=sleep):
    since = today - timedelta(days=90)
    sources = [source_result(repo, read_release, repo, fetch) for repo in RELEASES]
    primary_error = None
    crossref_used = False
    for query in RESEARCH:
        if primary_error is None:
            outcome = source_result(query, read_papers, query, since, fetch)
            primary_error = outcome.get("error")
            if primary_error is None:
                sources.append({**outcome, "provider": "OpenAlex"})
                continue
        if crossref_used:
            pause(CROSSREF_INTERVAL_SECONDS)
        outcome = source_result(query, read_crossref, query, since, fetch)
        sources.append({**outcome, "provider": "Crossref", "openalex_error": primary_error})
        crossref_used = True
    return sources


def print_report(sources):
    print("# Design source review\n")
    print("Review these public leads before proposing a design or harness change.\n")
    for source in sources:
        print(f"## {source['source']}\n")
        if "openalex_error" in source:
            print(f"Using Crossref because OpenAlex was unavailable ({source['openalex_error']}).\n")
        if "error" in source:
            print(f"{source.get('provider', 'Source')} unavailable ({source['error']}).\n")
            continue
        if not source["leads"]:
            print("No results in the current search.\n")
        for lead in source["leads"]:
            url = escape(lead["url"], quote=True)
            print(f'- {lead["date"]} · <a href="{url}">{escape(lead["title"])}</a>')
        print()


if __name__ == "__main__":
    sources = collect(date.today())
    print_report(sources)
    raise SystemExit(int(all("error" in source for source in sources)))
