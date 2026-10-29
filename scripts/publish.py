"""Obsidian 노트 중 `publish: true`인 것만 Hugo page bundle로 옮긴다.

python3 scripts/publish.py           미리보기
python3 scripts/publish.py --write   파일 쓰기
"""
import json
import re
from pathlib import Path


class PublishError(Exception):
    pass


ALLOWED_KINDS = ("설계", "트러블슈팅", "회고", "개념")
OBSIDIAN_ONLY = {"categories", "author", "topics", "status", "created", "url", "language"}
OUTPUT_KEYS = ("title", "date", "description", "kind", "tags", "project", "milestone", "book", "book_author")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}

FENCE = re.compile(r"^\s*(```|~~~)")
COMMENT = re.compile(r"%%.*?%%", re.S)
EMBED = re.compile(r"!\[\[([^\]]+)\]\]")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


# ---- front matter ----

def _scalar(raw):
    raw = raw.strip()
    if raw == "":
        return None
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith("[") and raw.endswith("]"):
        return [_scalar(x) for x in raw[1:-1].split(",") if x.strip()]
    return raw


def parse_note(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        raise PublishError("front matter가 닫히지 않았다")
    lines = text[4:end].split("\n")
    body = text[end + 4:].removeprefix("\n")
    meta, i = {}, 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        key, sep, rest = line.partition(":")
        if not sep or line[0].isspace():
            raise PublishError(f"front matter를 읽을 수 없다: {line!r}")
        key = key.strip()
        nested = []
        while i < len(lines) and lines[i][:1].isspace():
            nested.append(lines[i].strip())
            i += 1
        if key in OBSIDIAN_ONLY:
            continue
        if nested:
            if rest.strip() or not all(n.startswith("- ") for n in nested if n):
                raise PublishError(f"지원하지 않는 front matter 형태: {key}")
            meta[key] = [_scalar(n[2:]) for n in nested if n]
        else:
            meta[key] = _scalar(rest)
    return meta, body


def to_front_matter(meta: dict, fallback_title: str) -> str:
    values = dict(meta)
    values["title"] = meta.get("title") or fallback_title
    values["date"] = meta.get("published")
    out = ["---"]
    for key in OUTPUT_KEYS:
        v = values.get(key)
        if v in (None, "", []):
            continue
        if key == "date":
            out.append(f"date: {v}")
        else:
            out.append(f"{key}: {json.dumps(v, ensure_ascii=False)}")
    out.append("generated: obsidian")
    out.append("---")
    return "\n".join(out) + "\n"


# ---- safety ----

SAFETY_PATTERNS = (
    ("이메일", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("전화번호", re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b")),
    ("로컬 경로", re.compile(r"/Users/[^/\s]+|(?<![\w.])~/")),
    ("사설 IP", re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    ("토큰", re.compile(
        r"sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}"
        r"|AKIA[0-9A-Z]{16}|xox[abprs]-[A-Za-z0-9-]+|-----BEGIN"
    )),
)


def load_denylist(vault: Path) -> list[str]:
    path = vault / ".publish-denylist"
    if not path.exists():
        return []
    words = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [w for w in words if w and not w.startswith("#")]


def check_safety(text: str, denylist: list[str], allowed_emails: set[str]) -> list[str]:
    problems = []
    for n, line in enumerate(text.split("\n"), 1):
        for kind, pattern in SAFETY_PATTERNS:
            for m in pattern.finditer(line):
                if kind == "이메일" and m.group(0) in allowed_emails:
                    continue
                problems.append(f"줄 {n}: {kind} ({m.group(0)[:6]}…)")
        lowered = line.lower()
        for word in denylist:
            if word.lower() in lowered:
                problems.append(f"줄 {n}: 차단어 ({word})")
    return problems


# ---- body ----

def heading_anchor(heading: str) -> str:
    s = heading.strip().lower().replace(" ", "-")
    return re.sub(r"[^\w\-]", "", s)


def _bundle_name(name: str) -> str:
    return name.replace(" ", "-")


def _convert_chunk(chunk, link_map, find_attachment, assets):
    chunk = COMMENT.sub("", chunk)

    def embed(m):
        name = m.group(1).split("|")[0].strip()
        suffix = Path(name).suffix.lower()
        if suffix == ".excalidraw":
            name = name + ".svg"
            src = find_attachment(name)
            if src is None:
                raise PublishError(f"{m.group(1)}: Excalidraw 그림을 같은 이름의 SVG로 내보내야 한다")
        elif suffix in IMAGE_EXTS:
            src = find_attachment(name)
            if src is None:
                raise PublishError(f"이미지를 찾을 수 없다: {name}")
        else:
            raise PublishError(f"노트 임베드는 발행할 수 없다: ![[{m.group(1)}]]")
        out = _bundle_name(name)
        assets.append((src, out))
        return f"![]({out})"

    def link(m):
        target, _, alias = m.group(1).partition("|")
        note, _, heading = target.partition("#")
        text = alias or note
        url = link_map.get(note.strip())
        if url is None:
            return text
        if heading:
            url += "#" + heading_anchor(heading)
        return f"[{text}]({url})"

    chunk = EMBED.sub(embed, chunk)
    return WIKILINK.sub(link, chunk)


def convert_body(body: str, link_map: dict, find_attachment) -> tuple[str, list]:
    assets, out, chunk, fence = [], [], [], None
    for line in body.split("\n"):
        m = FENCE.match(line)
        if fence is None and m:
            if chunk:
                out.append(_convert_chunk("\n".join(chunk), link_map, find_attachment, assets))
            chunk, fence = [], m.group(1)
            out.append(line)
        elif fence is not None:
            out.append(line)
            if m and m.group(1) == fence:
                fence = None
        else:
            chunk.append(line)
    if fence is None and chunk:
        out.append(_convert_chunk("\n".join(chunk), link_map, find_attachment, assets))
    return "\n".join(out), assets
