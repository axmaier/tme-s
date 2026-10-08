#!/usr/bin/env python3
"""Read public Telegram channels without an API key, phone number or account.

Uses the logged-out web preview https://t.me/s/<channel>, the page a browser shows
when you open a channel link without Telegram. Python standard library only.

    python3 tme_s.py durov                     # last ~20 posts as JSON lines
    python3 tme_s.py durov telegram -p 5       # 5 pages back, only posts containing "telegram"
    python3 tme_s.py durov --since 2026-09-01  # stop at posts older than this date
    python3 tme_s.py durov --state seen.json   # only posts newer than the previous run (for cron)
"""
import argparse, html, json, os, re, sys, time, urllib.request

UA = "Mozilla/5.0 (compatible; tme-s; +https://github.com/axmaier/tme-s)"


def fetch(channel, before=None):
    url = f"https://t.me/s/{channel}" + (f"?before={before}" if before else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return parse(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))


def parse(page):
    posts = []
    for block in page.split('class="tgme_widget_message_wrap')[1:]:
        pid = re.search(r'data-post="([^"]+)"', block)
        if not pid:
            continue
        text = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        when = re.search(r'<time datetime="([^"]+)"', block)
        views = re.search(r'tgme_widget_message_views">([^<]+)<', block)
        body = text.group(1) if text else ""
        links = sorted(set(html.unescape(u) for u in re.findall(r'<a href="(https?://[^"]+)"', body)))
        clean = re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", body))
        posts.append({
            "post": pid.group(1),
            "url": "https://t.me/" + pid.group(1),
            "date": when.group(1) if when else None,
            "views": views.group(1) if views else None,
            "text": html.unescape(clean),
            "links": links,
        })
    return posts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read a public Telegram channel via t.me/s/ (no API key, no login).")
    ap.add_argument("channel", help="channel username, e.g. durov (no @)")
    ap.add_argument("keyword", nargs="?", help="only print posts containing this text (case-insensitive)")
    ap.add_argument("-p", "--pages", type=int, default=1, help="how many pages of ~20 posts to read (default 1)")
    ap.add_argument("--since", help="stop when posts get older than this ISO date, e.g. 2026-09-01")
    ap.add_argument("--state", metavar="FILE", help="JSON file with the last seen post per channel; "
                    "print only newer posts and update it (reads back up to -p pages)")
    a = ap.parse_args(argv)

    channel, kw, before = a.channel.lstrip("@"), (a.keyword or "").lower(), None
    state = {}
    if a.state and os.path.exists(a.state):
        with open(a.state) as f:
            state = json.load(f)
    last = state.get(channel, 0)
    newest = last
    for page in range(a.pages):
        posts = fetch(channel, before)
        if not posts:
            if page == 0:
                sys.exit(f"no posts: '{channel}' is private, mistyped, or has the web preview disabled")
            break
        old = False
        for p in reversed(posts):  # newest first
            pid = int(p["post"].split("/")[-1])
            newest = max(newest, pid)
            if pid <= last:
                old = True
                continue
            if a.since and p["date"] and p["date"][:10] < a.since:
                old = True
                continue
            if not kw or kw in p["text"].lower():
                print(json.dumps(p, ensure_ascii=False))
        if old:
            break
        before = posts[0]["post"].split("/")[-1]
        time.sleep(PAUSE)  # be polite

    if a.state and newest > last:
        state[channel] = newest
        with open(a.state + ".tmp", "w") as f:
            json.dump(state, f, indent=1, sort_keys=True)
        os.replace(a.state + ".tmp", a.state)


PAUSE = 1

if __name__ == "__main__":
    main()
