# Grok Bot Rocks

A forkable, searchable mirror of the public **Grok Bot** directory.

Upstream: [“Every Grok Bot: The Complete Directory”](https://readmultiplex.com/grokbot-rocks/) by
[@ReadMultiplex](https://readmultiplex.com/) (Brian Roemmele). This repo is an unaffiliated fork of
that page’s **public** listing: the same bots, the same one-line descriptions, in a static site you
can clone, grep, embed or self-host. Members-only sections are not included and are not scraped.

- **780 public bots in 26 categories**, captured as a JSON snapshot.
- Zero build step, zero dependencies, zero tracking — one HTML page plus one JSON file.
- Search across name, author, description and category; filter by category; sort three ways.

## Layout

```
index.html            static page (no framework, no CDN)
styles.css            dark theme
app.js                search / filter / render
data/directory.json   the snapshot the site reads
scripts/scrape.py     rebuilds the snapshot from the upstream page
```

## Run it locally

```bash
uv run --script scripts/scrape.py                     # refresh data/directory.json
python3 -m http.server 8080                           # http://localhost:8080
```

`index.html` fetches `data/directory.json`, so open it over HTTP, not `file://`.

## Refresh the data

```bash
uv run --script scripts/scrape.py
```

The scraper reads the upstream page with the standard library only, keeps the first occurrence of
each bot URL (the popular-bots block repeats entries), and refuses to overwrite the snapshot if it
parses fewer than 100 bots — that is the signal that upstream changed its markup.

## Deploy

`.github/workflows/pages.yml` publishes the repo root to GitHub Pages on every push to `main`.
Nothing is compiled; Pages just serves these files.

## Attribution and licence

Bot names, authors and descriptions are the work of Brian Roemmele and the individual bot builders;
they remain their property. This fork adds only the page, the search UI and the scraper, and links
every entry back to its `x.ai` bot page. If you are the rights holder and want the mirror changed or
removed, open an issue and it will be handled promptly.

The code in this repo (`scripts/scrape.py`, `index.html`, `styles.css`, `app.js`) is MIT licensed —
see [LICENSE](LICENSE).
