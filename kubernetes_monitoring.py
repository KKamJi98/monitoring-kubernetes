#!/usr/bin/env python3

import sys
import os
from kubernetes import client, config, watch
from tabulate import tabulate

def main_menu():
    print("\n=== Kubernetes Monitoring Tool ===")
    print("1) Watch Events")
    print("2) List-up")
    print("3) 가장 최근에 재시작한 Pod 찾기")
    print("Q) Quit")
    return input("Select an option: ").strip()

def sub_menu_list_up():
    print("\n=== List-up Menu ===")
    print("1) List Nodes")
    print("2) List Pods")
    print("3) List Deployments")
    print("4) List DaemonSets")
    print("5) List StatefulSets")
    print("B) Back to main menu")
    return input("Select a resource to list: ").strip()

def pick_namespace():
    """사용자가 네임스페이스를 고르도록 안내. 'all' 입력 시 All Namespaces."""
    core_v1 = client.CoreV1Api()
    ns_list = core_v1.list_namespace()
    table = []
    for ns in ns_list.items:
        table.append([ns.metadata.name])
    print("\n[Available Namespaces]")
    print(tabulate(table, headers=["Namespace"], tablefmt="github"))

    ns = input("Select namespace (type 'all' for all-namespaces): ").strip()
    return ns

def watch_events():
    """Event를 실시간으로 감시. (Namespace, 리소스 이름, Reason, 시간, 메시지 등 표시)"""
    core_v1 = client.CoreV1Api()
    w = watch.Watch()
    print("\n[Watching Events - press Ctrl+C to stop]")
    try:
        for event in w.stream(core_v1.list_event_for_all_namespaces):
            evt_obj = event["object"]
            ns = evt_obj.metadata.namespace or "-"
            name = evt_obj.involved_object.name or "-"
            reason = evt_obj.reason or "-"
            message = evt_obj.message or "-"
            # 시간은 metadata.creationTimestamp 또는 lastTimestamp 등을 쓸 수 있다.
            ts = str(evt_obj.last_timestamp or evt_obj.event_time or evt_obj.metadata.creation_timestamp)

            print(f"* NS=[{ns}] Name=[{name}] Reason=[{reason}] Time=[{ts}] Msg=[{message}]")

    except KeyboardInterrupt:
        print("\nStopped watching events.")

def list_nodes():
    apps_v1 = client.CoreV1Api()
    nodes = apps_v1.list_node()
    table = []
    for node in nodes.items:
        name = node.metadata.name
        alloc_cpu = node.status.allocatable.get("cpu","?")
        alloc_mem = node.status.allocatable.get("memory","?")
        table.append([name, alloc_cpu, alloc_mem])
    print("\n[Nodes]")
    print(tabulate(table, headers=["Name", "CPU", "Memory"], tablefmt="github"))

def list_pods(namespace=None):
    core_v1 = client.CoreV1Api()
    if namespace == "all":
        pods = core_v1.list_pod_for_all_namespaces()
    else:
        pods = core_v1.list_namespaced_pod(namespace)

    table = []
    for pod in pods.items:
        ns = pod.metadata.namespace
        name = pod.metadata.name
        phase = pod.status.phase
        restarts = 0
        if pod.status.container_statuses:
            restarts = sum(cs.restart_count for cs in pod.status.container_statuses)
        table.append([ns, name, phase, restarts])

    print("\n[Pods]")
    print(tabulate(table, headers=["Namespace", "Pod Name", "Phase", "Restarts"], tablefmt="github"))

def list_deployments(namespace=None):
    apps_v1 = client.AppsV1Api()
    if namespace == "all":
        deps = apps_v1.list_deployment_for_all_namespaces()
    else:
        deps = apps_v1.list_namespaced_deployment(namespace)

    table = []
    for d in deps.items:
        ns = d.metadata.namespace
        name = d.metadata.name
        replicas = f"{d.status.ready_replicas or 0}/{d.spec.replicas}"
        table.append([ns, name, replicas])
    print("\n[Deployments]")
    print(tabulate(table, headers=["Namespace", "Name", "Ready/Total"], tablefmt="github"))

def list_daemonsets(namespace=None):
    apps_v1 = client.AppsV1Api()
    if namespace == "all":
        dss = apps_v1.list_daemon_set_for_all_namespaces()
    else:
        dss = apps_v1.list_namespaced_daemon_set(namespace)

    table = []
    for ds in dss.items:
        ns = ds.metadata.namespace
        name = ds.metadata.name
        desired = ds.status.desired_number_scheduled or 0
        ready = ds.status.number_ready or 0
        table.append([ns, name, f"{ready}/{desired}"])
    print("\n[DaemonSets]")
    print(tabulate(table, headers=["Namespace", "Name", "Ready/Desired"], tablefmt="github"))

def list_statefulsets(namespace=None):
    apps_v1 = client.AppsV1Api()
    if namespace == "all":
        sts_list = apps_v1.list_stateful_set_for_all_namespaces()
    else:
        sts_list = apps_v1.list_namespaced_stateful_set(namespace)

    table = []
    for sts in sts_list.items:
        ns = sts.metadata.namespace
        name = sts.metadata.name
        replicas = f"{sts.status.ready_replicas or 0}/{sts.spec.replicas}"
        table.append([ns, name, replicas])
    print("\n[StatefulSets]")
    print(tabulate(table, headers=["Namespace", "Name", "Ready/Total"], tablefmt="github"))

def show_recent_restarted_pods():
    """
    '가장 최근에 재시작한 pod 찾기' 기능.
    - 사용자에게 namespace 물어보고, "all"이면 --all-namespaces.
    - watch -n1 'kubectl get pods ... --sort-by=.status.startTime | tail -n30'
    """
    #ns = input("Select namespace (or 'all' for all-namespaces): ").strip()
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = "watch -n1 'kubectl get pods --all-namespaces --sort-by=.status.startTime | tail -n30'"
    else:
        cmd = f"watch -n1 'kubectl get pods -n {ns} --sort-by=.status.startTime | tail -n30'"

    print(f"\nRunning command: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def list_up_menu():
    """2번 List-up 메뉴 흐름"""
    while True:
        sub_choice = sub_menu_list_up()
        if sub_choice == "1":
            # List Nodes (namespace 상관없이 노드자원은 global)
            list_nodes()
        elif sub_choice == "2":
            # List Pods
            ns = pick_namespace()
            list_pods(ns)
        elif sub_choice == "3":
            # List Deployments
            ns = pick_namespace()
            list_deployments(ns)
        elif sub_choice == "4":
            # List DaemonSets
            ns = pick_namespace()
            list_daemonsets(ns)
        elif sub_choice == "5":
            # List StatefulSets
            ns = pick_namespace()
            list_statefulsets(ns)
        elif sub_choice.upper() == "B":
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    # Load kubeconfig from local (similar to 'kubectl' style)
    config.load_kube_config()

    while True:
        choice = main_menu()
        if choice == "1":
            watch_events()
        elif choice == "2":
            list_up_menu()
        elif choice == "3":
            show_recent_restarted_pods()
        elif choice.lower() == "q":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

