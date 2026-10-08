# tme-s

Read public Telegram channels **without an API key, phone number or account**.

Every public channel has a logged-out web preview at `https://t.me/s/<channel>`: the page a browser
shows when you open a channel link without Telegram. `tme-s` reads that page and prints posts as
JSON lines. One file, Python 3 standard library only.

Most Telegram OSINT tools need an `api_id`/`api_hash` plus a phone number, or a bot token. If you
only need public channels, you can skip all of that, and nothing ties the collection to your number
or sock puppet account.

## Usage

```bash
python3 tme_s.py durov                      # last ~20 posts
python3 tme_s.py durov telegram -p 5        # 5 pages back (~100 posts), only posts containing "telegram"
python3 tme_s.py durov --since 2026-09-01   # stop at posts older than this date
python3 tme_s.py durov --state seen.json    # only posts newer than the previous run
```

Output, one JSON object per line, newest first:

```json
{"post": "durov/548", "url": "https://t.me/durov/548", "date": "2026-09-11T16:04:02+00:00", "views": "1.95M", "text": "Telegram has become the sponsor of Codeforces...", "links": []}
```

Pipe it into `jq` or save it for evidence.

## Watch a channel from cron

`--state FILE` remembers the newest post ID per channel. Each run prints only posts published since
the previous run (reading back up to `-p` pages) and updates the file. Empty output means nothing new.

```bash
# every 15 minutes: new posts mentioning "leak" in two channels, appended to a log
*/15 * * * * cd ~/tme-s && for c in durov telegram; do python3 tme_s.py $c leak --state seen.json -p 3; done >> hits.jsonl
```

## Tests

Offline, on two saved pages of `t.me/s/durov`:

```bash
python3 -m unittest discover tests
```

## Limits

- Public channels only. Groups, private channels and comment threads are not in the preview.
- A channel owner can disable the web preview; then there is nothing to read.
- ~20 posts per page; older pages are fetched with `?before=<post_id>` (`-p`).
- View counts are rounded the way Telegram shows them (`1.95M`).
- Media files are not downloaded, only text, links, date and views.
- Deleted posts leave gaps in the IDs (`durov/530` does not exist); that is expected.
- macOS with python.org Python: if you get `CERTIFICATE_VERIFY_FAILED`, run
  `/Applications/Python 3.x/Install Certificates.command` once, or prefix the command with
  `SSL_CERT_FILE=/etc/ssl/cert.pem`.

Please respect Telegram's Terms of Service and the law where you work.

## Hosted version

If you need this for many channels on a schedule without keeping a machine on, with deep history,
retries and export to OpenCTI (STIX 2.1) or MISP, I run a hosted version on Apify:
[Telegram Channel Monitor](https://apify.com/ax_dev/telegram-channel-monitor) (paid per result,
needs an Apify account). The script above stays free and does not depend on it.

## License

MIT
