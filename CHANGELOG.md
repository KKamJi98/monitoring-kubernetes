# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Refactor

* Rename '재시작된 컨테이너 확인 및 로그 조회' menu to 'Container Monitoring (재시작된 컨테이너 및 로그)' for consistency.

## [1.3.0](https://github.com/KKamJi98/monitoring-kubernetes/compare/v1.2.0...v1.3.0) (2025-07-04)


### Refactor

* Combine 'Error Pod Catch' and 'Error Log Catch' features into a single, streamlined function.


### Documentation

* Update README.md to reflect the combined functionality and re-ordered menu.

## [1.2.0](https://github.com/KKamJi98/monitoring-kubernetes/compare/v1.1.0...v1.2.0) (2025-06-28)


### Features

* Apply rich library for enhanced main menu display ([4d821c0](https://github.com/KKamJi98/monitoring-kubernetes/commit/4d821c064accc1c09a08eb5b11cd5e4dc9bc1bf1))
* Enhance main menu display ([76d2179](https://github.com/KKamJi98/monitoring-kubernetes/commit/76d2179c82e334ab84d7d472df1c8b01a733c4dc))


### Bug Fixes

* Ensure consistent rich styling for all main menu items ([7596ae2](https://github.com/KKamJi98/monitoring-kubernetes/commit/7596ae29685893c897266f9f4868f8fb310a9ee6))


### Documentation

* Update README.md UI and refactor menu title ([8c179b1](https://github.com/KKamJi98/monitoring-kubernetes/commit/8c179b13ce165658278f63d780db34427b773390))

## [1.1.0](https://github.com/KKamJi98/monitoring-kubernetes/compare/v1.0.1...v1.1.0) (2025-06-28)


### Features

* Add CI/CD pipeline and migrate from Poetry to UV ([30cc5c6](https://github.com/KKamJi98/monitoring-kubernetes/commit/30cc5c638dbbf6a704ee6009f94d888fa207ecd1))
* Integrate CI workflows and add GEMINI.md ([b7ab113](https://github.com/KKamJi98/monitoring-kubernetes/commit/b7ab113b97781324b94d75f3b7512e1a3aa1d432))


### Bug Fixes

* Add virtual environment creation to CI workflow ([b8dde70](https://github.com/KKamJi98/monitoring-kubernetes/commit/b8dde70b1406989c25b5ad2a53e4ef817b4e60e6))
* Adjust pyproject.toml dependencies to PEP 621 format ([5dcf80c](https://github.com/KKamJi98/monitoring-kubernetes/commit/5dcf80cb49fdfddf0ef4186f35b4e7f981070804))
* Correct pyproject.toml dependencies format for uv ([1b40125](https://github.com/KKamJi98/monitoring-kubernetes/commit/1b401254b651f800e31b962f70b96644ef81a953))


### Documentation

* Add GEMINI.md to .gitignore ([874f894](https://github.com/KKamJi98/monitoring-kubernetes/commit/874f894bfcda46ec93737645928d7892757621ba))

## [Unreleased]

## [0.1.0] - 2025-06-29
### Added
- Initial project setup.
