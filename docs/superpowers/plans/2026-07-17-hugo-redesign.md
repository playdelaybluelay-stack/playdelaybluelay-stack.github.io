# Hugo 리디자인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jekyll 블로그를 Hugo로 이전하고 docs/superpowers/specs/2026-07-15-blog-redesign-design.md의 확정 디자인을 구현한다.

**Architecture:** 테마 임포트 없이 layouts/를 직접 작성하는 자작 Hugo 사이트. CSS는 토큰(CSS 변수) 한 파일, JS는 테마 토글(인라인)과 목차/복사 두 파일. GitHub Actions로 gh-pages 빌드 배포. 기존 글 URL은 front matter `url`로 그대로 유지.

**Tech Stack:** Hugo extended(최신 안정판), Goldmark + Chroma(noClasses=false), GitHub Actions(actions/deploy-pages), fonttools(woff2 서브셋)

## Global Constraints

스펙(docs/superpowers/specs/2026-07-15-blog-redesign-design.md)이 정본. 아래는 전 태스크 공통 규칙이다.

- 가운뎃점(·)을 어떤 산출물에도 쓰지 않는다. 구분은 줄바꿈, 한 줄 안에서는 쉼표.
- 같은 정보를 두 번 보여주지 않는다.
- 모노스페이스(D2Coding)는 코드에만. 날짜와 메타는 본문 서체.
- 영어는 굳어진 자리에만: about, series, EN, bash 등 소문자.
- 색 토큰(정확히 이 값): 바탕 `#fcfdfc`/`#101413`, 본문 `#1c211f`/`#e3e9e6`, 보조 `#5e6a65`/`#93a09b`, 메타 `#6b7770`/`#7f8a85`, 구분선 `#e4eae7`/`#252c29`, 액센트 `#0e7568`/`#52c4b0`, 노선도 현재 역 `#0e7568`/`#d9ad5c`, 코드 배경 `#f3f6f5`/`#0b100f`, 라이트 코드 주석 `#5d6c66` 이상 어둡게.
- 본문 폭 42rem, 본문 16px 행간 1.85, `word-break: keep-all`.
- 모든 텍스트 대비 WCAG AA 4.5:1 이상. 본문 링크는 밑줄 유지.
- 모든 전환 효과는 `prefers-reduced-motion: reduce`에서 꺼진다.
- 인터랙티브 요소: 포커스 스타일 2px 액센트 아웃라인 offset 2px, 히트 영역 44px 이상(헤더 내비, 테마 토글, summary, 복사 버튼).
- 기존 글 URL `/network/2026/01/14/network-1-ip-subnetting.html` 그대로 유지.
- 커밋 메시지는 기존 저장소 스타일: `feat:`, `chore:`, `docs:` 접두 + 한국어 요약.
- v1 범위 제외: 검색, 댓글, 조회수, 인터랙티브 다이어그램, 긴 연재 접힘 노선도, KaTeX/Mermaid, 관련 글, 공유 버튼.

---

## 파일 구조

```
hugo.toml                              # 사이트 설정
content/
  posts/network-1-ip-subnetting.md     # 이전된 글 (url로 기존 경로 유지)
  about.md                             # 소개
  series.md                            # 연재 인덱스 (layout: series)
layouts/
  _default/baseof.html                 # 뼈대: head, 헤더, 푸터, 스킵 링크
  _default/single.html                 # 글 페이지
  _default/list.html                   # (미사용 폴백, 홈은 index.html)
  _default/series.html                 # 연재 인덱스
  _default/_markup/render-heading.html # h2 앵커 링크
  _default/_markup/render-codeblock.html # 코드블록: 언어 라벨 + 복사 버튼
  index.html                           # 홈
  404.html
  partials/head.html                   # meta, OG, hreflang, FOUC 스크립트, CSS
  partials/header.html                 # 워드마크, series, about, EN, 테마 토글
  partials/footer.html                 # 저작권, GitHub, RSS
  partials/toc-linemap.html            # 노선도 목차
  shortcodes/callout.html              # 참고 박스
assets/css/main.css                    # 토큰 + 전체 스타일 (한 파일)
assets/js/toc.js                       # IntersectionObserver 목차 추적
assets/js/copy.js                      # 코드 복사 버튼
static/fonts/*.woff2                   # 서브셋 서체
static/og-default.png                  # 기본 OG 이미지
static/favicon.svg                     # 이니셜 SVG (기존 것 재사용)
i18n/ko.yaml, i18n/en.yaml             # UI 문자열
.github/workflows/hugo.yml             # 빌드 배포
docs/font-prototype/index.html         # Task 2 검증용 (배포 제외)
```

책임 분리: `main.css`가 유일한 스타일 원천(토큰 → 컴포넌트 순서), 템플릿은 구조만, JS 두 파일은 각각 목차와 복사만 담당한다.

---

### Task 1: 브랜치와 Hugo 스캐폴드

**Files:**
- Create: `hugo.toml`
- Create: `content/.gitkeep`, `layouts/.gitkeep`, `assets/css/.gitkeep`, `i18n/.gitkeep`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `hugo.toml`의 설정 키 — `params.github`, `params.author = "한예빈"`, taxonomy `tags`. 이후 모든 태스크가 이 설정을 전제한다.

- [ ] **Step 1: 작업 브랜치 생성**

```bash
git checkout -b hugo-redesign
```

- [ ] **Step 2: Hugo 설치 확인**

Run: `hugo version`
Expected: `hugo v0.1xx.x+extended` 출력. 없으면 `brew install hugo`.

- [ ] **Step 3: hugo.toml 작성**

```toml
baseURL = "https://playdelaybluelay-stack.github.io/"
title = "한예빈"
languageCode = "ko"
defaultContentLanguage = "ko"
hasCJKLanguage = true
enableRobotsTXT = true

[languages]
  [languages.ko]
    languageName = "한국어"
    weight = 1
  [languages.en]
    languageName = "English"
    weight = 2
    disabled = true # 영문 글이 생기면 false로

[taxonomies]
  tag = "tags"

[params]
  author = "한예빈"
  bio = "클라우드와 네트워크를 공부합니다."
  github = "https://github.com/playdelaybluelay-stack"

[markup.highlight]
  noClasses = false
  codeFences = true

[markup.goldmark.parser.attribute]
  title = true

[outputs]
  home = ["HTML", "RSS"]
```

- [ ] **Step 4: .gitignore에 Hugo 산출물 추가**

`.gitignore` 끝에 추가:

```
public/
resources/
.hugo_build.lock
```

- [ ] **Step 5: 빌드가 도는지 확인**

```bash
mkdir -p content layouts assets/css i18n
hugo --logLevel info
```

Expected: 에러 없이 종료(레이아웃이 없어 WARN은 허용). `public/` 생성 확인.

- [ ] **Step 6: 커밋**

```bash
git add hugo.toml .gitignore
git commit -m "feat: Hugo 스캐폴드와 사이트 설정"
```

---

### Task 2: 서체 파이프라인과 실물 프로토타입 (스펙의 구현 1단계 게이트)

