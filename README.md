# furiosa-uv-setup

FuriosaAI 드라이버/펌웨어/PE Runtime 설치를 **재현 가능**하게 자동화하는 CLI 도구입니다.  
Ubuntu/Debian에서 APT 레포 등록 → 커널 헤더 설치 → 드라이버/PE Runtime 설치 → 검증까지 한 번에 수행합니다.

---

## Prerequisites

- **OS**: Ubuntu 22.04 LTS (Jammy) 이상 또는 Debian Bookworm 이상  
- **Kernel**: Linux 6.3+  
- **권한**: 관리자 권한(`sudo`)  
- **네트워크**:  
  - `asia-northeast3-apt.pkg.dev` (Furiosa APT 서버)  
  - `packages.cloud.google.com` (APT 키)  
- **런타임**: Python 3.8+ 와 아래 중 하나
  - [uv](https://github.com/astral-sh/uv) (권장)  
  - pipx 또는 pip

필요 시 자동으로 설치되는 도구: `curl`, `gnupg`, `pciutils`

---

## 설치 방법

### A. uv 사용 (권장)

```bash
# uv 설치
curl -Ls https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 리포지토리 클론
git clone https://github.com/<YOUR_ORG>/furiosa-uv-setup.git
cd furiosa-uv-setup

# 의존성 동기화
uv sync
```

### B. pipx 사용

```bash
pipx install "git+https://github.com/<YOUR_ORG>/furiosa-uv-setup.git"
```

### C. pip 사용

```bash
pip install "git+https://github.com/<YOUR_ORG>/furiosa-uv-setup.git"
```

---

## 사용법

도움말:
```bash
furiosa-setup --help
```

단계별 실행:
```bash
furiosa-setup check-devices
furiosa-setup setup-apt
furiosa-setup install-prereqs
furiosa-setup install-furiosa
furiosa-setup verify
furiosa-setup upgrade-firmware   # (옵션)
```

한 번에:
```bash
furiosa-setup all
```

---

## Troubleshooting

- **명령어가 안 잡힐 때**:  
  - `uv sync` 또는 `pipx install .` 다시 실행  
  - 모듈 방식으로 실행: `uv run python -m furiosa_env.cli --help`

- **빌드 오류 발생 시**:  
  - `pyproject.toml` 구조 확인 (setuptools + src 레이아웃)  
  - 패키지 디렉터리: `src/furiosa_env`

- **장치 미검출 시**:  
  - `lspci -nn | grep FuriosaAI` 확인  
  - 커널 버전 6.3+ 인지 확인 (`uname -r`)  
  - BIOS/PCIe 슬롯 점검 후 재부팅

