#!/usr/bin/env python3

import datetime
import os
import sys
import time
from typing import List, Optional

try:
    from kubernetes import client, config
    from kubernetes.client import CoreV1Api, V1NamespaceList, V1Pod
except ImportError:
    client = None  # type: ignore
    config = None  # type: ignore
    CoreV1Api = None  # type: ignore
    V1Pod = None  # type: ignore
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

# 노드그룹 라벨을 변수로 분리 (기본값: node.kubernetes.io/app)
NODE_GROUP_LABEL = "node.kubernetes.io/app"


def cleanup() -> None:
    """리소스 정리 및 종료 전 후처리.

    현재는 외부 리소스를 별도로 잡지 않지만, 추후 확장을 대비해
    공통 정리 지점을 한곳으로 모읍니다.
    """
    # 필요한 경우, 추가 정리 작업을 이곳에 배치합니다.
    console.print("정리 중...", style="dim")


def _exit_with_cleanup(code: int, message: str, style: str = "bold yellow") -> None:
    """메시지를 출력하고 정리 후 지정된 코드로 종료."""
    # 요구사항: 메시지 앞에 한 줄 공백 출력
    print()
    console.print(message, style=style)
    cleanup()
    sys.exit(code)


def setup_asyncio_graceful_shutdown() -> None:
    """
    asyncio 사용 시 SIGINT/SIGTERM를 graceful 하게 처리하기 위한 유틸리티.

    이 함수는 런타임에 호출될 때만 의존성을 import 하며, 현재 스크립트가
    동기 방식으로 동작할 때는 불필요한 오버헤드를 만들지 않습니다.
    """
    try:
        import asyncio
        import contextlib
        import signal
    except Exception:
        return

    loop = asyncio.get_event_loop()

    stop_event = asyncio.Event()

    def _handle_signal(sig: int) -> None:
        console.print(
            f"신호 수신: {signal.Signals(sig).name}. 안전 종료를 시작합니다.",
            style="bold yellow",
        )
        stop_event.set()

    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is not None:
            try:
                loop.add_signal_handler(sig, _handle_signal, sig)
            except NotImplementedError:
                # Windows 등 일부 환경에서는 add_signal_handler 미지원
                pass

    async def _graceful_shutdown(timeout: float = 10.0) -> None:
        await stop_event.wait()
        tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)
        ]
        for t in tasks:
            t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks, return_exceptions=True)
        cleanup()

    # 호출 측에서 생성한 메인 코루틴과 함께 사용하도록 안내 목적.
    # 예: await asyncio.gather(main(), _graceful_shutdown())
    globals()["_async_graceful_shutdown"] = _graceful_shutdown  # for advanced usage


def load_kube_config() -> None:
    """kube config 로드 (예외처리 포함)"""
    try:
        config.load_kube_config()
    except Exception as e:
        print(f"Error loading kube config: {e}")
        sys.exit(1)


def choose_namespace() -> Optional[str]:
    """
    클러스터의 모든 namespace 목록을 표시하고, 사용자가 index로 선택
    아무 입력도 없으면 전체(namespace 전체) 조회
    """
    load_kube_config()
    v1 = client.CoreV1Api()
    try:
        ns_list: V1NamespaceList = v1.list_namespace()
        items = ns_list.items
    except Exception as e:
        print(f"Error fetching namespaces: {e}")
        return None

    if not items:
        print("Namespace가 존재하지 않습니다.")
        return None

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Index", style="bold green", width=5)
    table.add_column("Namespace")
    for idx, ns in enumerate(items, start=1):
        table.add_row(str(idx), ns.metadata.name)
    console.print("\n=== Available Namespaces ===", style="bold green")
    console.print(table)

    selection = Prompt.ask(
        "조회할 Namespace 번호를 선택하세요 (기본값: 전체)", default=""
    )
    if not selection:
        return None
    if not selection.isdigit():
        print("숫자로 입력해주세요. 전체 조회로 진행합니다.")
        return None
    index = int(selection)
    if index < 1 or index > len(items):
        print("유효하지 않은 번호입니다. 전체 조회로 진행합니다.")
        return None
    chosen_ns = str(items[index - 1].metadata.name)
    return chosen_ns


