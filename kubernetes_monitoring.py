#!/usr/bin/env python3
import os
import sys
import time
import datetime
from kubernetes import client, config
from tabulate import tabulate

def main_menu():
    """
    메인 메뉴 출력
    """
    print("\n===== Kubernetes Monitoring Tool =====")
    print("1) Event Monitoring")
    print("2) Error Pod Catch (가장 최근에 재시작된 컨테이너 Top 10)")
    print("3) Error Log Catch (가장 최근에 재시작된 컨테이너 목록에서 선택)")
    print("4) Pod Monitoring (생성된 순서)")
    print("5) Pod Monitoring (Running이 아닌 Pod: grep -ivE ' Ready')")
    print("6) Pod Monitoring - 전체/정상/비정상 Pod 개수 출력")
    print("7) Node Monitoring (Unhealthy Node 확인)")
    print("8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬)")
    print("Q) Quit")
    return input("Select an option: ").strip()

def get_tail_lines():
    """
    tail -n에 사용될 숫자 입력
    """
    while True:
        val = input("How many lines do you want to tail? (예: 30): ").strip()
        if val.isdigit():
            return val
        else:
            print("숫자로 입력해주세요.")

def watch_event_monitoring():
    """
    1. Event Monitoring
       - watch -n1 "kubectl get events -A --sort-by=\".metadata.managedFields[].time\" | tail -n <user_input>"
    """
    tail_num = get_tail_lines()
    cmd = f'watch -n1 "kubectl get events -A --sort-by=\\".metadata.managedFields[].time\\" | tail -n {tail_num}"'
    print(f"\nExecuting: {cmd}\n(Press Ctrl+C to stop)\n")
    os.system(cmd)

def error_pod_catch_once():
    """
    2) Error Pod Catch (최근 재시작 컨테이너 Top 10, 단 한 번 테이블 출력)
       - lastState.terminated.finishedAt 기준 내림차순 정렬
       - watch 없이 한 번만 표시
    """
    print("\n[2] 가장 최근에 재시작된 컨테이너 Top 10 (시간 기준) - 한 번만 표시")

    # kubeconfig 로드
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_pod_for_all_namespaces().items

    restarted_containers = []
    for pod in pods:
        ns = pod.metadata.namespace
        p_name = pod.metadata.name

        if not pod.status.container_statuses:
            continue

        for c_status in pod.status.container_statuses:
            term = c_status.last_state.terminated
            if term and term.finished_at:
                finished_at = term.finished_at
                # 문자열인 경우 datetime 변환
                if isinstance(finished_at, str):
                    finished_at = datetime.datetime.fromisoformat(
                        finished_at.replace("Z", "+00:00")
                    )
                restarted_containers.append((ns, p_name, c_status.name, finished_at))

    # finishedAt 기준 내림차순 정렬 후 Top 5
    restarted_containers.sort(key=lambda x: x[3], reverse=True)
    top_10 = restarted_containers[:10]

    if not top_10:
        print("재시작된 컨테이너가 없습니다.")
        return

    table = []
    for ns, podname, cname, fat in top_10:
        table.append([
            ns,
            podname,
            cname,
            fat.strftime("%Y-%m-%d %H:%M:%S")
        ])

    print("\n=== 최근 재시작된 컨테이너 Top 5 ===\n")
    print(tabulate(
        table,
        headers=["Namespace", "Pod", "Container", "LastTerminatedTime"],
        tablefmt="github"
    ))

def catch_error_logs():
    """
    3) Error Log Catch
       - 가장 최근에 재시작된 컨테이너를 동일한 기준(lastState.terminated.finishedAt)으로 전체 조회.
       - 테이블로 모두 보여주고, 인덱스를 입력받아 kubectl logs -p 출력.
    """
    print("\n[3] Error Log Catch (가장 최근에 재시작된 컨테이너 목록에서 선택)")
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # 모든 Pod의 containerStatuses를 가져와 정렬
    pods = v1.list_pod_for_all_namespaces().items
    restarted_containers = []
    for pod in pods:
        ns = pod.metadata.namespace
        p_name = pod.metadata.name

        if not pod.status.container_statuses:
            continue

        for c_status in pod.status.container_statuses:
            term = c_status.last_state.terminated
            if term and term.finished_at:
                finished_at = term.finished_at
                if isinstance(finished_at, str):
                    finished_at = datetime.datetime.fromisoformat(
                        finished_at.replace("Z", "+00:00")
                    )
                restarted_containers.append((ns, p_name, c_status.name, finished_at))

    # 최근에 재시작된 순 내림차순 (finishedAt)
    restarted_containers.sort(key=lambda x: x[3], reverse=True)

    # 테이블로 보여주기
    if not restarted_containers:
        print("최근 재시작된 컨테이너가 없습니다.")
        return

    table = []
    for i, (ns, p_name, c_name, fat) in enumerate(restarted_containers, start=1):
        table.append([
            i,
            ns,
            p_name,
            c_name,
            fat.strftime("%Y-%m-%d %H:%M:%S")
        ])

    print("\n=== 최근 재시작된 컨테이너 목록 (시간 기준) ===\n")
    print(tabulate(
        table,
        headers=["INDEX", "Namespace", "Pod", "Container", "LastTerminatedTime"],
        tablefmt="github"
    ))

    # 인덱스 선택
    while True:
        sel = input("\n로그를 볼 INDEX를 입력 (Q: 종료): ").strip()
        if sel.upper() == "Q":
            return

        if not sel.isdigit():
            print("숫자를 입력하거나 Q로 돌아가세요.")
            continue

        idx = int(sel)
        if idx < 1 or idx > len(restarted_containers):
            print("인덱스 범위를 벗어났습니다.")
            continue

        # 해당 컨테이너 정보
        ns, p_name, c_name, _ = restarted_containers[idx - 1]
        # 이전 로그 (-p), tail=50
        cmd = f"kubectl logs -n {ns} -p {p_name} -c {c_name} --tail=50"
        print(f"\nExecuting: {cmd}\n")
        os.system(cmd)

