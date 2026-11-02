# -*- coding: utf-8 -*-
r"""배포 묶음 dist/DenshaSanyo_KR_v0.9/ : ISO xdelta + xdelta.exe + readme.txt(CP949) + bat(CP949)"""
import hashlib, os, shutil, subprocess, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); VER = 'v0.9'; NAME = 'DenshaSanyo_KR_' + VER
X = os.path.join('C:' + os.sep, 'claude', 'utils', 'xdelta.exe'); SRC = os.path.join(ROOT, 'work', 'game.iso'); OUT = os.path.join(ROOT, 'dist', 'build', 'RG4JC0_KR.iso')
B = "Densha de Go! Shinkansen EX - San'you Shinkansen Hen (Japan).iso"


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest().upper()


R_ = """전차로 GO! 신칸센 EX 산요 신칸센편 (Wii 일본판 RG4JC0) 한글 패치 {v}
============================================================

원본 ISO 에 패치하시면 됩니다. RVZ 는 Dolphin 에서 ISO 로 변환해 쓰세요.

원본md5 : {o}
패치md5 : {d}


[ 적용 방법 ]

  1) 원본 ISO 를 이 폴더에 복사하고 이름을 다음으로 바꾸세요
       "{b}"
  2) 한글패치_적용.bat 실행 → 이름 끝에 [KR] 이 붙은 ISO 가 만들어집니다


[ 바뀌는 것 ]

  메뉴, 안내, 입문편, 말풍선, 판정·평가, 자료관 설명, 저장 화면, 이름 입력판(한글 음절 160자)


[ 알려진 점 ]

  - 시험판입니다. 전체 플레이 검증을 마치지 않았습니다.
  - 음성, 동영상, 3D 풍경 속 간판·터널 이름판, 스태프 그림은 원본 그대로입니다.
  - 서명을 다시 맞춘 이미지라 실기 Wii 는 별도 로더가 필요합니다.
"""
BAT = """@echo off
chcp 949 >nul
if not exist "%~dp0{b}" (
  echo   [오류] 원본 ISO 를 이 폴더에 넣어 주세요 - readme 참고.
  pause ^& exit /b 1
)
"%~dp0xdelta.exe" -d -f -s "%~dp0{b}" "%~dp0{p}" "%~dp0{k}"
if errorlevel 1 (
  echo   [오류] 패치 실패 - 원본이 다를 수 있습니다 - readme 의 원본md5 확인.
  pause ^& exit /b 1
)
echo   완료
pause
"""
d = os.path.join(ROOT, 'dist', NAME); shutil.rmtree(d, ignore_errors=True); os.makedirs(d); P = NAME + '.xdelta'; pp = os.path.join(d, P)
subprocess.run([X, '-e', '-9', '-B', '536870912', '-f', '-s', SRC, OUT, pp], check=True); c = os.path.join(d, '_c.bin'); subprocess.run([X, '-d', '-f', '-s', SRC, pp, c], check=True)
o, w, g = md5(SRC), md5(OUT), md5(c); os.remove(c); assert g == w
shutil.copy2(X, os.path.join(d, 'xdelta.exe')); kb = B[:-4] + ' [KR].iso'
open(os.path.join(d, 'readme.txt'), 'wb').write(R_.format(v=VER, o=o, d=w, b=B).replace('\n', '\r\n').encode('cp949'))
open(os.path.join(d, '한글패치_적용.bat'), 'wb').write(BAT.replace('^&', '&').format(b=B, p=P, k=kb).replace('\n', '\r\n').encode('cp949'))
z = os.path.join(ROOT, 'dist', NAME + '.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as f:
    for x in sorted(os.listdir(d)): f.write(os.path.join(d, x), NAME + '/' + x)
print('원본', o, '패치', w, 'xdelta', os.path.getsize(pp), 'zip', os.path.getsize(z), md5(z))