def choose_node_group() -> Optional[str]:
    """
    클러스터의 모든 노드 그룹 목록(NODE_GROUP_LABEL로부터) 표시 후, 사용자가 index로 선택
    아무 입력도 없으면 필터링하지 않음
    """
    load_kube_config()
    v1 = client.CoreV1Api()
    try:
        nodes = v1.list_node().items
    except Exception as e:
        print(f"Error fetching nodes: {e}")
        return None

    node_groups: List[str] = []
    temp_node_groups = set()
    for node in nodes:
        if node.metadata.labels and NODE_GROUP_LABEL in node.metadata.labels:
            temp_node_groups.add(node.metadata.labels[NODE_GROUP_LABEL])
    node_groups = sorted(list(temp_node_groups))
    if not node_groups:
        print("노드 그룹이 존재하지 않습니다.")
        return None
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Index", style="bold green", width=5)
    table.add_column("Node Group")
    for idx, ng in enumerate(node_groups, start=1):
        table.add_row(str(idx), ng)
    console.print("\n=== Available Node Groups ===", style="bold green")
    console.print(table)

    selection = Prompt.ask(
        "필터링할 Node Group 번호를 선택하세요 (기본값: 필터링하지 않음)", default=""
    )
    if not selection:
        return None
    if not selection.isdigit():
        print("숫자로 입력해주세요. 필터링하지 않음으로 진행합니다.")
        return None
    index = int(selection)
    if index < 1 or index > len(node_groups):
        print("유효하지 않은 번호입니다. 필터링하지 않음으로 진행합니다.")
        return None
    chosen_ng = node_groups[index - 1]
    return chosen_ng


def get_tail_lines(prompt="몇 줄씩 확인할까요? (숫자 입력. default: 20줄): ") -> str:
    """
    tail -n에 사용할 숫자 입력 (기본값 20)
    """
    val = Prompt.ask(prompt, default="20")
    if val.isdigit():
        return val
    else:
        console.print("숫자로 입력해주세요.", style="bold red")
        return "20"


def get_pods(v1_api: CoreV1Api, namespace: Optional[str] = None) -> List[V1Pod]:
    """
    지정된 namespace 또는 전체 namespace에서 Pod 목록을 가져옵니다.
    """
    try:
        if namespace:
            return list(v1_api.list_namespaced_pod(namespace=namespace).items)
        else:
            return list(v1_api.list_pod_for_all_namespaces().items)
    except Exception as e:
        print(f"Error fetching pods: {e}")
        return []


def watch_event_monitoring() -> None:
    """
    1) Event Monitoring
       전체 이벤트 또는 비정상 이벤트(!=Normal)를 확인
    """
    console.print("\n[1] Event Monitoring", style="bold blue")
    ns = choose_namespace()
    event_choice = Prompt.ask(
        "어떤 이벤트를 보시겠습니까? (1: 전체 이벤트(default), 2: 비정상 이벤트(!=Normal))",
        default="1",
    )
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 20): ")

    ns_option = f"-n {ns}" if ns else "-A"
    if event_choice == "2":
        cmd = f'watch -n2 "kubectl get events {ns_option} --field-selector type!=Normal --sort-by=".metadata.managedFields[].time" | tail -n {tail_num}"'
    else:
        cmd = f'watch -n2 "kubectl get events {ns_option} --sort-by=".metadata.managedFields[].time" | tail -n {tail_num}"'
    console.print(
        f"\n실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold"
    )
    os.system(cmd)


