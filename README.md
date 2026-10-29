# playdelaybluelay-blog

Hugo로 만든 개인 기술 블로그. `main`에 push하면 GitHub Actions가 배포한다.

## Obsidian에서 글 발행하기

1. Obsidian의 Post Template으로 쓰고, front matter에 `slug`, `published`, `kind`(설계, 트러블슈팅, 회고, 개념)를 채운다. 독서 정리는 `section: notes`와 `book`, `book_author`를 쓴다.
2. 발행할 준비가 되면 `publish: true`로 바꾼다.
3. `python3 scripts/publish.py`로 미리보기를 본다. 개인정보나 차단어가 걸리면 그 노트는 중단되고 이유가 나온다.
4. `python3 scripts/publish.py --write`로 `content/`에 반영하고 `hugo server`로 확인한다.
5. 커밋하고 push한다. 스크립트는 git을 건드리지 않는다.

테스트: `python3 -m unittest scripts/test_publish.py`
