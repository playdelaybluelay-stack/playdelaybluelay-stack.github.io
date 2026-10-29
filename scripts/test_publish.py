import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import publish  # noqa: E402
from publish import PublishError, convert_body, parse_note, to_front_matter  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
