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
    print("2) Error Pod Catch (가장 최근에 재시작된 컨테이너 N개 확인)")
    print("3) Error Log Catch (가장 최근에 재시작된 컨테이너 N개 확인 후 이전 컨테이너의 로그 확인)")
    print("4) Pod Monitoring (생성된 순서)")
    print("5) Pod Monitoring (Running이 아닌 Pod: grep -ivE 'Running')")
    print("6) Pod Monitoring (전체/정상/비정상 Pod 개수 출력)")
    print("7) Node Monitoring (Unhealthy Node 확인)")
    print("8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬)")
    print("Q) Quit")
    return input("Select an option: ").strip()


def get_tail_lines(prompt="몇 줄씩 확인할까요? (예: 10): "):
    """
    tail -n 에 사용할 숫자 입력
    """
    while True:
        val = input(prompt).strip()
        if val.isdigit():
            return val
        else:
            print("숫자로 입력해주세요.")


def watch_event_monitoring():
    """
    1) Event Monitoring
        watch -n1 "kubectl get events -A --sort-by=\".metadata.managedFields[].time\" | tail -n <user_input>"
    """
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 30): ")
    cmd = f'watch -n1 "kubectl get events -A --sort-by=\\".metadata.managedFields[].time\\" | tail -n {tail_num}"'
    print(f"\n실행 명령어: {cmd}\n(Ctrl+C로 중지)\n")
    os.system(cmd)


def error_pod_catch_once():
    """
    2) Error Pod Catch
        가장 최근에 재시작된 컨테이너 중 상위 N개를 한 번만 표시
        lastState.terminated.finishedAt 기준으로 내림차순 정렬
    """
    print("\n[2] 가장 최근에 재시작된 컨테이너 Top N (시간 기준, 한 번만 표시)")

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
                if isinstance(finished_at, str):
                    finished_at = datetime.datetime.fromisoformat(
                        finished_at.replace("Z", "+00:00")
                    )
                restarted_containers.append((ns, p_name, c_status.name, finished_at))

    # finishedAt 기준 내림차순 정렬
    restarted_containers.sort(key=lambda x: x[3], reverse=True)

    # 사용자 입력으로 몇 줄(항목)을 표시할지 결정
    line_count = int(get_tail_lines("몇 개의 컨테이너를 표시할까요? (예: 10): "))
    selected_containers = restarted_containers[:line_count]

    if not selected_containers:
        print("재시작된 컨테이너가 없습니다.")
        return

    table = []
    for ns, podname, cname, fat in selected_containers:
        table.append([ns, podname, cname, fat.strftime("%Y-%m-%d %H:%M:%S")])

    print(f"\n=== 최근 재시작된 컨테이너 Top {line_count} ===\n")
    print(
        tabulate(
            table,
            headers=["Namespace", "Pod", "Container", "LastTerminatedTime"],
            tablefmt="github",
        )
    )


