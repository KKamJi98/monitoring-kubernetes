# monitoring-kubernetes

Kubernetes Monitoring Tool

## Overview

- **주요 기능**  
  1. **Event Monitoring**  
     Kubernetes 클러스터 전체 이벤트를 실시간으로 확인  
  2. **Error Pod Catch**  
     가장 최근에 재시작된 컨테이너 정보를 시간 기준으로 정렬하여 확인  
  3. **Error Log Catch**  
     재시작된 컨테이너의 이전 로그(-p 옵션)를 확인  
  4. **Pod Monitoring**  
     Pod 생성 순서, Running이 아닌 Pod, 전체/정상/비정상 Pod 개수를 조회  
  5. **Node Monitoring**  
     Unhealthy Node, CPU/Memory 사용량이 높은 Node 등을 확인

## Requirements

- Python 3.8 이상
  - 가상환경(권장): pyenv, conda 또는 내장 venv 모듈을 사용하여 독립된 환경을 구성
- Python Library  
  - kubernetes  
  - tabulate  
- Kubernetes Client: kubectl

## Installation & Usage

### 1. Git Clone & Python 실행

1. **Repository Clone**
  
   ```shell
   git clone https://github.com/KKamJi98/monitoring-kubernetes.git
   cd monitoring-kubernetes
   ```

2. **라이브러리 설치**  

   ```shell
   pip install kubernetes tabulate
   ```
  
   - Python 3.8 버전 이상의 환경에서 실행을 권장합니다.

3. **스크립트 실행**  

   ```shell
   python kubernetes_monitoring.py
   ```
  
   - 메뉴가 표시되면 원하는 항목 번호(또는 Q)를 입력해 사용할 수 있습니다.

### 2. 실행 파일로 등록하여 사용 (Option)

1. **Repository Clone**
  
   ```shell
   git clone https://github.com/KKamJi98/monitoring-kubernetes.git
   cd monitoring-kubernetes
   ```

2. **라이브러리 설치**  

   ```shell
   pip install kubernetes tabulate
   ```

3. 실행 권한 부여

   ```shell
   chmod u+x kubernetes_monitoring.py
   ```

4. 경로 이동

   ```shell
   sudo cp kubernetes_monitoring.py /usr/local/bin/kubernetes_monitoring.py
   ```

5. 실행

   ```shell
   kubernetes_monitoring.py
   ```

일반적으로 `/usr/local/bin`은 기본적으로 `PATH`에 포함되어 있습니다.  
만약 `PATH`에 `/usr/local/bin` 이 없다면, `~/.shellrc` 또는 `~/.zshrc`에 다음 문구를 추가해야 합니다.  

```shell
export PATH=$PATH:/usr/local/bin
```

## Menu Description

실행 시 아래와 같은 메뉴 출력

```shell
===== Kubernetes Monitoring Tool =====
1) Event Monitoring (Normal, !=Normal)
2) Error Pod Catch (가장 최근에 재시작된 컨테이너 N개 확인)
3) Error Log Catch (가장 최근에 재시작된 컨테이너 N개 확인 후 이전 컨테이너의 로그 확인)
4) Pod Monitoring (생성된 순서) [옵션: Pod IP 및 Node Name 표시]
5) Pod Monitoring (Running이 아닌 Pod 확인) [옵션: Pod IP 및 Node Name 표시]
6) Pod Monitoring (전체/정상/비정상 Pod 개수 출력)
7) Node Monitoring (생성된 순서) [AZ, NodeGroup 표시 및 필터링 가능]
8) Node Monitoring (Unhealthy Node 확인) [AZ, NodeGroup 표시 및 필터링 가능]
9) Node Monitoring (CPU/Memory 사용량 높은 순 정렬) [NodeGroup 필터링 가능]
Q) Quit
```

1. **Event Monitoring**  
   - Kubernetes 이벤트를 실시간(`watch -n1`)으로 모니터링  
   - 최신 이벤트부터 tail -n [사용자 지정]으로 확인  

2. **Error Pod Catch**  
   - 최근 재시작된 컨테이너 정보를 N개까지 한번에 확인  
   - 내림차순 정렬(`lastState.terminated.finishedAt` 기준)

3. **Error Log Catch**  
   - 최근 재시작된 컨테이너 N개를 표시한 뒤, 특정 컨테이너를 선택해 이전 로그(-p 옵션)를 tail -n [사용자 지정]으로 확인  

4. **Pod Monitoring (생성된 순서)**  
   - 클러스터 내 Pod를 생성 시간 기준으로 나열.  
   - tail -n [사용자 지정] 설정 가능.

5. **Pod Monitoring (Running이 아닌 Pod 확인)**  
   - `kubectl get pods` 결과에서 `grep -ivE 'Running'`를 통해 Running이 아닌 Pod만 필터링.

6. **Pod Monitoring (전체/정상/비정상 Pod 개수)**  
   - 2초 간격(`time.sleep(2)`)으로 전체 Pod 개수와 현재 Running 상태인지 아닌지 표시

7. Node Monitoring (생성된 순서)

   - 노드의 생성 순서를 확인하며, 추가로 AZ 및 Node Group 정보를 표시
   - 인덱스 기반으로 특정 Node Group을 선택하여 필터링 가능

8. **Node Monitoring (Unhealthy Node 확인)**  
   - `kubectl get no` 결과에서 `grep -ivE ' Ready'`를 통해 Ready 상태가 아닌 노드만 필터링

9. **Node Monitoring (CPU/Memory 사용량 높은 순 정렬)**  
   - `kubectl top node` 결과를 CPU나 메모리 사용량 기준으로 정렬한 뒤 상위 N개를 확인
