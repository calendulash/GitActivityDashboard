import os
import json
import urllib.request
import urllib.error
from urllib.parse import quote
from datetime import datetime, timedelta, timezone

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

COMMIT_DATA_SOURCE_ID = "3c28655a-72df-8076-a7aa-000b7d2948d4"
PROJECT_DATA_SOURCE_ID = "3c28655a-72df-8061-8782-000ba17e1ab9"

NOTION_VERSION = "2025-09-03"


def request_json(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(
        url,
        method=method,
        headers=headers or {},
        data=json.dumps(data).encode("utf-8") if data is not None else None,
    )

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print("HTTP ERROR:", e.code)
        print("URL:", url)
        print("BODY:", body)
        raise


def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "git-notion-tracker",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def get_project_repositories():
    url = f"https://api.notion.com/v1/data_sources/{PROJECT_DATA_SOURCE_ID}/query"

    # Notion에서 일단 전체 프로젝트를 가져온다.
    result = request_json(
        url,
        method="POST",
        headers=notion_headers(),
        data={}
    )

    print("Repo List 전체 행 수:", len(result.get("results", [])))

    repositories = []

    for page in result.get("results", []):
        props = page.get("properties", {})

        # 사용 여부 확인
        active = props.get("사용 여부", {}).get("checkbox", False)

        print("DEBUG 사용 여부:", active)

        if not active:
            continue

        github_id = ""
        repo_url = ""
        project_name = ""

        # GitHub ID
        rich_text = props.get("GitHub ID", {}).get("rich_text", [])
        if rich_text:
            github_id = rich_text[0].get("plain_text", "")

        # Repo URL
        repo_url = props.get("Repo URL", {}).get("url") or ""

        # 프로젝트명
        title = props.get("프로젝트명", {}).get("title", [])
        if title:
            project_name = title[0].get("plain_text", "")

        print("DEBUG 프로젝트:", project_name)
        print("DEBUG GitHub ID:", github_id)
        print("DEBUG Repo URL:", repo_url)

        if not repo_url:
            print("SKIP: Repo URL 없음")
            continue

        repo_url = repo_url.rstrip("/")

        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        prefix = "https://github.com/"

        if not repo_url.startswith(prefix):
            print("SKIP 잘못된 GitHub URL:", repo_url)
            continue

        repo_path = repo_url[len(prefix):]

        parts = repo_path.split("/")

        if len(parts) < 2:
            print("SKIP 잘못된 저장소:", repo_url)
            continue

        owner = parts[0]
        repo = parts[1]

        repositories.append({
            "github_id": github_id or owner,
            "project_name": project_name,
            "repo_path": f"{owner}/{repo}",
        })

    return repositories


def get_repository_info(repo_path):
    return request_json(
        f"https://api.github.com/repos/{repo_path}",
        headers=github_headers()
    )


def get_commits(repo_path, branch):
    url = (
        f"https://api.github.com/repos/{repo_path}/commits"
        f"?sha={quote(branch)}&per_page=100"
    )

    return request_json(url, headers=github_headers())


def get_commit_detail(repo_path, sha):
    return request_json(
        f"https://api.github.com/repos/{repo_path}/commits/{sha}",
        headers=github_headers()
    )


def notion_has_sha(sha):
    url = f"https://api.notion.com/v1/data_sources/{COMMIT_DATA_SOURCE_ID}/query"

    payload = {
        "filter": {
            "property": "커밋SHA",
            "rich_text": {
                "equals": sha
            }
        }
    }

    result = request_json(
        url,
        method="POST",
        headers=notion_headers(),
        data=payload,
    )

    return len(result.get("results", [])) > 0


def is_meaningful_file(filename):
    name = filename.lower()

    ignore_patterns = [
        "library/",
        "temp/",
        "logs/",
        "obj/",
        "build/",
        "usersettings/",
    ]

    for pattern in ignore_patterns:
        if pattern in name:
            return False

    if name.endswith(".meta"):
        return False

    if name in [
        "readme.md",
        ".gitignore",
        ".gitattributes",
    ]:
        return False

    meaningful_extensions = [
        ".cs",
        ".py",
        ".js",
        ".ts",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".java",
        ".shader",
        ".compute",
        ".json",
        ".asmdef",
        ".unity",
        ".prefab",
        ".controller",
        ".anim",
        ".asset",
        ".mat",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".wav",
        ".mp3",
        ".ogg",
        ".fbx",
        ".blend",
    ]

    return any(name.endswith(ext) for ext in meaningful_extensions)


def analyze_commit(detail, message):
    stats = detail.get("stats", {})
    files = detail.get("files", [])

    additions = stats.get("additions", 0)
    deletions = stats.get("deletions", 0)

    changed_files = len(files)
    meaningful_file_count = 0
    meaningful_change = 0

    for file_info in files:
        filename = file_info.get("filename", "")

        if is_meaningful_file(filename):
            meaningful_file_count += 1

            meaningful_change += (
                file_info.get("additions", 0)
                + file_info.get("deletions", 0)
            )

    suspicious_score = 0

    if meaningful_file_count == 0:
        suspicious_score += 45

    if meaningful_change <= 2:
        suspicious_score += 35
    elif meaningful_change <= 10:
        suspicious_score += 15

    if changed_files == 1 and meaningful_change <= 5:
        suspicious_score += 15

    simple_messages = [
        "수정",
        "수정1",
        "수정2",
        "fix",
        "update",
        "test",
        "테스트",
        "변경",
    ]

    clean_message = message.strip().lower()

    if clean_message in simple_messages:
        suspicious_score += 10

    if len(clean_message) <= 2:
        suspicious_score += 10

    suspicious_score = min(suspicious_score, 100)

    if suspicious_score >= 70:
        judgment = "뻥의심"
    elif suspicious_score >= 35:
        judgment = "확인필요"
    else:
        judgment = "정상"

    return {
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
        "meaningful_change": meaningful_change,
        "meaningful_file_count": meaningful_file_count,
        "suspicious_score": suspicious_score,
        "judgment": judgment,
    }


def add_commit_to_notion(
    project_name,
    github_id,
    repo_path,
    branch,
    sha,
    message,
    commit_url,
    commit_date,
    analysis,
):
    url = "https://api.notion.com/v1/pages"

    payload = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": COMMIT_DATA_SOURCE_ID,
        },
        "properties": {
            "커밋": {
                "title": [{
                    "text": {
                        "content": message[:2000]
                    }
                }]
            },
            "프로젝트명": {
                "rich_text": [{
                    "text": {
                        "content": project_name
                    }
                }]
            },
            "깃허브아이디": {
                "rich_text": [{
                    "text": {
                        "content": github_id
                    }
                }]
            },
            "저장소": {
                "rich_text": [{
                    "text": {
                        "content": repo_path
                    }
                }]
            },
            "브랜치": {
                "rich_text": [{
                    "text": {
                        "content": branch
                    }
                }]
            },
            "커밋SHA": {
                "rich_text": [{
                    "text": {
                        "content": sha
                    }
                }]
            },
            "커밋URL": {
                "url": commit_url
            },
            "날짜": {
                "date": {
                    "start": commit_date
                }
            },
            "변경파일수": {
                "number": analysis["changed_files"]
            },
            "추가라인": {
                "number": analysis["additions"]
            },
            "삭제라인": {
                "number": analysis["deletions"]
            },
            "실질변경량": {
                "number": analysis["meaningful_change"]
            },
            "의미파일수": {
                "number": analysis["meaningful_file_count"]
            },
            "의심점수": {
                "number": analysis["suspicious_score"]
            },
            "판정": {
                "select": {
                    "name": analysis["judgment"]
                }
            },
        },
    }

    request_json(
        url,
        method="POST",
        headers=notion_headers(),
        data=payload,
    )


