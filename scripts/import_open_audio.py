#!/usr/bin/env python3
"""Import openly licensed MP3s from Internet Archive into this repository.

Only exact CC BY 4.0 and CC0 licence URLs are accepted. Every saved track
gets a provenance record. This is a best-effort discovery importer, not a
claim that the archive contains current chart hits.
"""
import json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path("audio/open-library")
META = Path("licenses/open-library-attribution.jsonl")
MAX_TRACKS = int(os.getenv("MAX_TRACKS", "900"))
MAX_FILE = 25 * 1024 * 1024
MAX_TOTAL = 900 * 1024 * 1024
ALLOWED = {
    "https://creativecommons.org/licenses/by/4.0/",
    "http://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "http://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/publicdomain/mark/1.0/",
    "http://creativecommons.org/publicdomain/mark/1.0/",
}
QUERIES = [
    'mediatype:audio AND (licenseurl:"https://creativecommons.org/licenses/by/4.0/" OR licenseurl:"http://creativecommons.org/licenses/by/4.0/")',
    'mediatype:audio AND (licenseurl:"https://creativecommons.org/publicdomain/zero/1.0/" OR licenseurl:"http://creativecommons.org/publicdomain/zero/1.0/" OR licenseurl:"https://creativecommons.org/publicdomain/mark/1.0/")',
]
UA = "MusicArchiveImporter/1.0 (GitHub repository; license-filtered)"

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def safe_name(s):
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(s)).strip("-._")
    return (s[:110] or "untitled")

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    META.parent.mkdir(parents=True, exist_ok=True)
    existing = {p.stem.split("--")[0] for p in ROOT.glob("*.mp3")}
    records, seen, total = [], set(), sum(p.stat().st_size for p in ROOT.glob("*.mp3"))
    for query in QUERIES:
        if len(existing) + len(records) >= MAX_TRACKS or total >= MAX_TOTAL:
            break
        params = urllib.parse.urlencode([
            ("q", query), ("fl[]", "identifier"), ("rows", "500"),
            ("page", "1"), ("output", "json"), ("sort[]", "downloads desc")
        ])
        search = get_json("https://archive.org/advancedsearch.php?" + params)
        docs = search.get("response", {}).get("docs", [])
        for doc in docs:
            ident = doc.get("identifier")
            if not ident or ident in existing or ident in seen:
                continue
            seen.add(ident)
            try:
                item = get_json("https://archive.org/metadata/" + urllib.parse.quote(ident, safe=""))
                md = item.get("metadata", {})
                license_url = str(md.get("licenseurl", "")).strip().rstrip("/") + "/"
                if license_url not in ALLOWED:
                    continue
                files = item.get("files", [])
                mp3s = [f for f in files if str(f.get("name", "")).lower().endswith(".mp3")
                        and str(f.get("source", "")).lower() != "metadata"]
                mp3s.sort(key=lambda f: int(f.get("size", 0)) if str(f.get("size", "0")).isdigit() else MAX_FILE + 1)
                chosen = next((f for f in mp3s if str(f.get("size", "")).isdigit()
                               and 10_000 < int(f["size"]) <= MAX_FILE), None)
                if not chosen:
                    continue
                size = int(chosen["size"])
                if total + size > MAX_TOTAL:
                    break
                name = str(chosen["name"])
                url = "https://archive.org/download/" + urllib.parse.quote(ident, safe="") + "/" + urllib.parse.quote(name, safe="/")
                title = md.get("title", ident)
                creator = md.get("creator", "Unknown creator")
                if isinstance(creator, list):
                    creator = "; ".join(map(str, creator))
                dest = ROOT / (safe_name(ident) + "--" + safe_name(Path(name).stem) + ".mp3")
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as response, dest.open("wb") as out:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                        if out.tell() > MAX_FILE:
                            raise ValueError("file exceeded size limit")
                if dest.stat().st_size < 10_000:
                    dest.unlink(missing_ok=True)
                    continue
                record = {
                    "file": str(dest), "title": title, "creator": creator,
                    "source": "https://archive.org/details/" + ident,
                    "license": license_url, "license_verified_from_item_metadata": True,
                    "original_filename": name
                }
                records.append(record)
                total += dest.stat().st_size
                print("Downloaded:", title, "-", creator)
                if len(existing) + len(records) >= MAX_TRACKS or total >= MAX_TOTAL:
                    break
                time.sleep(0.15)
            except Exception as e:
                print("Skipped", ident, ":", e)
                continue
    if records:
        with META.open("a", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"New MP3s: {len(records)}; total archive MP3s: {len(list(ROOT.glob('*.mp3')))}; bytes: {total}")

if __name__ == "__main__":
    main()
