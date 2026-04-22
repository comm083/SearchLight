# SearchLight Project

This is the top-level project directory for SearchLight.

---

# 🔦 SearchLight 프로젝트 Git 사용 가이드

이 문서는 SearchLight 프로젝트에서 팀원들이 Git과 GitHub를 활용하여 협업하는 기본 방법을 설명합니다.

---

# 📌 1. 기본 작업 흐름

```bash
브랜치 생성 → 작업 → commit → push → Pull Request → 코드 리뷰 → merge
```

---

# 🌿 2. 브랜치(Branch) 생성 방법

❗ main 브랜치에서 직접 작업 금지

```bash
# 최신 코드 가져오기
git pull origin main

# 브랜치 생성 및 이동
git checkout -b feat/#1-login-ui
```

📌 브랜치 이름 규칙

* 형식: `타입/#이슈번호-작업내용`
* 예시:

  * feat/#1-login-ui
  * fix/#2-login-error

---

# 💾 3. 작업 후 Commit & Push

```bash
# 변경 파일 추가
git add .

# 커밋
git commit -m "feat: 로그인 UI 구현"

# 원격 저장소로 업로드
git push origin feat/#1-login-ui
```

---

# 🔄 4. Pull Request(PR) 생성 방법

1. GitHub 저장소 접속
2. "Compare & pull request" 클릭
3. base: main / compare: 작업 브랜치 선택
4. 내용 작성 후 "Create pull request" 클릭

📌 PR 작성 시 포함 내용

* 작업 내용 설명
* 변경 이유
* 확인 방법

---

# 👀 5. 코드 리뷰 & 승인

* 팀원들이 PR에서 코드 확인
* 수정 요청 또는 승인(Approve)
* 승인 후에만 merge 가능

---

# 🔀 6. Merge (main에 반영)

```bash
Merge pull request → Confirm merge
```

✔ 모든 리뷰가 완료된 후 진행

---

# ⬇️ 7. Pull (최신 코드 가져오기)

```bash
git pull origin main
```

✔ 작업 시작 전에 반드시 실행

---

# 📤 8. Push (코드 업로드)

```bash
git push origin 브랜치이름
```

---

# 🚨 주의사항

* main 브랜치 직접 수정 ❌
* 반드시 브랜치 생성 후 작업
* PR 없이 merge 금지
* 커밋 메시지는 명확하게 작성

---

# 💡 추천 커밋 메시지 규칙

* feat: 기능 추가
* fix: 버그 수정
* design: UI 작업
* refactor: 코드 개선
* docs: 문서 수정

---

# ✅ 정리

👉 브랜치에서 작업 → PR 생성 → 리뷰 → 승인 → main 반영

이 과정을 반드시 지켜주세요.