def process_repository(project):
    repo_path = project["repo_path"]

    repo_info = get_repository_info(repo_path)
    branch = repo_info.get("default_branch", "main")

    print("")
    print("프로젝트:", project["project_name"])
    print("깃허브:", project["github_id"])
    print("저장소:", repo_path)
    print("브랜치:", branch)

    commits = get_commits(repo_path, branch)

    for item in reversed(commits):
        sha = item.get("sha", "")

        commit = item.get("commit", {})
        message = commit.get("message", "").splitlines()[0]

        author = commit.get("author") or {}
        commit_date = author.get("date", "")

        commit_url = item.get("html_url", "")

        if notion_has_sha(sha):
            print("SKIP:", sha[:7], message)
            continue

        detail = get_commit_detail(repo_path, sha)
        analysis = analyze_commit(detail, message)

        add_commit_to_notion(
            project_name=project["project_name"],
            github_id=project["github_id"],
            repo_path=repo_path,
            branch=branch,
            sha=sha,
            message=message,
            commit_url=commit_url,
            commit_date=commit_date,
            analysis=analysis,
        )

        print(
            "ADD:",
            sha[:7],
            message,
            "/",
            analysis["judgment"],
            "/ 점수:",
            analysis["suspicious_score"]
        )


def parse_github_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def relative_time(value, now):
    parsed = parse_github_date(value)
    if not parsed:
        return "기록 없음"
    days = max(0, (now - parsed).days)
    return "오늘" if days == 0 else "어제" if days == 1 else f"{days}일 전"


