<img width="1036" height="1025" alt="image" src="https://github.com/user-attachments/assets/b2449869-2d1e-4445-b957-62c6b83acbdc" />


# Databricks-Airflow Projects

Apache Airflow, Kubernetes, Helm, Kind, AWS ECR를 사용해 데이터 파이프라인을 로컬과 컨테이너 환경에서 운영하는 프로젝트입니다.  
Airflow DAG로 데이터 적재를 오케스트레이션하고, Databricks 작업을 트리거하며, Docker 이미지 빌드와 ECR 배포 흐름까지 연결했습니다.

## Overview

이 프로젝트는 다음 목표를 중심으로 구성했습니다.

- Airflow 기반 데이터 워크플로 오케스트레이션
- KubernetesExecutor를 사용한 태스크 단위 Pod 실행
- Helm Chart 기반 Airflow 배포 자동화
- Docker 이미지 빌드 및 AWS ECR 푸시
- Databricks 워크플로 연계
- 로그 persistence 및 운영 트러블슈팅 정리

## Architecture

주요 구성은 아래와 같습니다.

- `Airflow`
  - DAG 스케줄링 및 태스크 실행 관리
  - `KubernetesExecutor` 기반으로 태스크별 Pod 생성
- `Kubernetes / Kind`
  - 로컬 클러스터 환경 구성
  - PV/PVC를 사용한 로그 persistence 실험
- `Helm`
  - Airflow 설치 및 설정 관리
- `AWS ECR`
  - 커스텀 Airflow 이미지 저장소
- `Databricks`
  - Airflow DAG에서 Databricks Job 트리거
- `Notebook`
  - Bronze / Silver / Gold 계층 데이터 처리 코드 관리

## Key Features

- 공개 GitHub 저장소에서 `gitSync`로 DAG 동기화
- Airflow 커스텀 이미지 구성
- ECR 기반 이미지 배포 워크플로
- 로컬 Kind 테스트용 설치 스크립트와 ECR 설치 스크립트 분리
- Airflow 로그 persistence 구성
- Secret 파일을 템플릿과 실제 값으로 분리해 Git 노출 방지

## Project Structure

```text
.
├── CICD/
│   └── Dockerfile
├── Dags/
│   ├── example_dag.py
│   ├── produce_data_assets.py
│   └── trigger_databricks_workflow_dag.py
├── chart/
│   ├── values-override.yaml
│   └── values-override-persistence.yaml
├── k8s/
│   ├── clusters/
│   ├── secrets/
│   └── volumes/
├── notebooks/
├── .github/workflows/
│   └── cicd.yaml
├── install_airflow.sh
├── install_airflow_with_persistence.sh
├── install_airflow_with_ecr.sh
└── upgrade_airflow.sh
```

## Main DAGs

### `example_dag`

- Airflow 기본 동작 확인용 예제 DAG
- `hello_world` -> `goodbye_world_Bye` 순서로 실행

### `produce_data_assets`

- StackExchange 데이터를 다운로드 및 압축 해제
- S3에 원천 데이터 적재
- asset 기반 스케줄링 실험

### `trigger_databricks_workflow_dag`

- Airflow에서 Databricks Job 실행
- upstream asset 완료 후 Databricks workflow trigger

## Deployment Flows

### 1. Local Kind Install

`install_airflow.sh`

- 로컬 Docker 이미지 빌드
- Kind 클러스터에 이미지 적재
- Helm으로 Airflow 설치

### 2. Persistence Install

`install_airflow_with_persistence.sh`

- PV/PVC를 사용해 Airflow 로그 persistence 적용
- 로그 보존 실험 및 UI 로그 확인 환경 구성

### 3. ECR-based Install

`install_airflow_with_ecr.sh`

- ECR에서 최신 Airflow 이미지 태그 조회
- `imagePullSecret` 생성
- private ECR 이미지를 사용하는 Helm 설치 수행

## CI/CD

GitHub Actions workflow는 `main` 브랜치 push 시 아래 작업을 수행합니다.

- AWS 자격 증명 설정
- Amazon ECR 로그인
- Docker 이미지 빌드
- ECR에 커스텀 Airflow 이미지 push

관련 파일:

- `.github/workflows/cicd.yaml`

## Security Handling

Git에 실제 Secret 값을 올리지 않도록 아래 방식으로 관리했습니다.

- `k8s/secrets/git-secrets.example.yaml`
  - 템플릿 파일
- `k8s/secrets/git-secrets.yaml`
  - 로컬에서만 생성하는 실제 Secret 파일
- `.gitignore`
  - 실제 secret 파일 제외

이를 통해 GitHub push protection 및 secret scanning 이슈를 방지했습니다.

## Troubleshooting Highlights

### 1. DAG가 Airflow UI에 보이지 않던 문제

원인:

- `gitSync.subPath`가 실제 디렉터리 `Dags`와 대소문자가 맞지 않았음
- DAG 코드 내 함수명 불일치로 파싱 실패 발생

조치:

- `subPath: "Dags"`로 수정
- DAG 함수명 참조 수정

### 2. Airflow UI에서 task 로그가 보이지 않던 문제

원인:

- `KubernetesExecutor` 환경에서 task Pod가 종료 후 삭제됨
- UI는 삭제된 Pod의 로그를 다시 읽으려다 실패

조치:

- `kubectl logs`, scheduler 로그로 직접 확인
- persistence 및 remote logging 방향 검토

### 3. Git push가 secret 문제로 막히던 이슈

원인:

- 실제 Git 토큰이 Secret manifest에 포함된 상태로 커밋됨

조치:

- 예제 파일과 실제 파일 분리
- Git 추적 대상에서 실제 secret 제거

### 4. ECR 이미지 pull 실패 가능성

원인:

- private ECR 이미지 사용 시 `imagePullSecret` 미설정

조치:

- 설치 스크립트에서 `docker-registry` secret 생성
- Helm install 시 `imagePullSecrets` 연결

## Tech Stack

- Python
- Apache Airflow
- Kubernetes
- Helm
- Kind
- Docker
- AWS ECR
- Databricks
- GitHub Actions

## What I Learned

- Airflow를 KubernetesExecutor로 운영할 때 task Pod 생명주기와 로그 조회 방식
- Helm values와 실제 클러스터 동작 간 차이를 디버깅하는 방법
- Secret을 Git에 안전하게 관리하는 방법
- ECR, GitHub Actions, Helm 설치 스크립트를 연결한 배포 흐름 설계
- 로컬 테스트 환경과 배포 환경을 분리해서 관리하는 방법

## Future Improvements

- remote logging을 S3로 연동해 UI 로그 조회 안정성 개선
- Helm upgrade 자동화 추가
- ECR push 이후 자동 배포 파이프라인 완성
- Databricks 및 S3 연결 설정 문서화 강화
