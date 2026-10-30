import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import publish  # noqa: E402
from publish import PublishError, check_safety, convert_body, load_denylist, parse_note, to_front_matter  # noqa: E402


def no_attachment(name):
    return None


class ParseNoteTest(unittest.TestCase):
    def test_parse_inline_and_block_lists(self):
        meta, _ = parse_note("---\ntags: [a, b]\n---\n본문")
        self.assertEqual(meta["tags"], ["a", "b"])
        meta, _ = parse_note("---\ntags:\n  - a\n  - b\n---\n본문")
        self.assertEqual(meta["tags"], ["a", "b"])

    def test_parse_scalars(self):
        meta, body = parse_note('---\npublish: true\nslug: my-post\ntitle: "따옴표: 제목"\nurl:\n---\n\n본문\n')
        self.assertIs(meta["publish"], True)
        self.assertEqual(meta["slug"], "my-post")
        self.assertEqual(meta["title"], "따옴표: 제목")
        self.assertEqual(body, "\n본문\n")

    def test_parse_skips_obsidian_only_keys(self):
        meta, _ = parse_note('---\ncategories:\n  - "[[Posts]]"\nauthor:\n  - "[[Me]]"\ntopics: []\nslug: a\n---\n')
        self.assertNotIn("categories", meta)
        self.assertNotIn("author", meta)
        self.assertEqual(meta["slug"], "a")

    def test_parse_rejects_nested_mapping(self):
        with self.assertRaises(PublishError):
            parse_note("---\nfoo:\n  bar: 1\n---\n")

    def test_note_without_front_matter(self):
        meta, body = parse_note("그냥 노트")
        self.assertEqual(meta, {})
        self.assertEqual(body, "그냥 노트")


