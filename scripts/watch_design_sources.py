"""Collect public design and browser source leads for review."""

from datetime import date, timedelta
from html import escape
import json
import re
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


RELEASES = ("USWDS/uswds", "remorses/playwriter")
RESEARCH = ("screenshot to code UI generation", "visual critique user interface design")
MAX_BYTES = 256_000


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


def collect(today, fetch=fetch_json):
    since = today - timedelta(days=90)
    sources = []

    def inspect(name, read, *arguments):
        try:
            leads = read(*arguments, fetch)
        except HTTPError as error:
            sources.append({"source": name, "error": f"HTTP {error.code}"})
        except (OSError, AttributeError, KeyError, TypeError, ValueError) as error:
            sources.append({"source": name, "error": type(error).__name__})
        else:
            sources.append({"source": name, "leads": leads})

    for repo in RELEASES:
        inspect(repo, read_release, repo)
    for query in RESEARCH:
        inspect(query, read_papers, query, since)
    return sources


def print_report(sources):
    print("# Design source review\n")
    print("Review these public leads before proposing a design or harness change.\n")
    for source in sources:
        print(f"## {source['source']}\n")
        if "error" in source:
            print(f"Source unavailable ({source['error']}).\n")
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