def watch_pod_monitoring_by_creation():
    """
    4) Pod Monitoring (생성된 순서대로)
       - watch -n1 "kubectl get po -A --sort-by=.status.startTime | tail -n <user_input>"
    """
    tail_num = get_tail_lines()
    cmd = f'watch -n1 "kubectl get po -A --sort-by=.status.startTime | tail -n {tail_num}"'
    print(f"\nExecuting: {cmd}\n(Press Ctrl+C to stop)\n")
    os.system(cmd)

def watch_non_running_pod():
    """
    5) Pod Monitoring (Running이 아닌 Pod)
       - grep -ivE ' Ready'
       - Running 문자열이 " Ready" 형태로 들어가면 제외, NotReady 등은 표시됨
    """
    tail_num = get_tail_lines()
    cmd = f'watch -n1 "kubectl get pods -A -o wide | grep -ivE \' Ready\' | tail -n {tail_num}"'
    print(f"\nExecuting: {cmd}\n(Press Ctrl+C to stop)\n")
    os.system(cmd)

def watch_pod_counts():
    """
    6) Pod Monitoring - 전체/정상/비정상 Pod 개수
       - 파이썬 루프
    """
    print("\n(Press Ctrl+C to stop watching)")
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        while True:
            pods = v1.list_pod_for_all_namespaces().items
            total = len(pods)
            running = sum(1 for p in pods if p.status.phase == "Running")
            abnormal = total - running

            os.system("clear")
            print("=== Pod Count Summary ===")
            print(f"Total Pods    : {total}")
            print(f"Running Pods  : {running}")
            print(f"Abnormal Pods : {abnormal}")

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nReturning to menu...")

def watch_unhealthy_nodes():
    """
    7) Node Monitoring (Unhealthy Node 확인)
       - watch -n1 "kubectl get no ... | grep -ivE ' Ready' | tail -n <user_input>"
    """
    tail_num = get_tail_lines()
    cmd = (
        'watch -n1 "'
        "kubectl get no "
        '-L topology.ebs.csi.aws.com/zone -L node.kubernetes.io/instancegroup '
        '--sort-by=.metadata.creationTimestamp '
        '| grep -ivE \' Ready\' '
        f'| tail -n {tail_num}"'
    )
    print(f"\nExecuting: {cmd}\n(Press Ctrl+C to stop)\n")
    os.system(cmd)

def watch_node_resources():
    """
    8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬)
       - 사용자에게 CPU 또는 Memory 선택 -> sort 컬럼 결정
       - watch -n1 "kubectl top node | ...sort... | head -n ..."
    """
    while True:
        sort_key = input("정렬 기준을 선택하세요 (1: CPU, 2: Memory): ").strip()
        if sort_key == "1":
            sort_column = 3
            break
        elif sort_key == "2":
            sort_column = 5
            break
        else:
            print("잘못된 입력입니다. 다시 입력해주세요.")

    while True:
        val = input("상위 몇 개 노드를 볼까요? (예: 5): ").strip()
        if val.isdigit():
            top_n = val
            break
        else:
            print("숫자로 입력해주세요.")

    cmd = (
        f'watch -n1 "kubectl top node '
        f'| sed 1d '
        f'| sort -k{sort_column} -nr '
        f'| head -n {top_n}"'
    )
    print(f"\nExecuting: {cmd}\n(Press Ctrl+C to stop)\n")
    os.system(cmd)

def main():
    while True:
        choice = main_menu()
        if choice == "1":
            watch_event_monitoring()
        elif choice == "2":
            error_pod_catch_once()    # watch 제거, 한 번만 Top 5
        elif choice == "3":
            catch_error_logs()
        elif choice == "4":
            watch_pod_monitoring_by_creation()
        elif choice == "5":
            watch_non_running_pod()
        elif choice == "6":
            watch_pod_counts()
        elif choice == "7":
            watch_unhealthy_nodes()
        elif choice == "8":
            watch_node_resources()
        elif choice.upper() == "Q":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