def activity_status(value, now):
    parsed = parse_github_date(value)
    if not parsed:
        return "inactive"
    days = (now - parsed).days
    return "active" if days <= 3 else "watch" if days <= 7 else "inactive"


def build_dashboard_data(projects):
    now = datetime.now(timezone.utc)
    rows = []

    for project in projects:
        repo_path = project["repo_path"]
        try:
            repo_info = get_repository_info(repo_path)
            branch = repo_info.get("default_branch", "main")
            items = get_commits(repo_path, branch)
            commits = []
            for item in items:
                commit = item.get("commit", {})
                author = commit.get("author") or commit.get("committer") or {}
                commits.append({
                    "date": author.get("date", ""),
                    "message": commit.get("message", "").splitlines()[0],
                    "sha": item.get("sha", "")[:7],
                    "url": item.get("html_url", ""),
                })

            week_ago = now - timedelta(days=7)
            recent_week = [row for row in commits if parse_github_date(row["date"]) and parse_github_date(row["date"]) >= week_ago]
            active_days = len({row["date"][:10] for row in recent_week if row["date"]})
            weekly = []
            for index in range(6, -1, -1):
                start = now - timedelta(days=(index + 1) * 7)
                end = now - timedelta(days=index * 7)
                weekly.append(sum(1 for row in commits if parse_github_date(row["date"]) and start <= parse_github_date(row["date"]) < end))

            last_date = commits[0]["date"] if commits else ""
            rows.append({
                "name": project["project_name"] or project["github_id"],
                "id": project["github_id"],
                "team": repo_path.split("/")[0],
                "github": project["github_id"],
                "repo": repo_path,
                "commits": len(recent_week),
                "activeDays": active_days,
                "lastCommit": relative_time(last_date, now),
                "status": activity_status(last_date, now),
                "weekly": weekly,
                "recent": [{"message": row["message"], "time": relative_time(row["date"], now), "sha": row["sha"], "url": row["url"]} for row in commits[:5]],
            })
        except Exception as error:
            print("DASHBOARD ERROR:", repo_path, str(error))
            rows.append({"name": project["project_name"] or project["github_id"], "id": project["github_id"], "team": repo_path.split("/")[0], "github": project["github_id"], "repo": repo_path, "commits": 0, "activeDays": 0, "lastCommit": "수집 실패", "status": "inactive", "weekly": [0, 0, 0, 0, 0, 0, 0], "recent": []})

    os.makedirs("data", exist_ok=True)
    payload = {
        "course": "Git 프로젝트 활동 현황",
        "notionUrl": "https://abaft-vibraphone-8f7.notion.site/Git-3c28655a72df80199dafc115fef9ddd4?pvs=74",
        "updatedAt": now.astimezone(timezone(timedelta(hours=9))).strftime("%Y. %m. %d. %H:%M"),
        "students": rows,
    }
    with open("data/students.json", "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print("대시보드 프로젝트 수:", len(rows))


def main():
    projects = get_project_repositories()

    print("활성 프로젝트 수:", len(projects))

    for project in projects:
        try:
            process_repository(project)

        except Exception as e:
            print(
                "ERROR:",
                project.get("repo_path"),
                str(e)
            )

    build_dashboard_data(projects)


if __name__ == "__main__":
    main()
