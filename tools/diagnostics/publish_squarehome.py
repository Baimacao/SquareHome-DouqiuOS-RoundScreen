#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 发布工具（REST API，无需本机 git）。token 只从环境/文件读取，绝不打印。

    python publish_squarehome.py check
    python publish_squarehome.py create-repo [--private]
    python publish_squarehome.py publish <staging_dir> <tag> <release_title> <notes_md> [--asset <file>]
"""
import base64
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "Baimacao"
REPO = "SquareHome-DouqiuOS-RoundScreen"
BRANCH = "main"
API = "https://api.github.com"

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_token.txt")
ENV_FILES = [
    os.path.join(os.environ["DSH_HOME"], ".env") if os.environ.get("DSH_HOME") else "",
    os.path.expanduser("~/.dsh/.env"),
    os.path.expanduser("~/.dsh/.github-token"),
]
BINARY_EXT = {".apk", ".jar", ".png", ".jpg", ".webp", ".zip"}


def load_token():
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        v = os.environ.get(name, "").strip()
        if v:
            return v, "env:" + name
    for path in ENV_FILES:
        if path and os.path.exists(path):
            try:
                with io.open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GITHUB_TOKEN=") or line.startswith("GH_TOKEN="):
                            v = line.split("=", 1)[1].strip()
                            if v:
                                return v, path
                        if path.endswith(".github-token") and len(line) > 20 and "=" not in line:
                            return line, path
            except OSError:
                pass
    if os.path.exists(TOKEN_FILE):
        v = io.open(TOKEN_FILE, encoding="utf-8").read().strip()
        if v:
            return v, TOKEN_FILE
    raise SystemExit("no GitHub token found")


TOKEN, TOKEN_SRC = load_token()


def api(method, path, payload=None, raw=False, accept="application/vnd.github+json"):
    url = path if path.startswith("http") else API + path
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "dsh-squarehome-publisher")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            return r.status, (body if raw else (json.loads(body) if body else None))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body


def cmd_check():
    print("token source:", TOKEN_SRC, "| length:", len(TOKEN))
    st, me = api("GET", "/user")
    print("GET /user ->", st, (me.get("login") if isinstance(me, dict) else me))
    st, repo = api("GET", f"/repos/{OWNER}/{REPO}")
    print(f"GET /repos/{OWNER}/{REPO} ->", st, (repo.get("full_name") if isinstance(repo, dict) else repo))
    st, rl = api("GET", "/user/repos?per_page=1")
    if isinstance(rl, list) and rl:
        print("existing repo sample scopes ok; sample:", rl[0]["full_name"])


def cmd_create(private=False):
    payload = {
        "name": REPO,
        "description": "DouqiuOS 圆屏适配 mod for Square Home 3.0.1 (480x480 round watch): app-drawer list arc fit + switch, OOBE adaptation, About attribution",
        "private": bool(private),
        "has_issues": True,
        "has_wiki": False,
        "auto_init": False,
    }
    st, res = api("POST", "/user/repos", payload)
    print("POST /user/repos ->", st)
    if isinstance(res, dict):
        print("  full_name:", res.get("full_name"), "| private:", res.get("private"), "| url:", res.get("html_url"))
    else:
        print("  ", str(res)[:400])
    return st == 201


def blob_sha(content):
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(content))
    h.update(content)
    return h.hexdigest()


def ensure_nonempty():
    """空仓库不能直接用 Git Data API 建 blob（409），先用 Contents API 建一个初始提交。"""
    global BRANCH
    st, ref = api("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")
    if st == 200:
        return
    st, repo = api("GET", f"/repos/{OWNER}/{REPO}")
    branch = repo.get("default_branch", BRANCH) if isinstance(repo, dict) else BRANCH
    payload = {
        "message": "chore: init repository",
        "content": base64.b64encode(b"# bootstrap\n").decode("ascii"),
    }
    st, res = api("PUT", f"/repos/{OWNER}/{REPO}/contents/.bootstrap?branch={branch}", payload)
    print("bootstrap via Contents API ->", st, (res.get("commit", {}).get("sha") if isinstance(res, dict) else str(res)[:200]))
    BRANCH = branch


def cmd_publish(staging, tag, title, notes_path, asset=None):
    ensure_nonempty()
    entries = []
    for root, _dirs, files in os.walk(staging):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, staging).replace("\\", "/")
            entries.append((rel, full))
    entries.sort()
    print(f"staging: {staging} -> {len(entries)} files")

    # 1) blobs
    tree = []
    for rel, full in entries:
        data = open(full, "rb").read()
        st, res = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs",
                      {"content": base64.b64encode(data).decode("ascii"), "encoding": "base64"})
        if st != 201:
            raise SystemExit(f"blob failed {rel}: {st} {str(res)[:200]}")
        tree.append({"path": rel, "mode": "100755" if rel.endswith(".sh") else "100644",
                     "type": "blob", "sha": res["sha"]})
        print(f"  blob {rel} ({len(data)} bytes) ok")

    # 2) parent commit (main 可能是空的 -> 用空 tree 建首 commit)
    st, ref = api("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")
    parents = []
    base_tree = None
    if st == 200 and isinstance(ref, dict):
        parents = [ref["object"]["sha"]]
        st2, c = api("GET", f"/repos/{OWNER}/{REPO}/git/commits/{parents[0]}")
        if st2 == 200:
            base_tree = c["tree"]["sha"]
        print("parent commit:", parents[0])
    else:
        print("no existing main -> first commit")

    st, t = api("POST", f"/repos/{OWNER}/{REPO}/git/trees",
                {"tree": tree, **({"base_tree": base_tree} if base_tree else {})})
    if st != 201:
        raise SystemExit(f"tree failed: {st} {str(t)[:300]}")
    print("tree:", t["sha"])

    st, commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                     {"message": f"release: {tag}", "tree": t["sha"], "parents": parents})
    if st != 201:
        raise SystemExit(f"commit failed: {st} {str(commit)[:300]}")
    print("commit:", commit["sha"])

    if parents:
        st, r = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": False})
    else:
        st, r = api("POST", f"/repos/{OWNER}/{REPO}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})
    print("ref update ->", st)

    st, tg = api("POST", f"/repos/{OWNER}/{REPO}/git/refs", {"ref": f"refs/tags/{tag}", "sha": commit["sha"]})
    print(f"tag {tag} ->", st, "" if st == 201 else str(tg)[:200])

    notes = io.open(notes_path, encoding="utf-8").read() if notes_path and os.path.exists(notes_path) else ""
    st, rel = api("POST", f"/repos/{OWNER}/{REPO}/releases",
                  {"tag_name": tag, "name": title, "body": notes, "draft": False, "prerelease": False})
    print("release ->", st)
    rel_id = rel["id"] if isinstance(rel, dict) else None

    if asset and os.path.exists(asset) and rel_id:
        name = os.path.basename(asset)
        upload_url = f"https://uploads.github.com/repos/{OWNER}/{REPO}/releases/{rel_id}/assets?name={name}"
        with open(asset, "rb") as f:
            data = f.read()
        req = urllib.request.Request(upload_url, data=data, method="POST")
        req.add_header("Authorization", "Bearer " + TOKEN)
        req.add_header("Content-Type", "application/vnd.android.package-archive")
        req.add_header("User-Agent", "dsh-squarehome-publisher")
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                res = json.loads(r.read())
            print("asset uploaded:", res.get("browser_download_url"), res.get("size"), "bytes")
        except urllib.error.HTTPError as e:
            print("asset upload failed:", e.code, e.read().decode("utf-8", "replace")[:300])

    print("done:", f"https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        cmd_check()
    elif cmd == "create-repo":
        cmd_create(private="--private" in sys.argv)
    elif cmd == "publish":
        staging, tag, title, notes = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        asset = None
        if "--asset" in sys.argv:
            asset = sys.argv[sys.argv.index("--asset") + 1]
        cmd_publish(staging, tag, title, notes, asset)
    else:
        raise SystemExit(__doc__)