def view_restarted_container_logs() -> None:
    """
    2) Container Monitoring (재시작된 컨테이너 및 로그)
       최근 재시작된 컨테이너 목록에서 선택하여 이전 컨테이너의 로그 확인
    """
    console.print("\n[2] 재시작된 컨테이너 확인 및 로그 조회", style="bold blue")
    load_kube_config()
    v1 = client.CoreV1Api()
    ns = choose_namespace()
    pods = get_pods(v1, ns)
    if not pods:
        return

    restarted_containers = []
    for pod in pods:
        ns_pod = pod.metadata.namespace
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
                restarted_containers.append(
                    (ns_pod, p_name, c_status.name, finished_at)
                )
    restarted_containers.sort(key=lambda x: x[3], reverse=True)
    line_count = int(get_tail_lines("몇 개의 컨테이너를 표시할까요? (예: 20): "))
    displayed_containers = restarted_containers[:line_count]

    if not displayed_containers:
        print("최근 재시작된 컨테이너가 없습니다.")
        return

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("INDEX", style="bold green", width=5)
    table.add_column("Namespace")
    table.add_column("Pod")
    table.add_column("Container")
    table.add_column("LastTerminatedTime")
    for i, (ns_pod, p_name, c_name, fat) in enumerate(displayed_containers, start=1):
        table.add_row(str(i), ns_pod, p_name, c_name, fat.strftime("%Y-%m-%d %H:%M:%S"))
    console.print(
        f"\n=== 최근 재시작된 컨테이너 목록 (시간 기준, Top {line_count}) ===\n",
        style="bold green",
    )
    console.print(table)

    sel = Prompt.ask("\n로그를 볼 INDEX를 입력 (Q: 종료)", default="").strip()
    if sel.upper() == "Q" or not sel.isdigit():
        return
    idx = int(sel)
    if idx < 1 or idx > len(displayed_containers):
        console.print("인덱스 범위를 벗어났습니다.", style="bold red")
        return
    ns_pod, p_name, c_name, _ = displayed_containers[idx - 1]
    log_tail = Prompt.ask(
        "몇 줄의 로그를 확인할까요? (미입력 시 50줄)", default="50"
    ).strip()
    if not log_tail.isdigit():
        console.print(
            "입력하신 값이 숫자가 아닙니다. 50줄을 출력합니다.", style="bold red"
        )
        log_tail = "50"
    cmd = f"kubectl logs -n {ns_pod} -p {p_name} -c {c_name} --tail={log_tail}"
    print(f"\n실행 명령어: {cmd}\n")
    os.system(cmd)


def watch_pod_monitoring_by_creation() -> None:
    """
    3) Pod Monitoring (생성된 순서)
       Pod IP 및 Node Name을 선택적으로 표시하며, namespace 지정 가능
    """
    console.print("\n[3] Pod Monitoring (생성된 순서)", style="bold blue")
    ns = choose_namespace()
    extra = (
        Prompt.ask("Pod IP 및 Node Name을 표시할까요? (yes/no)", default="no")
        .strip()
        .lower()
    )
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 20): ")
    ns_option = f"-n {ns}" if ns else "-A"
    if extra.startswith("y"):
        cmd = f'watch -n2 "kubectl get po {ns_option} -o wide --sort-by=.metadata.creationTimestamp | tail -n {tail_num}"'
    else:
        cmd = f'watch -n2 "kubectl get po {ns_option} --sort-by=.metadata.creationTimestamp | tail -n {tail_num}"'
    console.print(
        f"\n실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold"
    )
    os.system(cmd)


def watch_non_running_pod() -> None:
    """
    4) Pod Monitoring (Running이 아닌 Pod)
       Pod IP 및 Node Name을 선택적으로 표시하며, namespace 지정 가능
    """
    console.print("\n[4] Pod Monitoring (Running이 아닌 Pod)", style="bold blue")
    ns = choose_namespace()
    extra = (
        Prompt.ask("Pod IP 및 Node Name을 표시할까요? (yes/no)", default="no")
        .strip()
        .lower()
    )
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 20): ")
    ns_option = f"-n {ns}" if ns else "-A"
    if extra.startswith("y"):
        cmd = f"watch -n2 \"kubectl get pods {ns_option} -o wide | grep -ivE ' Running' | tail -n {tail_num}\""
    else:
        cmd = f"watch -n2 \"kubectl get pods {ns_option} | grep -ivE ' Running' | tail -n {tail_num}\""
    console.print(
        f"\n실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold"
    )
    os.system(cmd)


def watch_pod_counts() -> None:
    """
    5) Pod Monitoring - 전체/정상/비정상 Pod 개수 출력 (2초 간격)
       namespace 지정 가능
    """
    console.print(
        "\n[5] Pod Monitoring (전체/정상/비정상 Pod 개수 출력)", style="bold blue"
    )
    ns = choose_namespace()
    console.print("\n(Ctrl+C로 중지 후 메뉴로 돌아갑니다.)", style="bold yellow")
    load_kube_config()
    v1 = client.CoreV1Api()
    try:
        while True:
            pods = get_pods(v1, ns)
            total = len(pods)
            normal = sum(
                1
                for p in pods
                if getattr(p.status, "phase", None) in ("Running", "Succeeded")
            )
            abnormal = total - normal
            console.clear()
            console.print("=== Pod Count Summary ===", style="bold blue")
            console.print(f"Total Pods    : [green]{total}[/green]")
            console.print(f"Normal Pods   : [green]{normal}[/green]")
            console.print(f"Abnormal Pods : [red]{abnormal}[/red]")
            time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n메뉴로 돌아갑니다...", style="bold yellow")


