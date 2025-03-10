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
- Python Library (kubernetes, tabulate)
- kubectl

## Installation & Usage

### 1. Python 스크립트로 실행하기

1. **리포지토리 클론**
  
   ```bash
   git clone https://github.com/KKamJi98/monitoring-kubernetes.git
   cd monitoring-kubernetes
   ```

2. **필요 라이브러리 설치**  

   ```bash
   pip install kubernetes tabulate
   ```
  
   - Python 3.8 버전 이상의 환경에서 실행을 권장합니다.

3. **스크립트 실행**  

   ```bash
   python kubernetes_monitoring.py
   ```
  
   - 메뉴가 표시되면 원하는 항목 번호(또는 Q)를 입력해 사용할 수 있습니다.

### 2. 바이너리로 실행하기

1. **바이너리 다운로드**  
   - [bin/kubernetes_monitoring](https://github.com/KKamJi98/monitoring-kubernetes/blob/main/bin/kubernetes_monitoring)를 다운로드 받아 실행 권한을 부여합니다.

    ```bash
    chmod +x kubernetes_monitoring
    ```

2. **실행**  

  ```bash
  ./kubernetes_monitoring
  ```

## Menu Description

실행 시 아래와 같은 메뉴 출력

```shell
===== Kubernetes Monitoring Tool =====
1) Event Monitoring
2) Error Pod Catch (가장 최근에 재시작된 컨테이너 N개 확인)
3) Error Log Catch (가장 최근에 재시작된 컨테이너 N개 확인 후 이전 컨테이너의 로그 확인)
4) Pod Monitoring (생성된 순서)
5) Pod Monitoring (Running이 아닌 Pod: grep -ivE 'Running')
6) Pod Monitoring (전체/정상/비정상 Pod 개수 출력)
7) Node Monitoring (Unhealthy Node 확인)
8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬)
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

7. **Node Monitoring (Unhealthy Node 확인)**  
   - `kubectl get no` 결과에서 `grep -ivE ' Ready'`를 통해 Ready 상태가 아닌 노드만 필터링

8. **Node Monitoring (CPU/Memory 사용량 높은 순 정렬)**  
   - `kubectl top node` 결과를 CPU나 메모리 사용량 기준으로 정렬한 뒤 상위 N개를 확인