**Files:**
- Create: `static/fonts/Paperlogy-7Bold.woff2`, `static/fonts/KoPubWorldDotum-Regular.woff2`, `static/fonts/KoPubWorldDotum-Bold.woff2`, `static/fonts/D2Coding.woff2`
- Create: `docs/font-prototype/index.html`

**Interfaces:**
- Produces: `@font-face` 패밀리명 — `"Paperlogy"`(700), `"KoPubWorld Dotum"`(400, 700), `"D2Coding"`(400). Task 3의 main.css가 이 이름을 그대로 쓴다.

- [ ] **Step 1: 원본 서체 확보**

```bash
mkdir -p /tmp/fonts-src static/fonts
# D2Coding: GitHub 릴리스에서 자동 획득
curl -L -o /tmp/fonts-src/d2coding.zip \
  https://github.com/naver/d2codingfont/releases/download/VER1.3.2/D2Coding-Ver1.3.2-20180524.zip
unzip -o /tmp/fonts-src/d2coding.zip -d /tmp/fonts-src/d2coding
find /tmp/fonts-src/d2coding -name "D2Coding-Ver*.ttf" ! -name "*Bold*" ! -name "*ligature*" -exec cp {} /tmp/fonts-src/D2Coding.ttf \;
```

Paperlogy와 KoPubWorld 돋움은 라이선스 동의가 필요한 공식 배포처(각각 프리젠테이션/Paperlogy 공식 페이지, KoPubWorld는 한국출판인회의)에서 받아야 한다. TTF를 자동으로 받을 수 없으면 **여기서 멈추고 사용자에게 파일을 요청하라**: `/tmp/fonts-src/Paperlogy-7Bold.ttf`, `/tmp/fonts-src/KoPubWorld-Dotum-Md.ttf`(400 대용 Medium), `/tmp/fonts-src/KoPubWorld-Dotum-Bd.ttf`.

- [ ] **Step 2: woff2 서브셋 생성**

```bash
python3 -m pip install --quiet fonttools brotli
RANGES="U+0020-007E,U+00A0-00FF,U+2010-2030,U+AC00-D7A3,U+1100-11FF,U+3130-318F"
for f in Paperlogy-7Bold KoPubWorld-Dotum-Md KoPubWorld-Dotum-Bd D2Coding; do
  python3 -m fontTools.subset "/tmp/fonts-src/$f.ttf" \
    --flavor=woff2 --unicodes="$RANGES" \
    --layout-features='*' --output-file="static/fonts/$f.woff2"
done
mv static/fonts/KoPubWorld-Dotum-Md.woff2 static/fonts/KoPubWorldDotum-Regular.woff2
mv static/fonts/KoPubWorld-Dotum-Bd.woff2 static/fonts/KoPubWorldDotum-Bold.woff2
ls -la static/fonts/
```

Expected: woff2 4개, 각 1.5MB 이하. (KS X 1001 정밀 서브셋 최적화는 v1 이후 — 현대 한글 전체 범위로 시작한다.)

- [ ] **Step 3: 프로토타입 페이지 작성**

`docs/font-prototype/index.html` (독립 파일, 배포와 무관):

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>서체 검증</title>
<style>
@font-face{font-family:Paperlogy;src:url(../../static/fonts/Paperlogy-7Bold.woff2) format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:"KoPubWorld Dotum";src:url(../../static/fonts/KoPubWorldDotum-Regular.woff2) format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"KoPubWorld Dotum";src:url(../../static/fonts/KoPubWorldDotum-Bold.woff2) format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:D2Coding;src:url(../../static/fonts/D2Coding.woff2) format("woff2");font-weight:400;font-display:swap}
body{font-family:"KoPubWorld Dotum","Apple SD Gothic Neo",sans-serif;font-size:16px;line-height:1.85;word-break:keep-all;max-width:42rem;margin:40px auto;padding:0 20px}
h1{font-family:Paperlogy;font-size:28px;font-weight:700}
h2{font-family:Paperlogy;font-size:21px;font-weight:700}
code{font-family:D2Coding;font-size:13.5px;background:#f3f6f5;padding:1px 5px;border:1px solid #e4eae7;border-radius:4px}
</style></head><body>
<h1>IP 주소 체계와 서브네팅</h1>
<p>OSI 7계층과 TCP/IP 4계층은 통신 과정을 역할별로 나눈 모델이다. NAT 뒤의 사설망에서 <b>강조 텍스트</b>와 날짜 2026년 1월 14일, 그리고 <code>ipcalc 192.168.1.0/26</code> 같은 인라인 코드가 섞인다.</p>
<h2>라틴 혼용 확인</h2>
<p>TCP, DynamoDB, GitHub Actions, Terraform 같은 영문이 본문에 상시 섞일 때의 인상을 본다. 0123456789.</p>
</body></html>
```

- [ ] **Step 4: 검증 게이트 (사용자 체크포인트 — 건너뛰지 말 것)**

브라우저로 `docs/font-prototype/index.html`을 열어 확인을 요청한다. 확인 항목(스펙 명시): KoPubWorld 돋움의 400/700 대비, 라틴 글리프 품질(TCP, 날짜 숫자), 가능하면 Windows 실기기 렌더링. **사용자가 탈락 판정하면 본문을 Wanted Sans로, 제목을 경기천년제목으로 교체하고 이 태스크를 다시 돈다.**

- [ ] **Step 5: 커밋**

```bash
git add static/fonts docs/font-prototype
git commit -m "feat: 서체 셀프호스팅 파이프라인과 검증 프로토타입"
```

---

### Task 3: 디자인 토큰 CSS와 베이스 템플릿

**Files:**
- Create: `assets/css/main.css`
- Create: `layouts/_default/baseof.html`
- Create: `layouts/partials/head.html`
- Create: `layouts/partials/header.html`
- Create: `layouts/partials/footer.html`
- Create: `i18n/ko.yaml`, `i18n/en.yaml`

**Interfaces:**
- Consumes: Task 2의 @font-face 패밀리명.
- Produces: CSS 클래스 — `.wrap`(콘텐츠 폭), `.post-list`, `.post-item`, `.hero`, `.linemap`, `.callout`, `.foot-nav`, `.skip-link`. 토큰 변수 — `--bg --text --text-2 --text-3 --border --accent --station --code-bg --surface`. partial 이름 — `head.html`, `header.html`, `footer.html`. 이후 모든 태스크가 이것을 쓴다.

- [ ] **Step 1: i18n 문자열 파일**

`i18n/ko.yaml`:

```yaml
themeToggleToDark: "어두운 화면으로 전환"
themeToggleToLight: "밝은 화면으로 전환"
skipToContent: "본문 바로가기"
toEnglish: "영어판으로 보기"
toc: "목차"
copyCode: "코드 복사"
copied: "복사됨"
```

`i18n/en.yaml`:

```yaml
themeToggleToDark: "Switch to dark mode"
themeToggleToLight: "Switch to light mode"
skipToContent: "Skip to content"
toEnglish: "Read in English"
toc: "Table of contents"
copyCode: "Copy code"
copied: "Copied"
```

- [ ] **Step 2: main.css 작성 (토큰 → 베이스 → 컴포넌트 순)**

`assets/css/main.css` — 같은 경로에 Jekyll의 옛 main.css가 있으므로 **통째로 이 내용으로 교체**한다:

```css
/* ---- 서체 ---- */
@font-face{font-family:Paperlogy;src:url(/fonts/Paperlogy-7Bold.woff2) format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:"KoPubWorld Dotum";src:url(/fonts/KoPubWorldDotum-Regular.woff2) format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"KoPubWorld Dotum";src:url(/fonts/KoPubWorldDotum-Bold.woff2) format("woff2");font-weight:700;font-display:swap}
@font-face{font-family:D2Coding;src:url(/fonts/D2Coding.woff2) format("woff2");font-weight:400;font-display:swap}

/* ---- 토큰 ---- */
:root{
  --bg:#fcfdfc; --text:#1c211f; --text-2:#5e6a65; --text-3:#6b7770;
  --border:#e4eae7; --surface:#f2f5f4;
  --accent:#0e7568; --station:#0e7568;
  --code-bg:#f3f6f5; --code-text:#2b3431; --code-comment:#5d6c66; --code-keyword:#0c6a5e;
  --code-string:#8a5a2b; --hl-line:rgba(14,117,104,0.08);
  --sans:"KoPubWorld Dotum","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
  --display:Paperlogy,var(--sans);
  --mono:D2Coding,ui-monospace,Menlo,monospace;
  --header-h:57px;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#101413; --text:#e3e9e6; --text-2:#93a09b; --text-3:#7f8a85;
  --border:#252c29; --surface:#181d1b;
  --accent:#52c4b0; --station:#d9ad5c;
  --code-bg:#0b100f; --code-text:#bcd4cc; --code-comment:#6d938a; --code-keyword:#7fd8c9;
  --code-string:#d9b98a; --hl-line:rgba(82,196,176,0.10);
}}
:root[data-theme=light]{
  --bg:#fcfdfc; --text:#1c211f; --text-2:#5e6a65; --text-3:#6b7770;
  --border:#e4eae7; --surface:#f2f5f4;
  --accent:#0e7568; --station:#0e7568;
  --code-bg:#f3f6f5; --code-text:#2b3431; --code-comment:#5d6c66; --code-keyword:#0c6a5e;
  --code-string:#8a5a2b; --hl-line:rgba(14,117,104,0.08);
}
:root[data-theme=dark]{
  --bg:#101413; --text:#e3e9e6; --text-2:#93a09b; --text-3:#7f8a85;
  --border:#252c29; --surface:#181d1b;
  --accent:#52c4b0; --station:#d9ad5c;
  --code-bg:#0b100f; --code-text:#bcd4cc; --code-comment:#6d938a; --code-keyword:#7fd8c9;
  --code-string:#d9b98a; --hl-line:rgba(82,196,176,0.10);
}