class ConvertBodyTest(unittest.TestCase):
    def test_wikilink_to_published_note(self):
        out, _ = convert_body("앞 [[Other]] 뒤", {"Other": "/posts/other/"}, no_attachment)
        self.assertEqual(out, "앞 [Other](/posts/other/) 뒤")

    def test_wikilink_alias_to_unpublished_note(self):
        out, _ = convert_body("[[Private Note|여기]] 그리고 [[Private Note]]", {}, no_attachment)
        self.assertEqual(out, "여기 그리고 Private Note")

    def test_wikilink_heading_suffix(self):
        out, _ = convert_body("[[Other#섹션 이름|x]]", {"Other": "/posts/other/"}, no_attachment)
        self.assertEqual(out, "[x](/posts/other/#섹션-이름)")

    def test_image_embed_with_spaces_and_korean(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "Pasted image 2026 한글.png"
            src.write_bytes(b"png")
            out, assets = convert_body(
                "![[Pasted image 2026 한글.png]]", {}, lambda n: src if n == src.name else None
            )
        self.assertEqual(out, "![](Pasted-image-2026-한글.png)")
        self.assertEqual(assets, [(src, "Pasted-image-2026-한글.png")])

    def test_missing_image_aborts(self):
        with self.assertRaises(PublishError):
            convert_body("![[없는 그림.png]]", {}, no_attachment)

    def test_excalidraw_uses_exported_svg(self):
        with tempfile.TemporaryDirectory() as d:
            svg = Path(d) / "Drawing 1.excalidraw.svg"
            svg.write_text("<svg/>")
            find = lambda n: svg if n == svg.name else None  # noqa: E731
            out, assets = convert_body("![[Drawing 1.excalidraw]]", {}, find)
        self.assertEqual(out, "![](Drawing-1.excalidraw.svg)")
        self.assertEqual(assets, [(svg, "Drawing-1.excalidraw.svg")])

    def test_excalidraw_without_svg_aborts(self):
        with self.assertRaisesRegex(PublishError, "SVG로 내보내"):
            convert_body("![[Drawing 1.excalidraw]]", {}, no_attachment)

    def test_note_and_base_embeds_abort(self):
        with self.assertRaises(PublishError):
            convert_body("![[Some Note]]", {}, no_attachment)
        with self.assertRaises(PublishError):
            convert_body("![[Tasks.base#x]]", {}, no_attachment)

    def test_strips_obsidian_comments(self):
        out, _ = convert_body("앞 %% 비밀 %% 뒤", {}, no_attachment)
        self.assertEqual(out, "앞  뒤")
        out, _ = convert_body("가\n%%\n여러 줄\n비밀\n%%\n나", {}, no_attachment)
        self.assertEqual(out, "가\n\n나")

    def test_code_fence_untouched(self):
        src = "```md\n[[x]] %% y %% ![[z]]\n```\n~~~\n[[x]]\n~~~"
        out, _ = convert_body(src, {}, no_attachment)
        self.assertEqual(out, src)


class FrontMatterTest(unittest.TestCase):
    def test_front_matter_output(self):
        fm = to_front_matter({"kind": "설계", "published": "2026-11-09", "slug": "a"}, "파일이름")
        self.assertIn('title: "파일이름"', fm)
        self.assertIn("date: 2026-11-09", fm)
        self.assertIn('kind: "설계"', fm)
        self.assertIn("generated: obsidian", fm)
        self.assertNotIn("slug", fm)
        self.assertTrue(fm.startswith("---\n") and fm.endswith("---\n"))

    def test_front_matter_lists_and_quotes(self):
        fm = to_front_matter({"title": '그가 "왜"라고', "tags": ["쿠버네티스", "kind"], "published": "2026-11-09"}, "x")
        self.assertIn('title: "그가 \\"왜\\"라고"', fm)
        self.assertIn('tags: ["쿠버네티스", "kind"]', fm)


class SafetyTest(unittest.TestCase):
    def problems(self, text, deny=(), allowed=("me@example.com",)):
        return check_safety(text, list(deny), set(allowed))

    def test_safety_email_allowlist(self):
        self.assertEqual(self.problems("연락: me@example.com"), [])
        self.assertEqual(len(self.problems("연락: other@corp.co.kr")), 1)

    def test_safety_phone(self):
        self.assertEqual(len(self.problems("전화 010-1234-5678")), 1)
        self.assertEqual(len(self.problems("전화 01012345678")), 1)

    def test_safety_local_paths(self):
        self.assertEqual(len(self.problems("경로 /Users/someone/x")), 1)
        self.assertEqual(len(self.problems("경로 ~/orca/x")), 1)

    def test_safety_private_ip(self):
        for ip in ("192.168.0.10", "10.0.0.5", "172.16.3.4"):
            self.assertEqual(len(self.problems(f"주소 {ip}")), 1, ip)
        for ip in ("172.32.0.1", "8.8.8.8"):
            self.assertEqual(self.problems(f"주소 {ip}"), [], ip)

    def test_safety_tokens(self):
        samples = [
            "sk-" + "a" * 24,
            "ghp_" + "A1" * 18,
            "github_pat_11ABCDEFG0123456789_abcdef",
            "AKIA" + "ABCDEFGHIJKLMNOP",
            "xoxb-123456-abcdef",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
        ]
        for s in samples:
            self.assertEqual(len(self.problems(f"값 {s}")), 1, s)

    def test_safety_denylist_case_insensitive(self):
        self.assertEqual(len(self.problems("우리 foo corp 이야기", deny=["Foo Corp"])), 1)

    def test_safety_scans_code_blocks(self):
        self.assertEqual(len(self.problems("```console\n$ ls /Users/x/\n```")), 1)

    def test_safety_reports_line_numbers(self):
        p = self.problems("첫 줄\n둘째 줄\n셋째 줄 010-1234-5678")
        self.assertIn("줄 3", p[0])

    def test_load_denylist(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_denylist(Path(d)), [])
            (Path(d) / ".publish-denylist").write_text("# 주석\n\nFoo Corp\n  bar  \n")
            self.assertEqual(load_denylist(Path(d)), ["Foo Corp", "bar"])


def note(slug="hello", publish="true", kind="설계", extra="", body="본문입니다."):
    return (
        f"---\npublish: {publish}\nslug: {slug}\npublished: 2026-11-09\nkind: {kind}\n{extra}---\n{body}\n"
    )


class SyncTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.vault = root / "vault"
        self.content = root / "content"
        self.vault.mkdir()
        (self.content / "posts").mkdir(parents=True)
        self.allowed = {"me@example.com"}

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = self.vault / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def plan(self):
        return publish.plan_actions(self.vault, self.content, self.allowed)

    def kinds(self):
        return sorted((a.kind, a.slug) for a in self.plan())

    def run_write(self):
        publish.apply_actions(self.plan())

    def test_only_publish_true_notes(self):
        self.write("a.md", note(slug="a", publish="false"))
        self.write("b.md", "---\ntitle: x\n---\n본문")
        self.write("c.md", note(slug="c"))
        self.assertEqual(self.kinds(), [("create", "c")])

    def test_skips_templates_and_hidden(self):
        self.write("Templates/Post Template.md", note(slug="tpl"))
        self.write(".trash/old.md", note(slug="old"))
        self.assertEqual(self.kinds(), [])

    def test_create_then_same(self):
        self.write("Hello.md", note())
        self.assertEqual(self.kinds(), [("create", "hello")])
        self.run_write()
        index = (self.content / "posts" / "hello" / "index.md").read_text(encoding="utf-8")
        self.assertIn('title: "Hello"', index)
        self.assertIn("본문입니다.", index)
        self.assertEqual(self.kinds(), [("same", "hello")])

    def test_update_when_note_changes(self):
        self.write("Hello.md", note())
        self.run_write()
        self.write("Hello.md", note(body="고친 본문"))
        self.assertEqual(self.kinds(), [("update", "hello")])

    def test_unpublish_deletes_generated_bundle(self):
        self.write("Hello.md", note())
        self.run_write()
        self.write("Hello.md", note(publish="false"))
        self.assertEqual(self.kinds(), [("delete", "hello")])
        self.run_write()
        self.assertFalse((self.content / "posts" / "hello").exists())

    def test_refuses_to_overwrite_handwritten_bundle(self):
        hand = self.content / "posts" / "hello"
        hand.mkdir()
        (hand / "index.md").write_text("---\ntitle: 손으로\n---\n", encoding="utf-8")
        self.write("Hello.md", note())
        self.assertEqual(self.kinds(), [("abort", "hello")])
        self.run_write()
        self.assertIn("손으로", (hand / "index.md").read_text(encoding="utf-8"))

    def test_never_deletes_handwritten_bundle(self):
        hand = self.content / "posts" / "mine"
        hand.mkdir()
        (hand / "index.md").write_text("---\ntitle: 손으로\n---\n", encoding="utf-8")
        self.assertEqual(self.kinds(), [])

    def test_duplicate_slug_aborts_both(self):
        self.write("One.md", note(slug="same"))
        self.write("Two.md", note(slug="same"))
        actions = self.plan()
        self.assertEqual([a.kind for a in actions], ["abort", "abort"])
        self.assertIn("One.md", actions[0].detail + actions[1].detail)
        self.assertIn("Two.md", actions[0].detail + actions[1].detail)

    def test_missing_required_fields_abort(self):
        self.write("a.md", note(slug="Bad Slug"))
        self.write("b.md", note(slug="b", kind="잡담"))
        self.write("c.md", note(slug="c", extra="section: notes\nbook_author: 저자\n"))
        self.write("d.md", "---\npublish: true\nslug: d\nkind: 설계\n---\n본문")
        self.assertEqual([a.kind for a in self.plan()], ["abort"] * 4)

    def test_notes_section(self):
        self.write("Book.md", note(slug="book", kind="", extra="section: notes\nbook: 책\nbook_author: 저자\n"))
        self.assertEqual(self.kinds(), [("create", "book")])
        self.run_write()
        self.assertTrue((self.content / "notes" / "book" / "index.md").exists())

    def test_safety_failure_aborts_without_writing(self):
        self.write("Hello.md", note(body="연락 other@corp.com"))
        self.assertEqual(self.kinds(), [("abort", "hello")])
        self.run_write()
        self.assertFalse((self.content / "posts" / "hello").exists())

    def test_aborted_note_keeps_previous_bundle(self):
        self.write("Hello.md", note())
        self.run_write()
        self.write("Hello.md", note(body="연락 other@corp.com"))
        self.assertEqual(self.kinds(), [("abort", "hello")])
        self.run_write()
        self.assertTrue((self.content / "posts" / "hello" / "index.md").exists())

    def test_invalid_section_keeps_previous_bundle(self):
        self.write("Hello.md", note())
        self.run_write()
        self.write("Hello.md", note(extra="section: post\n"))
        self.assertEqual(self.kinds(), [("abort", "hello")])

    def test_broken_front_matter_blocks_deletions(self):
        self.write("Hello.md", note())
        self.run_write()
        self.write("Hello.md", "---\npublish: true\nslug: hello\nfoo:\n  bar: 1\n---\n본문")
        kinds = [a.kind for a in self.plan()]
        self.assertNotIn("delete", kinds)
        self.assertIn("abort", kinds)

    def test_links_between_published_notes(self):
        self.write("First.md", note(slug="first", body="[[Second]] 참고, [[Secret]]"))
        self.write("Second.md", note(slug="second"))
        self.run_write()
        index = (self.content / "posts" / "first" / "index.md").read_text(encoding="utf-8")
        self.assertIn("[Second](/posts/second/) 참고, Secret", index)

    def test_images_copied_into_bundle(self):
        (self.vault / "Attachments").mkdir()
        (self.vault / "Attachments" / "그림 1.png").write_bytes(b"png")
        self.write("Hello.md", note(body="![[그림 1.png]]"))
        self.run_write()
        self.assertEqual((self.content / "posts" / "hello" / "그림-1.png").read_bytes(), b"png")

    def test_fence_without_language_warns(self):
        self.write("Hello.md", note(body="```\ncode\n```"))
        action = self.plan()[0]
        self.assertEqual(action.kind, "create")
        self.assertIn("언어", action.detail)

    def test_dry_run_writes_nothing(self):
        self.write("Hello.md", note())
        code = publish.main(["--vault", str(self.vault), "--content", str(self.content)])
        self.assertEqual(code, 0)
        self.assertEqual(list((self.content / "posts").iterdir()), [])

    def test_main_returns_1_on_abort(self):
        self.write("Hello.md", note(kind="잡담"))
        code = publish.main(["--vault", str(self.vault), "--content", str(self.content), "--write"])
        self.assertEqual(code, 1)

    def test_read_allowed_email(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "hugo.toml").write_text('[params]\n  email = "me@example.com"\n')
            self.assertEqual(publish.allowed_emails(Path(d) / "hugo.toml"), {"me@example.com"})


if __name__ == "__main__":
    unittest.main()
