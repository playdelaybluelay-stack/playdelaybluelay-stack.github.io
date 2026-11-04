"""Obsidian 노트 중 `publish: true`인 것만 Hugo page bundle로 옮긴다.

python3 scripts/publish.py           미리보기
python3 scripts/publish.py --write   파일 쓰기
"""
import argparse
import html
import json
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, namedtuple
from pathlib import Path
from urllib.parse import unquote


class PublishError(Exception):
    pass


ALLOWED_KINDS = ("설계", "트러블슈팅", "회고", "개념")
OBSIDIAN_ONLY = {"categories", "author", "topics", "status", "created", "url", "language"}
OUTPUT_KEYS = ("title", "date", "description", "category", "tags", "project", "milestone", "book", "book_author")
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
    values["category"] = meta.get("kind")  # Hugo에서 kind는 예약어라 이름을 바꿔 쓴다
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
    ("전화번호", re.compile(r"\b01[016789][-. ]?\d{3,4}[-. ]?\d{4}\b")),
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


def _visible(s):
    """전각 문자를 반각으로 바꾸고 보이지 않는 문자(제로폭 공백 등)를 뺀다."""
    s = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Cf")


def _squash(s):
    """차단어 비교용: 대소문자와 공백(줄바꿈 포함)을 무시한다."""
    return "".join(ch for ch in _visible(s).casefold() if not ch.isspace())


def check_safety(text: str, denylist: list[str], allowed_emails: set[str]) -> list[str]:
    problems = []
    lines = text.split("\n")
    # 렌더링하면 같은 글자가 되는 표기(전각, %40, &#64;)도 본다
    variants = [[_visible(line) for line in lines]]
    variants.append([_visible(html.unescape(unquote(line))) for line in variants[0]])
    for n in range(len(lines)):
        found = []
        for kind, pattern in SAFETY_PATTERNS:
            for line in dict.fromkeys(v[n] for v in variants):
                for m in pattern.finditer(line):
                    if (kind == "이메일" and m.group(0) in allowed_emails) or (kind, m.group(0)) in found:
                        continue
                    found.append((kind, m.group(0)))
                    problems.append(f"줄 {n + 1}: {kind} ({m.group(0)[:6]}…)")
    # 차단어는 줄을 이어 붙여 본다. Markdown은 줄바꿈 하나를 공백으로 렌더링한다
    for variant in variants:
        joined, line_of = [], []
        for n, line in enumerate(variant, 1):
            squashed = _squash(line)
            joined.append(squashed)
            line_of += [n] * len(squashed)
        joined = "".join(joined)
        for word in denylist:
            key, start = _squash(word), 0
            while key and (i := joined.find(key, start)) != -1:
                problem = f"줄 {line_of[i]}: 차단어 ({word})"
                if problem not in problems:
                    problems.append(problem)
                start = i + 1
    return problems


