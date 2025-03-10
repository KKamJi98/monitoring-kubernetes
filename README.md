# monitoring-kubernetes
monitoring kubernetes with python kubernetes lib

1. Event Monitoring - watch -n1 'kubectl get events -A --sort-by=".metadata.managedFields[].time" | tail -n (값은 사용자가 입력하도록)' 
2. Error pod catch - 가장 최근에 restart 된 컨테이너 10개, pod 이름과 함께 제공
3. Error Log catch - 가장 최근에 restart 된 컨테이너의 이전 에러로그 확인 (k logs -p 옵션과 tail -n 50 정도)
4. Pod Monitoring (생성된 순서대로) - watch -n1 ''kubectl get po -A --sort-by=.status.startTime | tail -n (값은 사용자 입력)''
5. Pod Monitoring (Running 상태가 아닌 Pod) - watch -n1 'kubectl get po -A --field-selector=status.phase!=Running -o wide | tail -n (값은 사용자가 입력)'
6. Pod Monitoring - 전체 Pod 개수, 정상 Pod 개수, 비정상 Pod 개수 출력
7. Node Monitoring (unhealthy node 확인) - watch -n1 'kubectl get no -L topology.ebs.csi.aws.com/zone -L node.kubernetes.io/instancegroup --sort-by=.metadata.creationTimestamp | grep -ivE " Ready" | tail -n (값은 사용자가 입력)'
8. Node Monitoring (리소스를 많이 사용하는 순서대로 모니터링) - 동일하게 tail사용. CPU 혹은 Memory 기준으로 정렬하는 것은 선택받기

