---
title: "about"
url: /about/
---

문제가 터진 뒤에 고치기보다, 터지기 전에 구조를 먼저 정해 두는 쪽을 좋아합니다. 메가존 클라우드의 SA 양성 과정에서 AWS 멀티리전 재해복구와 온프레미스 3-Tier 인프라를 직접 설계하고 구축했고, 지금은 회사에서 사내 영업관리 솔루션을 고도화하면서 개인적으로 [LLM 게이트웨이 플랫폼](/projects/llm-gateway/)을 만들고 있습니다. 무엇을 골랐고 왜 골랐는지, 무엇이 틀렸는지를 이 블로그에 남깁니다.

## 경력

**(주)에스티이지**, EBP사업부, 프로, 2026년 5월부터

자사 로우코드 플랫폼(JavaScript, JSP) 위에서 사내 영업관리 솔루션을 고도화합니다.

- 공용 화면을 고치지 않고 감싸는 구조로 범용 칸반 보기를 추가했습니다. 화면이 해 주던 검증을 서버 쪽에서 다시 채웠고, 같은 카드에 동시 요청 3건을 보내면 1건만 성공하도록 카드별 잠금을 걸어 검증했습니다.
- 2020년부터 쌓인 영업 이력 3,000여 건을 직접 세어 보고(77%가 500자 이하), 게시판형 기록을 유형, 일시, 할 일이 구조로 남는 타임라인으로 다시 설계했습니다. LLM 요약은 JSON으로 받고, 구조가 없으면 재요청하고 그래도 없으면 폴백하도록 했습니다.
- 금융감독원 공시 공개 API로 고객사 기업 정보 수기 입력을 회사명 입력 한 번으로 줄였고, 조회 기준표가 어긋나지 않게 정기 갱신 배치를 따로 만들었습니다.

## 프로젝트

### LLM 멀티 테넌트 게이트웨이

2026년 7월부터, 개인 프로젝트, 진행 중

매일 쓰는 개인 도구들의 LLM 호출을 맥미니의 로컬 모델과 구독 CLI로 나눠 보내는 쿠버네티스 플랫폼입니다. 설계 근거와 진행 상황은 [프로젝트 페이지](/projects/llm-gateway/)에 있습니다.

### AWS Pilot Light 멀티리전 재해복구

2025년 12월 ~ 2026년 2월, 5명 팀, 보안, 백업, DR 테스트 담당

가상 티켓팅 서비스(MAU 10,000)를 대상으로 서울, 도쿄 2개 리전의 Pilot Light DR을 설계하고 구축했습니다.

- 세 가지 DR 전략의 비용과 RTO를 비교표로 정리해 팀이 Pilot Light로 합의하게 했습니다.
- ALB마다 두던 WAF를 CloudFront 단일 진입점의 Custom WAF로 모아 공격 표면과 관리 지점을 줄였습니다.
- Terraform으로 2개 리전 약 50개 리소스를 코드로 관리하고, GitHub Actions OIDC로 저장소에서 장기 자격증명을 없앴습니다.
- Step Functions와 Slack 승인으로 DR 전환을 반자동화했습니다.
- 개인 고도화로 인증을 Cognito로 옮기고, DR 리전 User Pool에 사용자를 미리 복제해 재해 시 비밀번호 재설정 한 번으로 인증이 복구되게 했습니다.

결과: RTO 15분, RPO 5분 이내. 같은 조건의 Warm Standby 대비 평시 비용 98% 절감. 7일 운영 중 프랑스발 해킹 시도 23건 차단.

[저장소](https://github.com/playdelaybluelay-stack/aws-pilot-light-dr)

### 온프레미스 3-Tier 인프라

2025년 10월 ~ 11월(3주), 1인

VMware와 Vagrant로 VM 5대, 라우터 5대를 구성해 Web, WAS, DB, Shared 네 티어를 물리적으로 나눴습니다.

- 라우터를 2단으로 두어 외부와 내부 트래픽의 책임을 나누고, 티어별 ACL과 OSPF 동적 라우팅을 적용했습니다. 노드를 늘려도 정적 라우팅을 손으로 고칠 필요가 없습니다.
- HAProxy를 Primary와 Secondary로 이중화해 단일 장애점을 없앴고, Primary를 내렸을 때 Secondary가 자동으로 넘겨받는 것을 확인했습니다.
- MySQL을 비동기 Master, Replica로 복제해 읽기와 쓰기 경로를 나눴습니다. 복제 지연은 약 5분에서 안정됐습니다.

이후 같은 구성을 Docker Compose로 옮기고 Bash, Python으로 헬스체크와 장애 탐지를 자동화했습니다.

[저장소](https://github.com/playdelaybluelay-stack/onprem-3tier-infra), [Docker Compose 전환](https://github.com/playdelaybluelay-stack/3tier-docker-ops)

## 교육

- **메가존 클라우드 MSP 솔루션 아키텍트 양성 과정**, 2025년 7월 ~ 2026년 2월, 960시간
- **클라우드클럽 10기 Kubernetes Networking 스터디**, 2026년 9월부터 진행 중. CNI, Cilium과 eBPF, 다중 네트워크를 kind 클러스터에서 실습합니다.
- **한국외국어대학교** 프랑스·EU전공, 경영학 부전공, 2027년 2월 졸업 예정

## 기술

- **설계하고 구축해 본 것:** AWS(VPC, EC2, S3, ALB, SSM, Route 53, CloudFront, AWS Backup, DynamoDB, WAF와 Shield, CloudWatch, EventBridge, Lambda, Step Functions, Athena, ACM, Cognito, Bedrock), Terraform, GitHub Actions(OIDC), Linux, TCP/IP와 라우팅(OSPF, ACL), VMware, Vagrant
- **원리를 알고 다뤄 본 것:** GCP, Docker, Kubernetes, Python, MySQL 복제, PostgreSQL, HAProxy, Nginx, Wireshark

## 자격증

- AWS Certified Solutions Architect – Associate, 2026년 3월
- 정보처리기사 필기 합격, 2026년 3월
- OPIc 영어 IH, TOEIC 865
- FLEX 프랑스어 3B

## 연락

- [GitHub](https://github.com/playdelaybluelay-stack)
- [yebinhaan@gmail.com](mailto:yebinhaan@gmail.com)