/* ---- 베이스 ---- */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg)}
body{font-family:var(--sans);font-size:16px;line-height:1.85;color:var(--text);
  background:var(--bg);word-break:keep-all}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;animation:none!important}}
.wrap{max-width:42rem;margin:0 auto;padding:0 20px}
.skip-link{position:absolute;left:-9999px;top:0;background:var(--accent);color:var(--bg);
  padding:10px 16px;z-index:200}
.skip-link:focus{left:0}

/* ---- 헤더 ---- */
.site-header{position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border);
  background:color-mix(in srgb,var(--bg) 85%,transparent);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.site-header .wrap{display:flex;align-items:center;justify-content:space-between;min-height:var(--header-h)}
.wordmark{font-weight:700;font-size:16px;text-decoration:none}
.home .wordmark{opacity:0;pointer-events:none;transition:opacity .2s}
.home.scrolled .wordmark{opacity:1;pointer-events:auto}
.site-nav{display:flex;align-items:center;gap:4px}
.site-nav a,.site-nav button{display:inline-flex;align-items:center;justify-content:center;
  min-height:44px;min-width:44px;padding:0 10px;font-size:14px;color:var(--text-2);
  text-decoration:none;background:none;border:none;cursor:pointer;font-family:inherit}
.site-nav a:hover,.site-nav button:hover{color:var(--text)}
.lang-switch{border:1px solid var(--border);border-radius:6px;font-size:12px}
.theme-toggle svg{display:block}

/* ---- 홈 ---- */
.hero{padding:56px 0 0}
.hero h1{font-family:var(--display);font-size:24px;font-weight:700;letter-spacing:-.02em}
.hero p{margin-top:10px;color:var(--text-2)}
.hero a{color:var(--accent);text-decoration:underline;text-underline-offset:3px}
.post-list{list-style:none;padding:88px 0 96px}
.post-item{margin-bottom:40px}
.post-item h2{font-family:var(--display);font-size:17px;font-weight:700;line-height:1.5;letter-spacing:-.01em}
.post-item h2 a{text-decoration:none;transition:color .15s}
.post-item h2 a:hover{color:var(--accent)}
.post-item .desc{margin-top:4px;font-size:14px;color:var(--text-2)}
.post-item .when{margin-top:4px;font-size:13px;color:var(--text-3)}

/* ---- 글 페이지 ---- */
.post{padding:48px 0 96px}
.series-note{font-size:14px;color:var(--text-2);margin-bottom:14px}
.series-note a{color:var(--accent);text-decoration:underline;text-underline-offset:3px;font-weight:700}
.post-title{font-family:var(--display);font-size:28px;font-weight:700;line-height:1.4;letter-spacing:-.015em}
.post-meta{margin:10px 0 40px;font-size:13px;color:var(--text-3)}
.post-body>h2{font-family:var(--display);font-size:21px;font-weight:700;margin:56px 0 16px;scroll-margin-top:calc(var(--header-h) + 16px)}
.post-body>h3{font-size:17.5px;font-weight:700;margin:36px 0 12px;scroll-margin-top:calc(var(--header-h) + 16px)}
.post-body p{margin-bottom:1.35em}
.post-body a{color:var(--accent);text-decoration:underline;text-underline-offset:3px}
.post-body ul,.post-body ol{margin:0 0 1.35em 1.4em}
.post-body li{margin-bottom:.35em}
.post-body blockquote{border-left:3px solid var(--border);padding:2px 0 2px 16px;color:var(--text-2);margin-bottom:1.35em}
.post-body table{width:100%;border-collapse:collapse;margin-bottom:1.35em;font-size:14.5px}
.post-body th,.post-body td{border:1px solid var(--border);padding:9px 13px;text-align:left}
.post-body th{background:var(--surface)}
.post-body img{max-width:100%;border-radius:4px}
.post-body figcaption{font-size:13px;color:var(--text-3);margin-top:6px;text-align:center}
.post-body code{font-family:var(--mono);font-size:13.5px;background:var(--surface);
  border:1px solid var(--border);border-radius:4px;padding:1px 5px}
.post-body pre code{background:none;border:none;padding:0;font-size:13.5px}
.footnotes{font-size:14px;color:var(--text-2);border-top:1px solid var(--border);margin-top:48px;padding-top:16px}
.anchor{opacity:0;margin-left:8px;text-decoration:none;color:var(--text-3);font-weight:400}
h2:hover .anchor,h3:hover .anchor{opacity:1}
.anchor:focus-visible{opacity:1}

