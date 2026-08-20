# Git 활동 대시보드 — GitHub Pages용

압축을 풀어 GitHub 저장소 루트에 그대로 커밋하면 됩니다. 별도 설치나 빌드 과정이 없는 순수 HTML·CSS·JavaScript 사이트입니다.

## 1. 학생 목록 수정

`config/students.json`에서 수업명, Notion 주소, 학기 시작일과 학생 정보를 수정합니다.

```json
{"name":"학생명","id":"학번","team":"팀명","github":"GitHub아이디","repo":"소유자/저장소명"}
```

저장소 하나를 팀원이 함께 쓸 경우 `repo`는 같게 두고 `github`만 학생별로 입력합니다.

## 2. GitHub Pages 켜기

저장소의 `Settings → Pages → Build and deployment → Source`에서 `GitHub Actions`를 선택합니다. `Actions` 탭에서 `Collect Git activity and deploy Pages`를 한 번 실행하면 주소가 생성됩니다.

매일 한국시간 00:10에 학생 커밋을 수집하고 Pages를 갱신합니다. `Actions → Run workflow`로 즉시 갱신할 수도 있습니다.

## 3. 비공개 저장소가 있을 때

공개 저장소만 사용하면 추가 설정이 필요 없습니다. 비공개 저장소를 읽어야 한다면 읽기 권한만 가진 Fine-grained personal access token을 만든 뒤 `Settings → Secrets and variables → Actions`에 `GH_PAT`라는 이름으로 저장합니다. 토큰을 파일에 직접 쓰면 안 됩니다.

## 4. Notion 임베드

생성된 Pages 주소를 복사하고 Notion에서 `/embed`에 붙여넣습니다.

## 상태 기준

- 정상: 마지막 커밋 3일 이내
- 확인 필요: 4~7일
- 미활동: 8일 이상 또는 수집 실패

교수 평가, 학생 회고, 결과물 링크와 개인정보는 GitHub Pages에 넣지 말고 Notion에서 관리하세요.