def svg_text(data: bytes) -> str:
    """SVG에서 화면에 글자로 보이는 부분만 꺼낸다. 폰트 데이터나 Excalidraw 원본은 뺀다."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise PublishError(f"SVG를 읽을 수 없다: {e}")
    texts = ("text", "title", "desc")
    return "\n".join("".join(el.itertext()) for el in root.iter() if el.tag.rpartition("}")[2] in texts)


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


# ---- sync ----

Action = namedtuple("Action", "kind slug detail bundle files")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKIP_DIRS = {"Templates"}
LABELS = {"create": "생성", "update": "변경", "same": "그대로", "delete": "삭제", "abort": "중단"}
DEFAULT_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/real-world"
SITE = Path(__file__).resolve().parent.parent


def allowed_emails(hugo_toml: Path) -> set[str]:
    m = re.search(r'^\s*email\s*=\s*"([^"]+)"', hugo_toml.read_text(encoding="utf-8"), re.M)
    return {m.group(1)} if m else set()


def _vault_files(vault):
    for path in sorted(vault.rglob("*")):
        rel = path.relative_to(vault).parts
        if path.is_file() and not any(p.startswith(".") or p in SKIP_DIRS for p in rel):
            yield path


def _validate(meta):
    section = meta.get("section") or "posts"
    errors = []
    if section not in ("posts", "notes"):
        errors.append(f"section은 posts나 notes여야 한다: {section}")
    if not SLUG.match(str(meta.get("slug") or "")):
        errors.append("slug는 영문 소문자, 숫자, 하이픈만 쓴다")
    if not meta.get("published"):
        errors.append("published(발행일)가 없다")
    if section == "posts" and meta.get("kind") not in ALLOWED_KINDS:
        errors.append(f"kind는 {', '.join(ALLOWED_KINDS)} 중 하나여야 한다")
    if section == "notes" and not (meta.get("book") and meta.get("book_author")):
        errors.append("notes에는 book과 book_author가 필요하다")
    return section, errors


def _is_generated(bundle):
    index = bundle / "index.md"
    return index.exists() and "\ngenerated: obsidian\n" in index.read_text(encoding="utf-8")


def _bare_fences(body):
    count, inside = 0, False
    for line in body.split("\n"):
        if FENCE.match(line):
            if not inside and line.strip() in ("```", "~~~"):
                count += 1
            inside = not inside
    return count


def plan_actions(vault: Path, content_dir: Path, allowed: set[str]) -> list:
    denylist = load_denylist(vault)
    files = list(_vault_files(vault))
    by_name = {}
    for f in files:
        by_name.setdefault(f.name, f)

    notes, actions = [], []
    for path in files:
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"^publish:\s*true\s*$", text, re.M):
            continue
        try:
            meta, body = parse_note(text)
        except PublishError as e:
            actions.append(Action("abort", path.stem, f"{path.name}: {e}", None, None))
            continue
        if meta.get("publish") is not True:
            continue
        section, errors = _validate(meta)
        notes.append(dict(path=path, text=text, meta=meta, body=body, section=section,
                          slug=str(meta.get("slug") or path.stem), errors=errors))

    # 발행 대상이었던 노트의 slug는 섹션과 상관없이 지우지 않는다. front matter가 깨진 노트가 있으면 아무것도 지우지 않는다.
    seen = {n["slug"] for n in notes}
    unparsed = any(a.kind == "abort" for a in actions)
    counts = Counter(n["slug"] for n in notes)
    for n in notes:
        if counts[n["slug"]] > 1:
            others = ", ".join(m["path"].name for m in notes if m["slug"] == n["slug"])
            n["errors"].append(f"slug가 겹친다: {others}")
    link_map = {n["path"].stem: f"/{n['section']}/{n['slug']}/" for n in notes if not n["errors"]}

    for n in notes:
        bundle = content_dir / n["section"] / n["slug"]
        errors = list(n["errors"]) + check_safety(n["text"], denylist, allowed)
        if bundle.exists() and not _is_generated(bundle):
            errors.append("같은 이름의 번들을 사람이 직접 썼다. 덮어쓰지 않는다")
        out_files = {}
        if not errors:
            try:
                body, assets = convert_body(n["body"], link_map, by_name.get)
            except PublishError as e:
                errors.append(str(e))
            else:
                index = to_front_matter(n["meta"], n["path"].stem) + "\n" + body
                out_files["index.md"] = index.encode("utf-8")
                # 파일 이름에서 온 제목, JSON 이스케이프를 푼 front matter 값처럼 원문에 없던 글자를 본다
                errors += [f"발행본 {p}" for p in check_safety(index, denylist, allowed)]
                for src, name in assets:
                    out_files[name] = src.read_bytes()
                    if name.lower().endswith(".svg"):
                        try:
                            errors += [f"{name} {p}" for p in check_safety(svg_text(out_files[name]), denylist, allowed)]
                        except PublishError as e:
                            errors.append(str(e))
        if errors:
            actions.append(Action("abort", n["slug"], f"{n['path'].name}: " + "; ".join(errors), None, None))
            continue
        warn = _bare_fences(n["body"])
        detail = f"{n['path'].name}" + (f" (경고: 언어 이름이 없는 코드 펜스 {warn}개)" if warn else "")
        if not bundle.exists():
            kind = "create"
        else:
            current = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
            kind = "same" if current == out_files else "update"
        actions.append(Action(kind, n["slug"], detail, bundle, out_files))

    for section in ("posts", "notes"):
        base = content_dir / section
        if not base.is_dir():
            continue
        for bundle in sorted(base.iterdir()):
            if bundle.is_dir() and not unparsed and bundle.name not in seen and _is_generated(bundle):
                actions.append(Action("delete", bundle.name, f"{section}/{bundle.name}", bundle, None))
    return actions


def apply_actions(actions: list) -> None:
    for a in actions:
        if a.kind in ("create", "update"):
            if a.bundle.exists():
                shutil.rmtree(a.bundle)
            a.bundle.mkdir(parents=True)
            for name, data in a.files.items():
                (a.bundle / name).write_bytes(data)
        elif a.kind == "delete":
            shutil.rmtree(a.bundle)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Obsidian 노트를 Hugo 글로 옮긴다. 기본은 미리보기.")
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--content", type=Path, default=SITE / "content")
    ap.add_argument("--write", action="store_true", help="파일을 실제로 쓴다")
    args = ap.parse_args(argv)

    if not load_denylist(args.vault):
        print(f"경고: {args.vault / '.publish-denylist'} 이 없거나 비어 있다", file=sys.stderr)
    hugo_toml = SITE / "hugo.toml"
    allowed = allowed_emails(hugo_toml) if hugo_toml.exists() else set()
    actions = plan_actions(args.vault, args.content, allowed)
    if not actions:
        print("발행할 노트 없음")
    for a in actions:
        print(f"{LABELS[a.kind]}\t{a.slug}\t{a.detail}")
    if args.write:
        apply_actions(a for a in actions if a.kind != "abort")
    elif any(a.kind in ("create", "update", "delete") for a in actions):
        print("미리보기다. 반영하려면 --write를 붙인다.")
    return 1 if any(a.kind == "abort" for a in actions) else 0


if __name__ == "__main__":
    sys.exit(main())