/* ---- 콜아웃 ---- */
.callout{border-left:3px solid var(--accent);padding:2px 0 2px 16px;margin-bottom:1.35em;color:var(--text-2)}
.callout b:first-child{color:var(--text)}

/* ---- 코드블록 ---- */
.codeblock{position:relative;margin-bottom:1.35em}
.codeblock pre{background:var(--code-bg);color:var(--code-text);border:1px solid var(--border);
  border-radius:8px;padding:16px 18px;overflow-x:auto;line-height:1.7}
.codeblock .cb-bar{position:absolute;top:6px;right:8px;display:flex;align-items:center;gap:4px}
.cb-lang{font-size:12px;color:var(--text-2)}
.cb-copy{display:inline-flex;align-items:center;justify-content:center;min-width:44px;min-height:44px;
  background:none;border:none;color:var(--text-2);cursor:pointer}
.cb-copy:hover{color:var(--text)}
.chroma .c,.chroma .c1,.chroma .cm{color:var(--code-comment)}
.chroma .k,.chroma .kd,.chroma .kn,.chroma .nb{color:var(--code-keyword)}
.chroma .s,.chroma .s1,.chroma .s2{color:var(--code-string)}
.chroma .hl{display:block;background:var(--hl-line);margin:0 -18px;padding:0 16px;border-left:2px solid var(--accent)}

/* ---- 노선도 (목차와 연재 공용) ---- */
.linemap{list-style:none}
.linemap li{position:relative;padding:0 0 0 24px}
.linemap li+li{margin-top:2px}
.linemap li::before{content:"";position:absolute;left:2px;top:14px;width:9px;height:9px;
  border-radius:50%;border:1.5px solid var(--text-3)}
.linemap li:not(:last-child)::after{content:"";position:absolute;left:6px;top:26px;bottom:-12px;
  border-left:1.5px solid var(--border)}
.linemap li.done::before{background:var(--accent);border-color:var(--accent)}
.linemap li.todo{color:var(--text-3)}
.linemap li.todo::before{border-style:solid}
.linemap li:has(+ .todo)::after{border-left-style:dashed;border-left-color:var(--text-3)}
.linemap a{font-size:14.5px;color:var(--text-2);text-decoration:none;
  display:inline-flex;min-height:30px;align-items:center}
.linemap a:hover{color:var(--accent)}
.linemap a[aria-current=location]{color:var(--station);font-weight:700}
.linemap li:has(a[aria-current=location])::before{background:var(--station);border-color:var(--station)}
.linemap li.passed::before{background:var(--accent);border-color:var(--accent)}

/* ---- 목차 배치 ---- */
.toc-mobile{margin:0 0 40px}
.toc-mobile summary{font-weight:700;font-size:14.5px;cursor:pointer;min-height:44px;display:flex;align-items:center}
.toc-desktop{display:none}
@media (min-width:1100px){
  .toc-mobile{display:none}
  .toc-desktop{display:block;position:fixed;top:120px;left:calc(50% + 22rem + 32px);width:220px}
}

/* ---- 태그와 하단 내비 ---- */
.post-tags{margin-top:48px;padding-top:16px;border-top:1px solid var(--border);font-size:14px;color:var(--text-2)}
.post-tags a{color:var(--text-2);text-decoration:underline;text-underline-offset:3px}
.foot-nav{display:flex;justify-content:space-between;gap:16px;margin-top:16px;font-size:14px}
.foot-nav a{color:var(--text-2);text-decoration:none;display:inline-flex;min-height:44px;align-items:center}
.foot-nav a:hover{color:var(--accent)}
.foot-nav .next{margin-left:auto;color:var(--accent);font-weight:700}

/* ---- 연재 인덱스 ---- */
.series-page{padding:48px 0 96px}
.series-page h1{font-family:var(--display);font-size:24px;font-weight:700;margin-bottom:40px}
.series-block{margin-bottom:48px}
.series-block h2{font-family:var(--display);font-size:18px;font-weight:700;margin-bottom:14px;
  scroll-margin-top:calc(var(--header-h) + 16px)}
.series-block h2 .count{font-size:13px;color:var(--text-3);font-weight:400;margin-left:8px}
.tag-list{margin-top:56px;padding-top:20px;border-top:1px solid var(--border)}
.tag-list h2{font-size:15px;font-weight:700;margin-bottom:8px}
.tag-list p{font-size:14px;color:var(--text-2)}
.tag-list a{color:var(--text-2);text-decoration:underline;text-underline-offset:3px}

/* ---- 푸터 ---- */
.site-footer{border-top:1px solid var(--border);padding:24px 0;font-size:13px;color:var(--text-3)}
.site-footer .wrap{display:flex;justify-content:space-between;gap:12px}
.site-footer a{color:var(--text-3);text-decoration:none;display:inline-flex;min-height:44px;align-items:center;padding:0 6px}
.site-footer a:hover{color:var(--text)}

/* ---- 404 ---- */
.error-page{text-align:center;padding:96px 0}
.error-page h1{font-family:var(--display);font-size:28px}
.error-page p{margin-top:12px;color:var(--text-2)}
```

- [ ] **Step 3: head partial**

`layouts/partials/head.html`:

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ if .IsHome }}{{ site.Title }}{{ else }}{{ .Title }} — {{ site.Title }}{{ end }}</title>
<meta name="description" content="{{ with .Description }}{{ . }}{{ else }}{{ site.Params.bio }}{{ end }}">
<meta name="author" content="{{ site.Params.author }}">
<meta property="og:title" content="{{ if .IsHome }}{{ site.Title }}{{ else }}{{ .Title }}{{ end }}">
<meta property="og:description" content="{{ with .Description }}{{ . }}{{ else }}{{ site.Params.bio }}{{ end }}">
<meta property="og:url" content="{{ .Permalink }}">
<meta property="og:site_name" content="{{ site.Title }}">
<meta property="og:type" content="{{ if .IsPage }}article{{ else }}website{{ end }}">
<meta property="og:image" content="{{ "og-default.png" | absURL }}">
{{ range .Translations }}<link rel="alternate" hreflang="{{ .Language.Lang }}" href="{{ .Permalink }}">{{ end }}
<link rel="icon" type="image/svg+xml" href="{{ "favicon.svg" | relURL }}">
{{ with .OutputFormats.Get "rss" }}<link rel="alternate" type="application/rss+xml" title="{{ site.Title }}" href="{{ .Permalink }}">{{ end }}
<script>
(function(){var t=localStorage.getItem("theme");
if(!t){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}
document.documentElement.dataset.theme=t})();
</script>
{{ $css := resources.Get "css/main.css" | minify }}
<link rel="stylesheet" href="{{ $css.RelPermalink }}">
```

- [ ] **Step 4: header partial (테마 토글 포함)**

`layouts/partials/header.html`:

```html
<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="{{ "/" | relLangURL }}">{{ site.Title }}</a>
    <nav class="site-nav" aria-label="사이트">
      <a href="{{ "/series/" | relLangURL }}">series</a>
      <a href="{{ "/about/" | relLangURL }}">about</a>
      {{ range .Translations }}
      <a class="lang-switch" href="{{ .Permalink }}" hreflang="{{ .Language.Lang }}"
         aria-label="{{ i18n "toEnglish" }}">EN</a>
      {{ end }}
      <button class="theme-toggle" type="button" aria-label="{{ i18n "themeToggleToDark" }}">
        <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>
        <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" aria-hidden="true" hidden>
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      </button>
    </nav>
  </div>
</header>
<script>
(function(){
  var b=document.querySelector(".theme-toggle"),r=document.documentElement;
  var L={dark:{{ i18n "themeToggleToLight" | jsonify }},light:{{ i18n "themeToggleToDark" | jsonify }}};
  function sync(){var d=r.dataset.theme==="dark";
    b.querySelector(".icon-moon").hidden=d;b.querySelector(".icon-sun").hidden=!d;
    b.setAttribute("aria-label",d?L.dark:L.light)}
  b.addEventListener("click",function(){
    r.dataset.theme=r.dataset.theme==="dark"?"light":"dark";
    localStorage.setItem("theme",r.dataset.theme);sync()});
  sync();
  if(document.body.classList.contains("home")){
    var hero=document.querySelector(".hero");
    if(hero&&"IntersectionObserver"in window){
      new IntersectionObserver(function(e){
        document.body.classList.toggle("scrolled",!e[0].isIntersecting)
      }).observe(hero)}}
})();
</script>
```

- [ ] **Step 5: footer partial과 baseof**

`layouts/partials/footer.html`:

```html
<footer class="site-footer">
  <div class="wrap">
    <span>© {{ now.Year }} {{ site.Params.author }}</span>
    <span>
      <a href="{{ site.Params.github }}">GitHub</a>
      {{ with .OutputFormats.Get "rss" }}<a href="{{ .Permalink }}">RSS</a>{{ end }}
    </span>
  </div>
</footer>
```

`layouts/_default/baseof.html`:

```html
<!doctype html>
<html lang="{{ site.Language.Lang }}">
<head>{{ partial "head.html" . }}</head>
<body class="{{ if .IsHome }}home{{ end }}">
  <a class="skip-link" href="#main">{{ i18n "skipToContent" }}</a>
  {{ partial "header.html" . }}
  <main id="main">{{ block "main" . }}{{ end }}</main>
  {{ partial "footer.html" . }}
</body>
</html>
```

`layouts/_default/list.html` (폴백):

```html
{{ define "main" }}<div class="wrap">{{ .Content }}</div>{{ end }}
```

- [ ] **Step 6: 빌드와 검증**

```bash
hugo && grep -o 'data-theme' public/index.html | head -1 && grep -c 'skip-link' public/index.html
```

Expected: 빌드 성공, `data-theme` FOUC 스크립트와 `skip-link` 각 1회 이상 검출.

- [ ] **Step 7: 커밋**

```bash
git add assets/css layouts/partials layouts/_default/baseof.html layouts/_default/list.html i18n
git commit -m "feat: 디자인 토큰과 베이스 템플릿, 테마 토글"
```

---

### Task 4: 홈 화면

**Files:**
- Create: `layouts/index.html`
- Create: `content/posts/_test-sample.md` (검증용 임시 글, Task 9에서 삭제)

**Interfaces:**
- Consumes: `.hero`, `.post-list` 클래스(Task 3), front matter `description`.
- Produces: 홈이 `site.RegularPages`의 `section posts`만 나열한다는 규약.

- [ ] **Step 1: 검증용 임시 글 생성**

`content/posts/_test-sample.md`:

```markdown
---
title: "임시 검증 글"
date: 2026-07-17
description: "레이아웃 검증을 위한 임시 글입니다."
tags: [검증]
draft: false
---

## 첫 번째 섹션

본문 문단.

## 두 번째 섹션

본문 문단.

## 세 번째 섹션

본문 문단.

## 네 번째 섹션

`ipcalc 192.168.1.0/26` 인라인 코드.
```

- [ ] **Step 2: index.html 작성**

`layouts/index.html`:

```html
{{ define "main" }}
<div class="wrap">
  <section class="hero">
    <h1>{{ site.Params.author }}</h1>
    <p>{{ site.Params.bio }}
      {{ with site.GetPage "/series" }}지금은 <a href="{{ .RelPermalink }}#network-basics">네트워크 기초 연재</a>를 쓰고 있습니다.{{ end }}</p>
  </section>
  <ul class="post-list">
    {{ range where site.RegularPages "Section" "posts" }}
    <li class="post-item">
      <h2><a href="{{ .RelPermalink }}">{{ .Title }}</a></h2>
      {{ with .Description }}<p class="desc">{{ . }}</p>{{ end }}
      <p class="when">{{ .Date | time.Format "2006년 1월 2일" }}, {{ .ReadingTime }}분</p>
    </li>
    {{ end }}
  </ul>
</div>
{{ end }}
```

- [ ] **Step 3: 빌드와 검증**

```bash
hugo && grep -o '2026년 7월 17일, [0-9]*분' public/index.html
grep -c '·' public/index.html || echo "no middle dots"
```

Expected: 날짜 형식 `2026년 7월 17일, n분` 검출, 가운뎃점 0.

- [ ] **Step 4: 커밋**

```bash
git add layouts/index.html content/posts/_test-sample.md
git commit -m "feat: 홈 화면 - 히어로와 글 목록"
```

---

### Task 5: 글 페이지 (본문, 메타, 태그, 연재 이전/다음)

**Files:**
- Create: `layouts/_default/single.html`
- Create: `layouts/_default/_markup/render-heading.html`
- Create: `layouts/shortcodes/callout.html`

**Interfaces:**
- Consumes: `.post`, `.series-note`, `.foot-nav`, `.callout`, `.anchor` 클래스. front matter — `series`(연재 이름), `series_slug`(영문 앵커), `lastmod`.
- Produces: `single.html`이 Task 6, 7의 partial 삽입 지점을 가진다(`toc-linemap.html`은 Task 7에서 추가).

- [ ] **Step 1: 헤딩 앵커 렌더 훅**

`layouts/_default/_markup/render-heading.html`:

```html
<h{{ .Level }} id="{{ .Anchor | safeURL }}">{{ .Text | safeHTML }}
{{- if eq .Level 2 }} <a class="anchor" href="#{{ .Anchor | safeURL }}" aria-label="{{ .PlainText }} 섹션 링크">#</a>{{ end -}}
</h{{ .Level }}>
```

- [ ] **Step 2: 콜아웃 쇼트코드**

`layouts/shortcodes/callout.html`:

```html
<div class="callout"><p><b>{{ .Get 0 | default "참고" }}</b> — {{ .Inner | markdownify }}</p></div>
```

사용법: `{{</* callout */>}}서브넷 마스크의 1의 개수가 곧 프리픽스 길이입니다.{{</* /callout */>}}`

- [ ] **Step 3: single.html 작성**

