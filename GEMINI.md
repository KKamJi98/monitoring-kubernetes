# Kubernetes Monitoring (목적 및 프로젝트 개요)

Kubernetes 클러스터의 리소스(Pod, Node 등)를 모니터링하고, 현재 상태를 CLI를 통해 시각적으로 제공하는 도구입니다. 사용자가 클러스터의 상태를 쉽게 확인하고 관리할 수 있도록 지원합니다.

## Rules

- **커밋:** Conventional Commits 사양을 따르며, `googleapis/release-please-action@v4`에 맞춰 커밋 메시지를 영어로 작성합니다.
- **버전 관리:** 시맨틱 버전 관리(vX.X.X)를 사용합니다.
- **포맷팅:** 코드는 `black`과 `ruff`로 포맷팅합니다.
- **코드 품질:** `black`, `ruff`, `mypy`, `pytest`를 모두 통과한 상태에서만 GitHub에 커밋 및 푸시합니다.
- **문서 업데이트:** `CHANGELOG.md`는 항상 현재 형식에 맞춰 갱신하고, `README.md`는 현재 프로젝트와 변경사항을 기반으로 항상 최신화합니다.

## Requirement

- **언어:** Python 3.8+
- **패키지 관리자:** `uv`

## Environment

- **테스팅:** `pytest`, `pytest-cov`
- **의존성:** 외부 의존성의 수를 최소한으로 유지하고, 가능하면 표준 라이브러리를 사용합니다.