def watch_node_monitoring_by_creation() -> None:
    """
    6) Node Monitoring (생성된 순서)
       AZ, NodeGroup 정보를 함께 표시하며, 사용자가 특정 NodeGroup으로 필터링 가능
    """
    console.print("\n[6] Node Monitoring (생성된 순서)", style="bold blue")
    filter_choice = (
        Prompt.ask("특정 NodeGroup으로 필터링 하시겠습니까? (yes/no)", default="no")
        .strip()
        .lower()
    )
    if filter_choice.startswith("y"):
        filter_nodegroup = choose_node_group() or ""
    else:
        filter_nodegroup = ""
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 20): ")

    if filter_nodegroup:
        # label selector를 사용해서 정확히 일치하는 노드만 필터링
        cmd = (
            f'watch -n2 "kubectl get nodes -l {NODE_GROUP_LABEL}={filter_nodegroup} '
            f"-L topology.ebs.csi.aws.com/zone -L {NODE_GROUP_LABEL} "
            f'--sort-by=.metadata.creationTimestamp | tail -n {tail_num}"'
        )
    else:
        cmd_base = (
            f"kubectl get nodes -L topology.ebs.csi.aws.com/zone -L {NODE_GROUP_LABEL} "
            f"--sort-by=.metadata.creationTimestamp"
        )
        cmd = f'watch -n2 "{cmd_base} | tail -n {tail_num}"'

    console.print(
        f"\n실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold"
    )
    os.system(cmd)


def watch_unhealthy_nodes() -> None:
    """
    7) Node Monitoring (Unhealthy Node 확인)
       AZ, NodeGroup 정보를 함께 표시하며, 특정 NodeGroup 필터링 가능
    """
    console.print("\n[7] Node Monitoring (Unhealthy Node 확인)", style="bold blue")
    filter_choice = (
        Prompt.ask("특정 NodeGroup으로 필터링 하시겠습니까? (yes/no)", default="no")
        .strip()
        .lower()
    )
    if filter_choice.startswith("y"):
        filter_nodegroup = choose_node_group() or ""
    else:
        filter_nodegroup = ""
    tail_num = get_tail_lines("몇 줄씩 확인할까요? (예: 20): ")

    # label selector를 사용해서 정확한 노드 그룹으로 필터링
    if filter_nodegroup:
        cmd_base = f"kubectl get nodes -l {NODE_GROUP_LABEL}={filter_nodegroup} -L topology.ebs.csi.aws.com/zone -L {NODE_GROUP_LABEL} --sort-by=.metadata.creationTimestamp"
    else:
        cmd_base = f"kubectl get nodes -L topology.ebs.csi.aws.com/zone -L {NODE_GROUP_LABEL} --sort-by=.metadata.creationTimestamp"

    # 'Ready' 상태가 아닌 노드들만 표시
    cmd = f"watch -n2 \"{cmd_base} | grep -ivE ' Ready ' | tail -n {tail_num}\""
    console.print(f"실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold")
    os.system(cmd)


