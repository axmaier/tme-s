"""Offline tests on saved t.me/s/durov pages: python3 -m unittest discover tests"""
import contextlib, io, json, os, sys, tempfile, unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tme_s

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
PAGES = {None: "durov.html", "528": "durov_before.html"}  # ?before=528 is the next page back


def fake_fetch(channel, before=None):
    name = PAGES.get(before)
    if channel != "durov" or not name:
        return []
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return tme_s.parse(f.read())


def run(*argv):
    out = io.StringIO()
    with mock.patch.object(tme_s, "fetch", fake_fetch), mock.patch.object(tme_s, "PAUSE", 0), \
            contextlib.redirect_stdout(out):
        tme_s.main(list(argv))
    return [json.loads(line) for line in out.getvalue().splitlines()]


def ids(posts):
    return [int(p["post"].split("/")[1]) for p in posts]


# real gaps: durov/511 and durov/530 were deleted, Telegram skips them in the preview
P1 = [i for i in range(548, 527, -1) if i != 530]
P2 = [i for i in range(527, 507, -1) if i != 511]


def load(path):
    with open(path) as f:
        return json.load(f)


class TmeS(unittest.TestCase):
    def test_parse_page(self):
        posts = fake_fetch("durov")
        self.assertEqual(ids(posts), P1[::-1])
        for p in posts:
            self.assertTrue(p["date"] and p["views"] and p["url"].startswith("https://t.me/durov/"))
        self.assertTrue(sum(bool(p["text"]) for p in posts) >= 15)
        self.assertNotIn("<", "".join(p["text"] for p in posts))

    def test_newest_first(self):
        self.assertEqual(ids(run("durov")), P1)

    def test_pagination(self):
        self.assertEqual(ids(run("@durov", "-p", "3")), P1 + P2)  # page 3 is empty: stops cleanly

    def test_keyword(self):
        posts = run("durov", "TELEGRAM")
        self.assertTrue(posts)
        self.assertTrue(all("telegram" in p["text"].lower() for p in posts))

    def test_since(self):
        posts = run("durov", "-p", "2", "--since", "2026-09-01")
        self.assertTrue(posts)
        self.assertTrue(all(p["date"][:10] >= "2026-09-01" for p in posts))

    def test_state_only_new(self):
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "seen.json")
            with open(st, "w") as f:
                json.dump({"durov": 540, "other": 7}, f)
            self.assertEqual(ids(run("durov", "--state", st, "-p", "5")), list(range(548, 540, -1)))
            self.assertEqual(load(st), {"durov": 548, "other": 7})
            self.assertEqual(run("durov", "--state", st, "-p", "5"), [])  # second run: nothing new

    def test_state_first_run_reads_back_pages(self):
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "seen.json")
            self.assertEqual(ids(run("durov", "--state", st, "-p", "2")), P1 + P2)
            self.assertEqual(load(st), {"durov": 548})

    def test_unknown_channel(self):
        with self.assertRaises(SystemExit) as e:
            run("no_such_channel_xyz")
        self.assertIn("no posts", str(e.exception.code))


if __name__ == "__main__":
    unittest.main()