`layouts/_default/single.html`:

```html
{{ define "main" }}
{{ $series := .Params.series }}
{{ $siblings := slice }}
{{ if $series }}
  {{ $siblings = where (where site.RegularPages "Section" "posts") "Params.series" $series }}
  {{ $siblings = sort $siblings "Date" "asc" }}
{{ end }}
<article class="post wrap">
  {{ if $series }}
    {{ $idx := 0 }}
    {{ range $i, $p := $siblings }}{{ if eq $p.Permalink $.Permalink }}{{ $idx = add $i 1 }}{{ end }}{{ end }}
    <p class="series-note"><a href="{{ (site.GetPage "/series").RelPermalink }}#{{ .Params.series_slug }}">{{ $series }} 연재</a>의 {{ $idx }}편입니다.</p>
  {{ end }}
  <h1 class="post-title">{{ .Title }}</h1>
  <p class="post-meta">{{ .Date | time.Format "2006년 1월 2일" }}, {{ .ReadingTime }}분{{ if ne .Lastmod .Date }}, {{ .Lastmod | time.Format "2006년 1월 2일" }} 고침{{ end }}</p>
  {{ partial "toc-linemap.html" . }}
  <div class="post-body">{{ .Content }}</div>
  {{ with .Params.tags }}
  <p class="post-tags">{{ range $i, $t := . }}{{ if $i }}, {{ end }}<a href="{{ (printf "/tags/%s/" ($t | urlize)) | relLangURL }}">{{ $t }}</a>{{ end }}</p>
  {{ end }}
  {{ if $series }}
  <nav class="foot-nav" aria-label="연재 이동">
    {{ $prev := "" }}{{ $next := "" }}
    {{ range $i, $p := $siblings }}
      {{ if eq $p.Permalink $.Permalink }}
        {{ if gt $i 0 }}{{ $prev = index $siblings (sub $i 1) }}{{ end }}
        {{ if lt (add $i 1) (len $siblings) }}{{ $next = index $siblings (add $i 1) }}{{ end }}
      {{ end }}
    {{ end }}
    {{ with $prev }}<a href="{{ .RelPermalink }}">← {{ .Title }}</a>{{ end }}
    {{ with $next }}<a class="next" href="{{ .RelPermalink }}">{{ .Title }} →</a>{{ end }}
  </nav>
  {{ end }}
</article>
{{ end }}
```

- [ ] **Step 4: toc partial 스텁 (Task 7 전까지 빈 파일)**

```bash
echo "" > layouts/partials/toc-linemap.html
```

- [ ] **Step 5: 빌드와 검증**

```bash
hugo && P=public/posts/_test-sample/index.html
grep -c 'class="anchor"' $P          # h2 앵커 4
grep -rl 'scroll-margin' public/css/ # 토큰 CSS에 scroll-margin 존재
grep -c '·' $P || echo "no middle dots"
```

Expected: 앵커 4개, 가운뎃점 0. (임시 글에는 series가 없으므로 foot-nav와 series-note가 렌더링되지 않는 것도 확인: `grep -c 'foot-nav' $P` → 0.)

- [ ] **Step 6: 커밋**

```bash
git add layouts/_default/single.html layouts/_default/_markup layouts/shortcodes layouts/partials/toc-linemap.html
git commit -m "feat: 글 페이지 - 본문, 연재 내비, 헤딩 앵커, 콜아웃"
```

---

### Task 6: 코드블록 (언어 라벨, 복사 버튼, 라인 하이라이트)

**Files:**
- Create: `layouts/_default/_markup/render-codeblock.html`
- Create: `assets/js/copy.js`
- Modify: `layouts/_default/single.html` (copy.js 로드 한 줄 추가)

**Interfaces:**
- Consumes: `.codeblock`, `.cb-bar`, `.cb-lang`, `.cb-copy` 클래스, i18n `copyCode`, `copied`.
- Produces: 코드블록 DOM 구조 `<div class="codeblock"><div class="cb-bar">…</div><pre>…</pre></div>`.

- [ ] **Step 1: 코드블록 렌더 훅**

`layouts/_default/_markup/render-codeblock.html`:

```html
<div class="codeblock">
  <div class="cb-bar">
    {{ with .Type }}<span class="cb-lang">{{ . }}</span>{{ end }}
    <button class="cb-copy" type="button" aria-label="{{ i18n "copyCode" }}" data-copied="{{ i18n "copied" }}">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>
    </button>
    <span class="cb-live" aria-live="polite"></span>
  </div>
  {{ highlight .Inner .Type .Options }}
</div>
```

- [ ] **Step 2: copy.js**

`assets/js/copy.js`:

```js
document.querySelectorAll(".codeblock").forEach(function (block) {
  var btn = block.querySelector(".cb-copy");
  var live = block.querySelector(".cb-live");
  if (!btn) return;
  btn.addEventListener("click", function () {
    var code = block.querySelector("pre code") || block.querySelector("pre");
    navigator.clipboard.writeText(code.innerText).then(function () {
      var svg = btn.innerHTML;
      btn.innerHTML =
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
      live.textContent = btn.dataset.copied;
      setTimeout(function () { btn.innerHTML = svg; live.textContent = ""; }, 1200);
    });
  });
});
```

- [ ] **Step 3: single.html 끝(`</article>` 직후, `{{ end }}` 앞)에 스크립트 로드 추가**

```html
{{ $copy := resources.Get "js/copy.js" | minify }}
<script src="{{ $copy.RelPermalink }}" defer></script>
```

- [ ] **Step 4: 임시 글에 코드펜스가 있는지 확인 후 빌드 검증**

`content/posts/_test-sample.md` 네 번째 섹션 아래에 추가:

````markdown
```bash {hl_lines=[2]}
# 서브넷 확인
ipcalc 192.168.1.0/26
```
````

```bash
hugo && P=public/posts/_test-sample/index.html
grep -c 'cb-copy' $P    # 1
grep -c 'cb-lang' $P    # 1
grep -c 'class="hl"' $P # 1 (라인 하이라이트)
```

Expected: 각 1 이상.

- [ ] **Step 5: 커밋**

```bash
git add layouts/_default/_markup/render-codeblock.html assets/js/copy.js layouts/_default/single.html content/posts/_test-sample.md
git commit -m "feat: 코드블록 - 언어 라벨, 복사 버튼, 라인 하이라이트"
```

---

### Task 7: 노선도 목차

**Files:**
- Modify: `layouts/partials/toc-linemap.html` (스텁 → 구현)
- Create: `assets/js/toc.js`

**Interfaces:**
- Consumes: `.linemap`, `.toc-mobile`, `.toc-desktop` 클래스. 본문 h2의 `id`(Goldmark autoHeadingID).
- Produces: `nav > ol.linemap > li > a[href="#id"]` 구조. `aria-current="location"`은 toc.js가 부여.

- [ ] **Step 1: toc partial 구현**

`layouts/partials/toc-linemap.html`:

```html
{{ $h2s := findRE `<h2[^>]*id="([^"]+)"[^>]*>` .Content }}
{{ if gt (len $h2s) 3 }}
{{ $items := slice }}
{{ range findRESubmatch `<h2[^>]*id="([^"]+)"[^>]*>(.*?) <a` .Content }}
  {{ $items = $items | append (dict "id" (index . 1) "text" (index . 2 | plainify)) }}
{{ end }}
<details class="toc-mobile">
  <summary>{{ i18n "toc" }}</summary>
  <nav aria-label="{{ i18n "toc" }}">
    <ol class="linemap">
      {{ range $items }}<li><a href="#{{ .id }}">{{ .text }}</a></li>{{ end }}
    </ol>
  </nav>
</details>
<nav class="toc-desktop" aria-label="{{ i18n "toc" }}">
  <ol class="linemap">
    {{ range $items }}<li><a href="#{{ .id }}">{{ .text }}</a></li>{{ end }}
  </ol>
</nav>
{{ end }}
```

- [ ] **Step 2: toc.js (스크롤 추적)**

`assets/js/toc.js`:

```js
(function () {
  var desktop = document.querySelector(".toc-desktop");
  if (!desktop || !("IntersectionObserver" in window)) return;
  var links = desktop.querySelectorAll(".linemap a");
  var map = new Map();
  links.forEach(function (a) {
    var h = document.getElementById(a.getAttribute("href").slice(1));
    if (h) map.set(h, a);
  });
  var current = null;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) current = map.get(e.target);
    });
    if (!current) return;
    var passed = true;
    links.forEach(function (a) {
      a.removeAttribute("aria-current");
      a.parentElement.classList.toggle("passed", passed && a !== current);
      if (a === current) { a.setAttribute("aria-current", "location"); passed = false; }
    });
  }, { rootMargin: "-10% 0px -70% 0px" });
  map.forEach(function (_a, h) { io.observe(h); });
})();
```

- [ ] **Step 3: single.html에 toc.js 로드 추가 (copy.js 로드 옆)**

```html
{{ $toc := resources.Get "js/toc.js" | minify }}
<script src="{{ $toc.RelPermalink }}" defer></script>
```

- [ ] **Step 4: 빌드와 검증**

```bash
hugo && P=public/posts/_test-sample/index.html
grep -c 'linemap' $P                       # 2 이상 (모바일 + 데스크톱)
grep -c '<summary>목차</summary>' $P        # 1
grep -c 'aria-label="목차"' $P              # 2
```

임시 글의 h2를 3개로 줄인 사본으로 생략 조건도 확인: h2 3개면 `linemap` 0.

- [ ] **Step 5: 브라우저 확인**

```bash
hugo server -p 1414 &
sleep 2 && open http://localhost:1414/posts/_test-sample/
```

확인: 1100px 이상에서 우측 고정 목차, 스크롤 시 현재 역 이동(색 변화), 클릭 시 sticky 헤더에 가리지 않는 앵커 이동, 축소 창에서 접힌 details. 확인 후 `kill %1`.

- [ ] **Step 6: 커밋**

```bash
git add layouts/partials/toc-linemap.html assets/js/toc.js layouts/_default/single.html
git commit -m "feat: 노선도 목차 - 앵커 링크, 스크롤 추적, 반응형"
```

---

### Task 8: 연재 인덱스 페이지

**Files:**
- Create: `content/series.md`
- Create: `layouts/_default/series.html`

**Interfaces:**
- Consumes: front matter `series`, `series_slug`. `.linemap`, `.series-block`, `.tag-list` 클래스.
- Produces: `/series/` 경로와 연재별 앵커 `#<series_slug>`. Task 5의 series-note 링크가 이 앵커를 가리킨다.

- [ ] **Step 1: content/series.md**

```markdown
---
title: "연재"
layout: series
url: /series/
---
```

- [ ] **Step 2: series 레이아웃**

`layouts/_default/series.html`:

```html
{{ define "main" }}
<div class="series-page wrap">
  <h1>{{ .Title }}</h1>
  {{ $posts := where site.RegularPages "Section" "posts" }}
  {{ $bySeries := dict }}
  {{ range $p := $posts }}
    {{ with $p.Params.series }}
      {{ $cur := index $bySeries . | default slice }}
      {{ $bySeries = merge $bySeries (dict . ($cur | append $p)) }}
    {{ end }}
  {{ end }}
  {{ range $name, $pages := $bySeries }}
  {{ $pages = sort $pages "Date" "asc" }}
  {{ $slug := (index $pages 0).Params.series_slug }}
  {{ $total := (index $pages 0).Params.series_total }}
  <section class="series-block">
    <h2 id="{{ $slug }}">{{ $name }}<span class="count">
      {{- if and $total (lt (len $pages) (int $total)) }}{{ $total }}편 중 {{ len $pages }}편{{ else }}{{ len $pages }}편{{ end -}}
    </span></h2>
    <ol class="linemap">
      {{ range $pages }}<li class="done"><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>{{ end }}
      {{ with (index $pages 0).Params.series_upcoming }}<li class="todo">{{ . }}, 쓰는 중</li>{{ end }}
    </ol>
  </section>
  {{ end }}
  <div class="tag-list">
    <h2>태그</h2>
    <p>{{ range $i, $t := site.Taxonomies.tags.ByCount }}{{ if $i }}, {{ end }}<a href="{{ $t.Page.RelPermalink }}">{{ $t.Page.Title }} {{ $t.Count }}</a>{{ end }}</p>
  </div>
</div>
{{ end }}
```

규칙(스펙): 진행 중 연재는 "n편 중 m편"(front matter `series_total` 필요), 완결이나 미정은 "n편". 예정 글은 첫 글의 `series_upcoming: "TCP 심화"`로 표기하며 초고를 쓰는 동안만 두고 멈추면 지운다.

- [ ] **Step 3: 임시 글에 연재 front matter 부여 후 검증**

`content/posts/_test-sample.md` front matter에 추가:

```yaml
series: "네트워크 기초"
series_slug: network-basics
series_total: 3
```

```bash
hugo && S=public/series/index.html
grep -c 'id="network-basics"' $S   # 1
grep -o '3편 중 1편' $S             # 검출
grep -c '태그' $S                   # 1 이상
grep -c '·' $S || echo "no middle dots"
```

- [ ] **Step 4: 커밋**

```bash
git add content/series.md layouts/_default/series.html content/posts/_test-sample.md
git commit -m "feat: 연재 인덱스 - 노선도 목록과 태그"
```

---

### Task 9: 콘텐츠 마이그레이션과 Jekyll 제거

**Files:**
- Create: `content/posts/network-1-ip-subnetting.md` (기존 `_posts/2026-01-14-network-1-ip-subnetting.md`에서)
- Create: `content/about.md`
- Create: `layouts/404.html`
- Create: `static/og-default.png`
- Delete: `content/posts/_test-sample.md`
- Delete: Jekyll 파일 전부 — `_posts/ _layouts/ _includes/ _site/ _config.yml Gemfile Gemfile.lock jekyll-true-minimal.gemspec index.html 404.html archive/ categories/ contact/ about/ assets/css/syntax.css .jekyll-cache/ .ruby-lsp/` (assets/css/main.css는 Task 3에서 새 내용으로 교체됐으므로 지우지 않는다)
- Keep: `assets/favicon.svg` → `static/favicon.svg`로 이동, `LICENSE`, `README.md`, `docs/`

