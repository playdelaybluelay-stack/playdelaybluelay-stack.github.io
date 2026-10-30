---
title: "스타일 가이드: 본문 요소 점검용 원고"
date: 2026-10-29
draft: true
description: "레이아웃과 서체를 바꿀 때 렌더링을 확인하는 원고. 공개되지 않는다."
category: "개념"
tags: [점검]
---

구독 자격증명은 **수정하지 않은 CLI만** 다뤄야 한다. 그래서 러너를 Pod로 띄우지 않고 호스트에 두었고, 컨트롤 플레인의 `job-queue`를 outbound로 pull하게 했다. https://docs.example.com/very/long/path/that/keeps/going/without/any/break/at/all 같은 긴 주소가 섞여도 줄이 넘치지 않아야 한다.

## 목록과 인용

- 집으로 들어오는 포트는 `0`개를 목표로 한다.
- 로컬 모델은 Metal 가속 때문에 컨테이너 밖에서 돈다.
  - Docker Desktop의 VM 안에서는 GPU에 닿지 않는다.
  - 그래서 `ollama`는 호스트 프로세스다.

> 인용문은 이렇게 보인다. 출처를 밝히는 문장이 뒤따른다.

> [!note]
> 알림 문법이다. 제목 없이 쓰면 참고라는 제목이 붙는다.

> [!warning] 직접 단 제목
> 제목을 달면 그 제목을 쓴다.

## 소제목 리듬
### 바로 붙은 하위 소제목

문단과 문단 사이 간격을 본다. 두 번째 문단이 이어진다.

| 대안 | 평시 비용 | RTO |
|---|---|---|
| Backup & Restore | 1,200원 | 4시간 |
| Pilot Light | 3,400원 | 15분 |

## 코드

```hcl
# 러너가 큐에서 작업을 받는 경로
resource "kubernetes_network_policy" "runner_egress" {
  metadata { name = "runner-egress" }
  spec {
    pod_selector {}
    policy_types = ["Egress"]
    egress { ports { port = 5432 } }
  }
}
```

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 2   # 노드 장애 실험용
  template:
    spec:
      containers:
        - name: api
          image: ghcr.io/example/api:1.4.0
```

```console
$ kubectl get pods -n gateway
NAME                    READY   STATUS             RESTARTS
api-7c9d5b6f4-x2k8p     1/1     Running            0
queue-0                 0/1     CrashLoopBackOff   4
```

```diff
- maxConnections: 10
+ maxConnections: 50
  timeout: 30s
```

```go {hl_lines=[3]}
func route(t Task) Backend {
	if t.Interactive {
		return Subscription
	}
	return Local
}
```

```
언어 이름이 없는 펜스
```

## 마지막 섹션

목차 노선도가 나오려면 h2가 네 개 이상이어야 한다.