def watch_node_resources() -> None:
    """
    8) Node Monitoring (CPU/Memory 사용량 높은 순 정렬) 특정 NodeGroup 기준으로 필터링 가능
       NODE_GROUP_LABEL 변수 사용
    """
    console.print(
        "\n[8] Node Monitoring (CPU/Memory 사용량 높은 순 정렬)", style="bold blue"
    )
    while True:
        sort_key = Prompt.ask(
            "정렬 기준을 선택하세요 (1: CPU, 2: Memory)", choices=["1", "2"]
        )
        if sort_key == "1":
            sort_column = 3  # CPU 열 인덱스
            break
        elif sort_key == "2":
            sort_column = 5  # Memory 열 인덱스
            break
        else:
            console.print("잘못된 입력입니다. 다시 입력해주세요.", style="bold red")

    top_n = Prompt.ask("상위 몇 개 노드를 볼까요?", default="20")
    if not top_n.isdigit():
        console.print("숫자가 아닙니다. 기본값 20을 적용합니다.", style="bold red")
        top_n = "20"

    filter_choice = (
        Prompt.ask("특정 NodeGroup으로 필터링 하시겠습니까? (yes/no)", default="no")
        .strip()
        .lower()
    )
    filter_nodegroup = ""
    if filter_choice.startswith("y"):
        filter_nodegroup = choose_node_group() or ""

    # NodeGroup 필터링 시, label selector를 사용하도록 변경 (grep 대신)
    if filter_nodegroup:
        # NODE_GROUP_LABEL=<filter_nodegroup> 형태로 필터링
        cmd = f"kubectl top node -l {NODE_GROUP_LABEL}={filter_nodegroup} --no-headers"
    else:
        cmd = "kubectl top node --no-headers"

    # sort -k3 or -k5 -nr로 정렬 후, head로 상위 N개만
    cmd += f" | sort -k{sort_column} -nr 2>/dev/null | head -n {top_n}"
    cmd = f'watch -n1 "{cmd}"'
    console.print(f"실행 명령어: [green]{cmd}[/green]\n(Ctrl+C로 중지)\n", style="bold")
    os.system(cmd)


def main_menu() -> str:
    """
    메인 메뉴 출력
    """
    menu_table = Table(
        show_header=False,
        box=box.ROUNDED,
        padding=(0, 1),
        highlight=True,
        title="Kubernetes Monitoring Tool",
        title_style="bold yellow",
        title_justify="center",
    )
    menu_table.add_column("Option")
    menu_table.add_column("Description", style="white")

    menu_options = [
        ("1", "Event Monitoring (Normal, !=Normal)"),
        ("2", "Container Monitoring (재시작된 컨테이너 및 로그)"),
        ("3", "Pod Monitoring (생성된 순서) [옵션: Pod IP 및 Node Name 표시]"),
        ("4", "Pod Monitoring (Running이 아닌 Pod) [옵션: Pod IP 및 Node Name 표시]"),
        ("5", "Pod Monitoring (전체/정상/비정상 Pod 개수 출력)"),
        ("6", "Node Monitoring (생성된 순서) [AZ, NodeGroup 표시 및 필터링 가능]"),
        (
            "7",
            "Node Monitoring (Unhealthy Node 확인) [AZ, NodeGroup 표시 및 필터링 가능]",
        ),
        (
            "8",
            "Node Monitoring (CPU/Memory 사용량 높은 순 정렬) [NodeGroup 필터링 가능]",
        ),
        ("Q", "Quit"),
    ]

    for option, description in menu_options:
        if option == "Q":
            menu_table.add_row(f"[bold yellow]{option}[/bold yellow]", description)
        else:
            menu_table.add_row(f"[bold green]{option}[/bold green]", description)
    console.print(menu_table)
    return Prompt.ask("Select an option")


def main() -> None:
    """
    메인 함수 실행
    """
    try:
        while True:
            choice = main_menu()
            if choice == "1":
                watch_event_monitoring()
            elif choice == "2":
                view_restarted_container_logs()
            elif choice == "3":
                watch_pod_monitoring_by_creation()
            elif choice == "4":
                watch_non_running_pod()
            elif choice == "5":
                watch_pod_counts()
            elif choice == "6":
                watch_node_monitoring_by_creation()
            elif choice == "7":
                watch_unhealthy_nodes()
            elif choice == "8":
                watch_node_resources()
            elif choice.upper() == "Q":
                _exit_with_cleanup(0, "정상 종료합니다.", style="bold green")
            else:
                print("잘못된 입력입니다. 메뉴에 표시된 숫자 또는 Q를 입력하세요.")
    except KeyboardInterrupt:
        _exit_with_cleanup(130, "사용자 중단(Ctrl+C) 감지: 안전하게 종료합니다.")
    except EOFError:
        _exit_with_cleanup(
            0, "입력이 종료되었습니다(EOF). 정상 종료합니다.", style="bold green"
        )


if __name__ == "__main__":
    main()