**Interfaces:**
- Consumes: Task 5, 8의 front matter 규약(`series`, `series_slug`, `series_total`, `description`, `url`).

- [ ] **Step 1: 글 이전**

```bash
mkdir -p content/posts
git mv assets/favicon.svg static/favicon.svg
```

`content/posts/network-1-ip-subnetting.md` — front matter만 아래로 교체하고 본문은 기존 파일에서 그대로 복사:

```yaml
---
title: "Network (1) — IP 주소 체계와 서브네팅"
date: 2026-01-14
url: /network/2026/01/14/network-1-ip-subnetting.html
description: "사설망 하나가 수백 개의 주소로 쪼개지는 과정을 계산해봅니다."
tags: [네트워크]
series: "네트워크 기초"
series_slug: network-basics
---
```

`url`은 Jekyll이 만들던 실제 경로(`_site`에서 확인된 `/network/2026/01/14/network-1-ip-subnitting.html`이 아니라 정확히 `/network/2026/01/14/network-1-ip-subnetting.html`)와 문자 단위로 같아야 한다. `description`은 초안이므로 사용자에게 확인 요청.

- [ ] **Step 2: about 이전 (기존 about/index.html 내용을 마크다운으로)**

`content/about.md`:

```markdown
---
title: "about"
url: /about/
---

## 한예빈 — Cloud Infrastructure Engineer

Terraform과 AWS로 멀티리전 재해복구 인프라를 직접 설계하고 구축합니다.
설계 의사결정과 그 근거를 기록하는 공간입니다.

### Links

- [GitHub](https://github.com/playdelaybluelay-stack)

### Skills

- AWS — VPC, EC2, ALB, DynamoDB, S3, CloudFront, WAF, IAM, SSM, Lambda, Step Functions
- Terraform — 모듈화, Default Tags, 원격 상태 관리
- GitHub Actions — OIDC 인증 기반 CI/CD
- Docker, Kubernetes (기초), Linux

### Certifications

- AWS Solutions Architect - Associate (2026.03)
- TOEIC 865 / FLEX 프랑스어 3B
```

(기존 Contact 링크는 contact 페이지 삭제와 함께 제거. 가운뎃점이 원문에 있으면 쉼표로 바꾼다.)

- [ ] **Step 3: 404**

`layouts/404.html`:

```html
{{ define "main" }}
<div class="error-page wrap">
  <h1>404</h1>
  <p>이 주소에는 페이지가 없습니다.</p>
  <p><a href="{{ "/" | relURL }}">홈으로</a></p>
</div>
{{ end }}
```

- [ ] **Step 4: 기본 OG 이미지 생성**

```bash
# ImageMagick 필요: brew install imagemagick
magick -size 1200x630 xc:"#fcfdfc" \
  -font "/tmp/fonts-src/Paperlogy-7Bold.ttf" -pointsize 72 -fill "#1c211f" \
  -gravity center -annotate +0-20 "한예빈" \
  -pointsize 28 -fill "#5e6a65" -annotate +0+60 "playdelaybluelay-stack.github.io" \
  static/og-default.png
```

- [ ] **Step 5: Jekyll 제거와 임시 글 삭제**

```bash
git rm -r _posts _layouts _includes _config.yml Gemfile Gemfile.lock \
  jekyll-true-minimal.gemspec index.html 404.html archive categories contact about assets/css/syntax.css
git rm content/posts/_test-sample.md
rm -rf _site .jekyll-cache .ruby-lsp
```

- [ ] **Step 6: 빌드와 URL 유지 검증**

```bash
hugo
test -f public/network/2026/01/14/network-1-ip-subnetting.html && echo "URL preserved"
test -f public/about/index.html && echo "about ok"
test -f public/404.html && echo "404 ok"
grep -rc '·' public/index.html public/series/index.html || echo "no middle dots"
```

Expected: 세 파일 존재, 가운뎃점 0.

- [ ] **Step 7: 커밋**

```bash
git add -A
git commit -m "feat: 콘텐츠 이전과 Jekyll 제거"
```

---

### Task 10: GitHub Actions 배포와 최종 검증

**Files:**
- Create: `.github/workflows/hugo.yml`
- Delete: `.github/` 안의 기존 Jekyll 관련 워크플로우(있다면)

**Interfaces:**
- Consumes: 전체 빌드.

- [ ] **Step 1: 기존 워크플로우 확인**

```bash
ls .github/workflows/ 2>/dev/null
```

Jekyll용이 있으면 `git rm`.

- [ ] **Step 2: Hugo 공식 워크플로우 작성**

`.github/workflows/hugo.yml`:

```yaml
name: Deploy Hugo site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.147.0
    steps:
      - name: Install Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb \
            https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb
          sudo dpkg -i ${{ runner.temp }}/hugo.deb
      - uses: actions/checkout@v4
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5
      - name: Build
        run: hugo --gc --minify --baseURL "${{ steps.pages.outputs.base_url }}/"
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: 최종 로컬 점검 목록 실행**

```bash
hugo --gc --minify
# 1. 가운뎃점 전수 검사
grep -rl '·' public/ && echo "FAIL: middle dot found" || echo "PASS"
# 2. 홈에 워드마크 숨김 클래스
grep -c 'class="home"' public/index.html
# 3. 글 페이지에 skip-link, aria-current 준비물
grep -c 'skip-link' public/network/2026/01/14/network-1-ip-subnetting.html
# 4. hreflang은 번역 없으므로 0이어야 정상
grep -c 'hreflang' public/index.html || echo "0 as expected"
```

- [ ] **Step 4: 브라우저 최종 확인 (사용자 체크포인트)**

`hugo server`로 라이트/다크 토글, 키보드 탭 순회(스킵 링크 → 내비 → 본문), 목차 추적, 코드 복사, 모바일 폭(375px) 확인을 사용자와 함께 한다. GitHub Pages 저장소 설정에서 Source를 GitHub Actions로 바꿔야 함을 안내한다.

- [ ] **Step 5: 커밋과 PR**

```bash
git add .github/workflows/hugo.yml
git commit -m "feat: GitHub Actions 배포 워크플로우"
git push -u origin hugo-redesign
gh pr create --title "Hugo 리디자인" --body "$(cat <<'EOF'
## Summary
- Jekyll에서 Hugo로 이전, 확정 디자인 스펙 구현
- 스펙: docs/superpowers/specs/2026-07-15-blog-redesign-design.md
- 기존 글 URL 유지, 서체 셀프호스팅, 노선도 목차, 테마 토글, i18n 구조

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## 남는 결정 (실행 중 사용자 확인 필요)

1. Task 2 Step 4 — 서체 실물 검증 통과 여부 (스펙의 게이트, 탈락 시 교체 경로 명시됨)
2. Task 9 Step 1 — 기존 글의 `description` 문구
3. Task 10 Step 4 — 배포 전 최종 육안 확인과 Pages Source 설정 변경
