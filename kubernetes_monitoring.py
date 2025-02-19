#!/usr/bin/env python3

import sys
import os
from kubernetes import client, config
from tabulate import tabulate

def main_menu():
    print("\n=== Kubernetes Monitoring Tool ===")
    print("1) Watch Latest Events")
    print("2) Watch Recently Started Pods")
    print("3) Watch Other Resources (Pods/Deployments/DaemonSet/StatefulSet/Nodes)")
    print("Q) Quit")
    return input("Select an option: ").strip()

def resource_sub_menu():
    print("\n=== Resource Watch Menu ===")
    print("1) Pods")
    print("2) Deployments")
    print("3) DaemonSets")
    print("4) StatefulSets")
    print("5) Nodes")
    print("B) Back to main menu")
    return input("Select a resource to watch: ").strip()

def pick_namespace():
    """
    Let the user choose a namespace. 
    If the user types 'all', we'll use -A (all-namespaces).
    """
    core_v1 = client.CoreV1Api()
    ns_list = core_v1.list_namespace()
    
    table = [[ns.metadata.name] for ns in ns_list.items]
    print("\n[Available Namespaces]")
    print(tabulate(table, headers=["Namespace"], tablefmt="github"))
    
    ns = input("Select namespace (type 'all' for all-namespaces): ").strip()
    return ns

def watch_latest_events():
    """
    Watch the most recent events based on .lastTimestamp,
    showing only the last 40 lines in the terminal.
    """
    cmd = "watch -n1 \"kubectl get events -A --sort-by=.lastTimestamp | tail -n30\""
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_recently_started_pods():
    """
    Watch the most recently started Pods. 
    We'll pick 'all' or a specific namespace, then show 
    container images, node, restarts, sorted by startTime, 
    tailing the last 40 lines.
    """
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = (
            "watch -n1 \"kubectl get pods -A "
            "--sort-by=.status.startTime "
            "-o=custom-columns="
            + "'NAMESPACE:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase,"
            + "IMAGES:.spec.containers[*].image,NODE:.spec.nodeName,"
            + "RESTARTS:.status.containerStatuses[*].restartCount' "
            "| tail -n30\""
        )
    else:
        cmd = (
            f"watch -n1 \"kubectl get pods -n {ns} "
            "--sort-by=.status.startTime "
            "-o=custom-columns="
            + "'NAME:.metadata.name,PHASE:.status.phase,"
            + "IMAGES:.spec.containers[*].image,NODE:.spec.nodeName,"
            + "RESTARTS:.status.containerStatuses[*].restartCount' "
            "| tail -n30\""
        )
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_pods():
    """
    Watch pods in a specific namespace or all, with container images and node info.
    """
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = (
            "watch -n1 \"kubectl get pods -A "
            "-o=custom-columns="
            + "'NAMESPACE:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase,"
            + "IMAGES:.spec.containers[*].image,NODE:.spec.nodeName,"
            + "RESTARTS:.status.containerStatuses[*].restartCount'\""
        )
    else:
        cmd = (
            f"watch -n1 \"kubectl get pods -n {ns} "
            "-o=custom-columns="
            + "'NAME:.metadata.name,PHASE:.status.phase,"
            + "IMAGES:.spec.containers[*].image,NODE:.spec.nodeName,"
            + "RESTARTS:.status.containerStatuses[*].restartCount'\""
        )
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_deployments():
    """
    Watch deployments (namespace or all).
    We'll show images, node is not directly applicable, but we can show replicas.
    """
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = (
            "watch -n1 \"kubectl get deployments -A "
            "-o=custom-columns="
            + "'NAMESPACE:.metadata.namespace,NAME:.metadata.name,"
            + "READY:.status.readyReplicas,REPLICAS:.spec.replicas,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    else:
        cmd = (
            f"watch -n1 \"kubectl get deployments -n {ns} "
            "-o=custom-columns="
            + "'NAME:.metadata.name,"
            + "READY:.status.readyReplicas,REPLICAS:.spec.replicas,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_daemonsets():
    """
    Watch DaemonSets. We'll show images, desired/ready, etc.
    """
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = (
            "watch -n1 \"kubectl get ds -A "
            "-o=custom-columns="
            + "'NAMESPACE:.metadata.namespace,NAME:.metadata.name,"
            + "DESIRED:.status.desiredNumberScheduled,READY:.status.numberReady,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    else:
        cmd = (
            f"watch -n1 \"kubectl get ds -n {ns} "
            "-o=custom-columns="
            + "'NAME:.metadata.name,"
            + "DESIRED:.status.desiredNumberScheduled,READY:.status.numberReady,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_statefulsets():
    """
    Watch StatefulSets with images, replicas info.
    """
    ns = pick_namespace()
    if ns.lower() == "all":
        cmd = (
            "watch -n1 \"kubectl get sts -A "
            "-o=custom-columns="
            + "'NAMESPACE:.metadata.namespace,NAME:.metadata.name,"
            + "READY:.status.readyReplicas,REPLICAS:.spec.replicas,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    else:
        cmd = (
            f"watch -n1 \"kubectl get sts -n {ns} "
            "-o=custom-columns="
            + "'NAME:.metadata.name,"
            + "READY:.status.readyReplicas,REPLICAS:.spec.replicas,"
            + "IMAGES:.spec.template.spec.containers[*].image'\""
        )
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def watch_nodes():
    """
    Watch nodes. We'll just use -o wide for a quick overview.
    """
    cmd = 'watch -n1 "kubectl get nodes -o wide"'
    print(f"\nExecuting: {cmd}\nPress Ctrl+C to stop.")
    os.system(cmd)

def resource_menu():
    """
    Sub menu for 'Watch Other Resources'.
    """
    while True:
        choice = resource_sub_menu()
        if choice == "1":
            watch_pods()
        elif choice == "2":
            watch_deployments()
        elif choice == "3":
            watch_daemonsets()
        elif choice == "4":
            watch_statefulsets()
        elif choice == "5":
            watch_nodes()
        elif choice.upper() == "B":
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    # Load local kubeconfig (similar to `kubectl`)
    config.load_kube_config()

    while True:
        choice = main_menu()
        if choice == "1":
            watch_latest_events()
        elif choice == "2":
            watch_recently_started_pods()
        elif choice == "3":
            resource_menu()
        elif choice.lower() == "q":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
