# 전차로 GO! 신칸센 EX 산요 신칸센편 (Wii 일본판 RG4JC0) 한글 패치

> **내려받기:** [릴리즈 페이지](https://github.com/hospi0/densha-sanyo-kr-patch/releases/latest) — 최신 v0.9. 적용 방법·원본 MD5 는 패치 묶음의 readme 에 있습니다.
>
> 이 저장소에는 도구·번역 텍스트·작업 문서만 있습니다(ROM·빌드 결과물 없음).

## 내용

- 이 게임의 화면 글자는 글꼴이 아니라 전부 TPL 그림입니다. DAT 안 TPL(C4·C8·I4·CMPR·RGBA8)을 풀고(`tools/tpl.py`) 한글로 다시 그려 같은 크기·팔레트로 넣었습니다(`tools/build_gfx.py`).
- 메뉴, 안내, 입문편, 말풍선, 판정·평가, 자료관 설명, 저장 화면, 이름 입력판(한글 음절 160자), 제목 로고(`tools/logo_kr.py`)
- Wii 암호화 디스크 제자리 패치(`tools/wiiiso.py`, `tools/isopatch.py`)

## 빌드 순서

```
python tools/build_gfx.py
python tools/build_iso.py
python tools/make_dist.py
```
