"""Collect public design and browser source leads for review."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from html import escape, unescape
import json
import re
from time import sleep
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


RELEASES = ("USWDS/uswds", "remorses/playwriter")
RESEARCH = (
    "screenshot to code UI generation",
    "visual critique user interface design",
    "creative range originality LLM generated user interface design",
)
MAX_BYTES = 256_000
CROSSREF_TYPES = {"journal-article", "proceedings-article", "posted-content"}
CROSSREF_INTERVAL_SECONDS = 1.25
HN_API = "https://hacker-news.firebaseio.com/v0"
CSSDA = "https://www.cssdesignawards.com"
AWARD_LINK = re.compile(
    r'<h3\s+class="home-wotd__title">\s*<a\s+href="(/sites/[a-z0-9-]+/[0-9]+/)">([^<]+)</a>',
    re.I,
)
AWARD_DATE = re.compile(r'<h1\s+class="single-website__date">Website Of The Day (\d{4} [A-Za-z]{3} \d{1,2})</h1>')
SHOW_HN_LOOKUP_LIMIT = 30
SHOW_HN_WORKERS = 4
VISUAL_DEMO = re.compile(
    r"\b(?:interactive|design system|visuali[sz]ation|typography|gallery|portfolio|"
    r"webgl|webgpu|(?:3d|star) map|exhibit|simulator|calculator|animate your code)\b",
    re.I,
)
HTML_TAG = re.compile(r"<[^>]*>")


def fetch_bytes(url, accept):
    request = Request(url, headers={"User-Agent": "Design-MCP-source-review", "Accept": accept})
    with urlopen(request, timeout=10) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Response exceeded the source review byte limit")
    return body


def fetch_json(url):
    return json.loads(fetch_bytes(url, "application/json"))


def fetch_award_page(url):
    return fetch_bytes(url, "text/html").decode("utf-8")


def lead(title, published, url):
    return {"title": " ".join(title.split())[:220], "date": date.fromisoformat(published).isoformat(), "url": url}


def read_css_award(today, fetch):
    winner = AWARD_LINK.search(fetch(f"{CSSDA}/"))
    if not winner:
        raise ValueError("Website of the Day link was not found")
    link, title = winner.groups()
    url = CSSDA + link
    award = AWARD_DATE.search(fetch(url))
    if not award:
        raise ValueError("Website of the Day date was not found")
    published = datetime.strptime(award[1], "%Y %b %d").date()
    if not today - timedelta(days=7) <= published <= today:
        raise ValueError("Website of the Day date is outside the review window")
    return [lead(unescape(title), published.isoformat(), url)]


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



def read_show_hn(today, fetch):
    ids = fetch(f"{HN_API}/showstories.json")
    if not isinstance(ids, list):
        raise ValueError("Unexpected Show HN feed")
    relevant = []
    failures = []
    ids = tuple(dict.fromkeys(i for i in ids[:SHOW_HN_LOOKUP_LIMIT] if type(i) is int and i > 0))
    def fetch_item(item_id):
        try:
            return fetch(f"{HN_API}/item/{item_id}.json")
        except (OSError, ValueError) as error:
            return error

    with ThreadPoolExecutor(max_workers=SHOW_HN_WORKERS) as pool:
        items = list(pool.map(fetch_item, ids))
    for item_id, item in zip(ids, items):
        if isinstance(item, Exception):
            failures.append(item)
            continue
        if not isinstance(item, dict) or item.get("id") != item_id or item.get("type") != "story":
            continue
        if item.get("dead") or item.get("deleted"):
            continue
        title, timestamp, score = item.get("title"), item.get("time"), item.get("score")
        if not isinstance(title, str) or not re.match(r"^Show HN\s*:", title, re.I):
            continue
        description = item.get("text")
        description = unescape(HTML_TAG.sub(" ", description[:4000])) if isinstance(description, str) else ""
        if not (VISUAL_DEMO.search(title) or VISUAL_DEMO.search(description)):
            continue
        if type(timestamp) is not int or type(score) is not int or not 0 < timestamp < 4_102_444_800:
            continue
        published = datetime.fromtimestamp(timestamp, timezone.utc).date()
        if not today - timedelta(days=14) <= published <= today:
            continue
        url = f"https://news.ycombinator.com/item?id={item_id}"
        record = {**lead(title, published.isoformat(), url), "points": score}
        descendants = item.get("descendants")
        if type(descendants) is int and descendants >= 0:
            record["comments"] = descendants
        relevant.append(record)
    if ids and len(failures) == len(ids):
        raise failures[0]
    return sorted(relevant, key=lambda item: (-item["points"], -item.get("comments", 0), item["url"]))[:5]


def source_result(name, read, *arguments):
    try:
        return {"source": name, "leads": read(*arguments)}
    except HTTPError as error:
        return {"source": name, "error": f"HTTP {error.code}"}
    except (OSError, AttributeError, KeyError, TypeError, ValueError) as error:
        return {"source": name, "error": type(error).__name__}


def collect(today, fetch=fetch_json, pause=sleep, fetch_award=fetch_award_page):
    since = today - timedelta(days=90)
    sources = [source_result(repo, read_release, repo, fetch) for repo in RELEASES]
    sources.append(source_result("Show HN visual demos", read_show_hn, today, fetch))
    sources.append(source_result("CSS Design Awards Website of the Day", read_css_award, today, fetch_award))
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
    print("- [Awwwards current winner and nominees](https://www.awwwards.com/)")
    print("- [CSS Design Awards current winners](https://www.cssdesignawards.com/)")
    print("- [FWA launches from award winners](https://www.thefwa.net/label/launch)")
    print("- [Codrops Creative Hub demos](https://tympanus.net/codrops/hub/all/)\n")
    print("## Social leads to check in the browser\n")
    for label, query in (
        ("UI design on X", "UI design filter:images min_faves:200"),
        ("Design engineering on X", "design engineering filter:videos min_faves:200"),
        ("Micro-interactions on X", "micro-interaction filter:videos min_faves:100"),
        ("Design details on X", "design details filter:images min_faves:200"),
        ("Interface critique on X", "interface design critique min_faves:100"),
        ("Redesign comparisons on X", "before and after redesign filter:images min_faves:300"),
        ("Interface motion on X", "motion design UI filter:videos min_faves:200"),
        ("Product design breakdowns on X", "product design breakdown filter:images min_faves:150"),
    ):
        params = urlencode({"q": query, "f": "live"})
        print(f"- [{label}](https://x.com/search?{params})")
    params = urlencode({"q": "portfolio OR interactive", "sort": "top", "t": "week"})
    print(f"- [Recent web design discussions on Reddit](https://www.reddit.com/r/webdesign/search/?{params})\n")
    print("Open the live work and verify the original post, engagement and interaction.\n")
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
            signals = [f"{lead['points']} points"] if "points" in lead else []
            if "comments" in lead:
                count = lead["comments"]
                signals.append(f"{count} {'comment' if count == 1 else 'comments'}")
            engagement = f" ({', '.join(signals)} at capture)" if signals else ""
            print(f'- {lead["date"]} · <a href="{url}">{escape(lead["title"])}</a>{engagement}')
        print()


if __name__ == "__main__":
    sources = collect(date.today())
    print_report(sources)
    raise SystemExit(int(all("error" in source for source in sources)))