def catch_error_logs():
    """
    3) Error Log Catch
        - 최근 재시작된 컨테이너를 모두 조회하여 시간 기준으로 내림차순 정렬
        - 목록을 보여준 뒤, 인덱스를 입력받아 해당 컨테이너의 이전 로그(-p)를 사용자가 지정한 줄 수만큼 확인
    """
    print("\n[3] Error Log Catch (가장 최근에 재시작된 컨테이너 목록에서 선택)")
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
                if isinstance(finished_at, str):
                    finished_at = datetime.datetime.fromisoformat(
                        finished_at.replace("Z", "+00:00")
                    )
                restarted_containers.append((ns, p_name, c_status.name, finished_at))

    # finishedAt 기준 내림차순 정렬
    restarted_containers.sort(key=lambda x: x[3], reverse=True)

    # 사용자 입력으로 몇 줄(항목)을 표시할지 결정
    line_count = int(get_tail_lines("몇 개의 컨테이너를 표시할까요? (예: 10): "))
    displayed_containers = restarted_containers[:line_count]

    if not displayed_containers:
        print("최근 재시작된 컨테이너가 없습니다.")
        return

    table = []
    for i, (ns, p_name, c_name, fat) in enumerate(displayed_containers, start=1):
        table.append([i, ns, p_name, c_name, fat.strftime("%Y-%m-%d %H:%M:%S")])

    print(f"\n=== 최근 재시작된 컨테이너 목록 (시간 기준, Top {line_count}) ===\n")
    print(
        tabulate(
            table,
            headers=["INDEX", "Namespace", "Pod", "Container", "LastTerminatedTime"],
            tablefmt="github",
        )
    )

    while True:
        sel = input("\n로그를 볼 INDEX를 입력 (Q: 종료): ").strip()
        if sel.upper() == "Q":
            return

        if not sel.isdigit():
            print("숫자를 입력하거나 Q를 입력해 종료하세요.")
            continue

        idx = int(sel)
        if idx < 1 or idx > len(displayed_containers):
            print("인덱스 범위를 벗어났습니다.")
            continue

        ns, p_name, c_name, _ = displayed_containers[idx - 1]
        # 로그 tail 줄 수 입력받기
        log_tail = input(
            "몇 줄의 로그를 확인할까요? (숫자 입력 *숫자를 입력하지 않을 시 마지막 50줄 출력): "
        ).strip()
        if not log_tail.isdigit():
            print("입력하신 값이 숫자가 아닙니다. 50줄을 출력합니다.")
            log_tail = "50"
        cmd = f"kubectl logs -n {ns} -p {p_name} -c {c_name} --tail={log_tail}"
        print(f"\n실행 명령어: {cmd}\n")
        os.system(cmd)


def watch_pod_monitoring_by_creation():
    """
    4) Pod Monitoring (생성된 순서)
        watch -n1 "kubectl get po -A --sort-by=.metadata.creationTimestamp | tail -n <user_input>"
    """
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 30): ")
    cmd = f'watch -n1 "kubectl get po -A --sort-by=.metadata.creationTimestamp | tail -n {tail_num}"'
    print(f"\n실행 명령어: {cmd}\n(Ctrl+C로 중지)\n")
    os.system(cmd)


def watch_non_running_pod():
    """
    5) Pod Monitoring (Running이 아닌 Pod 확인)
        grep -ivE 'Running' 를 통해 Running이 아닌 라인만 필터링 후 출력
    """
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 30): ")
    cmd = f"watch -n1 \"kubectl get pods -A -o wide | grep -ivE 'Running' | tail -n {tail_num}\""
    print(f"\n실행 명령어: {cmd}\n(Ctrl+C로 중지)\n")
    os.system(cmd)


def watch_pod_counts():
    """
    6) Pod Monitoring - 전체/정상(Running)/비정상 Pod 개수를 2초 간격으로 출력
    Ctrl+C로 메뉴로 리턴
    """
    print("\n(Ctrl+C로 중지 후 메뉴로 돌아갑니다.)")
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
        print("\n메뉴로 돌아갑니다...")


def watch_unhealthy_nodes():
    """
    7) Node Monitoring (Unhealthy Node 확인)
        watch -n1 "kubectl get no ... | grep -ivE ' Ready' | tail -n <user_input>"
    """
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 30): ")
    cmd = (
        'watch -n1 "'
        "kubectl get no "
        "-L topology.ebs.csi.aws.com/zone -L node.kubernetes.io/instancegroup "
        "--sort-by=.metadata.creationTimestamp "
        "| grep -ivE ' Ready' "
        f'| tail -n {tail_num}"'
    )
    print(f"\n실행 명령어: {cmd}\n(Ctrl+C로 중지)\n")
    os.system(cmd)


def watch_node_resources():
    """
    8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬)
        사용자에게 CPU 또는 Memory를 정렬 기준으로 입력받은 뒤, kubectl top node 결과를 정렬하여 표시
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
        f"| sed 1d "
        f"| sort -k{sort_column} -nr "
        f'| head -n {top_n}"'
    )
    print(f"\n실행 명령어: {cmd}\n(Ctrl+C로 중지)\n")
    os.system(cmd)


def main():
    """
    메인 함수 실행
    """
    while True:
        choice = main_menu()
        if choice == "1":
            watch_event_monitoring()
        elif choice == "2":
            error_pod_catch_once()
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
            print("잘못된 입력입니다. 메뉴에 표시된 숫자 또는 Q를 입력하세요.")


if __name__ == "__main__":
    main()
