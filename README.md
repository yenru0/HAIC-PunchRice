# HAIC-PunchRice

주먹밥 팀을 위한 레포

## 구성

`main.py`가 진짜 중요함
`dist.py`는 `main.py`와 `data/**`를 자동으로 배포 ZIP 아카이브 형태로 압축해주는 스크립트

## `models/*.py`

다음이 필요함
* `DotsBoxModel`을 상속하는 클래스
  * `init`과 `run`을 구현해야함
  * `from models.DotsBoxModel import DotsBoxModel` 등 `DotsBoxModel`을 import하는 구문으로 쓰면 됨

## 실행 예시

`./dist.py V4b`
