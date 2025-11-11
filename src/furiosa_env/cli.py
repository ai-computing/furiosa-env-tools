import os
import sys
import shlex
import subprocess
from pathlib import Path
import typer
from rich import print
from rich.panel import Panel

app = typer.Typer(help="FuriosaAI 환경(드라이버/펌웨어/PE Runtime/LLM) 설치를 uv 기반으로 자동화하는 CLI")

# ------------------------------
# Utils
# ------------------------------
def run(cmd: str, sudo: bool = False, check: bool = True):
    """
    Run a shell command. When sudo=True, elevate only the command (no nested shells).
    """
    if sudo:
        proc = subprocess.run(["sudo", "bash", "-lc", cmd], check=check)
    else:
        proc = subprocess.run(["bash", "-lc", cmd], check=check)
    return proc

def require_root_notice():
    print(Panel.fit("[bold yellow]일부 단계는 관리자 권한(sudo)이 필요합니다.[/bold yellow]"))

def os_codename() -> str:
    code = subprocess.check_output(["bash", "-lc", ". /etc/os-release && echo \"$VERSION_CODENAME\""], text=True).strip()
    return code

def warn_if_unsupported_os():
    code = os_codename()
    supported = {"jammy", "bookworm"}  # Ubuntu 22.04 / Debian Bookworm
    if code not in supported:
        print(Panel.fit(f"[bold red]경고:[/bold red] 현재 배포판 코드네임은 [bold]{code}[/bold] 입니다. 공식 요구사항은 Ubuntu 22.04(jammy) 또는 Debian bookworm 이상입니다. 계속 진행은 가능하지만 저장소/의존성 오류가 날 수 있어요."))

def py_ok_for_llm() -> bool:
    v = sys.version_info
    ok = (v.major == 3 and v.minor in (9, 10, 11, 12))
    if not ok:
        print(Panel.fit(f"[bold red]경고:[/bold red] LLM 요구사항은 Python 3.9~3.12 입니다. 현재 python {v.major}.{v.minor}"))
    return ok

def torch_version():
    try:
        import importlib
        spec = importlib.util.find_spec("torch")
        if not spec:
            return None
        import torch  # type: ignore
        return getattr(torch, "__version__", None)
    except Exception:
        return None

# ------------------------------
# Base prereqs
# ------------------------------
@app.command()
def check_requirements():
    """
    OS/커널/권한 등 최소 요구사항 점검(안내용).
    """
    print(Panel.fit("[bold]요구사항[/bold]\n- Ubuntu 22.04 LTS (또는 Debian Bookworm) 이상\n- Linux Kernel 6.3 이상\n- 관리자 권한"))
    run("uname -r && (lsb_release -a || cat /etc/os-release)", check=False)

@app.command()
def check_devices():
    """
    FuriosaAI PCIe 장치 인식 여부 확인. lspci 없으면 설치 후 갱신.
    """
    require_root_notice()
    # Try scan
    run("lspci -nn | grep -i FuriosaAI || true", check=False)
    print("[bold]lspci가 없다면 설치 중...[/bold]")
    run("apt update && apt install -y pciutils", sudo=True)
    run("update-pciids", sudo=True)
    print("[bold green]장치 스캔 결과:[/bold green]")
    run("lspci -nn | grep -i FuriosaAI || echo 'FuriosaAI 장치를 찾지 못했습니다.'", check=False)

@app.command()
def setup_apt():
    """
    FuriosaAI APT 레포 등록(서명키 + sources.list.d 항목).
    """
    require_root_notice()
    warn_if_unsupported_os()
    print("[bold]필수 패키지 설치 및 GPG 키 등록...[/bold]")
    run("apt update && apt install -y curl gnupg", sudo=True)

    # 키 저장 (직접 최종 위치에 저장)
    run("curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/cloud.google.gpg > /dev/null")

    # 코드네임/아키텍처를 파이썬에서 문자열로 확보
    code = os_codename()  # 예: jammy, bookworm, focal
    try:
        arch = subprocess.check_output(["bash", "-lc", "dpkg --print-architecture"], text=True).strip()
    except Exception:
        arch = "amd64"

    print(f"[bold]배포판 코드네임 확인:[/bold] {code}")
    apt_line = f"deb [arch={arch}] http://asia-northeast3-apt.pkg.dev/projects/furiosa-ai {code} main"

    # tee로 root 권한 쓰기
    run(f"echo {shlex.quote(apt_line)} | tee /etc/apt/sources.list.d/furiosa.list > /dev/null", sudo=True)
    print("[bold green]APT 레포 등록 완료[/bold green]")


@app.command()
def install_prereqs():
    """
    드라이버/PE Runtime 및 유틸리티 설치 전 공용 의존성 설치.
    """
    require_root_notice()
    run("apt update", sudo=True)

    # WSL2 환경 감지
    try:
        with open("/proc/version", "r") as f:
            proc_version = f.read()
        is_wsl = "microsoft" in proc_version.lower() or "wsl" in proc_version.lower()
    except Exception:
        is_wsl = False

    if is_wsl:
        print("[yellow]WSL2 환경 감지: 커널 헤더 패키지 설치를 건너뜁니다.[/yellow]")
        run("apt install -y build-essential", sudo=True)
    else:
        run("apt install -y build-essential linux-modules-extra-$(uname -r) linux-headers-$(uname -r)", sudo=True)

    print("[bold green]커널 헤더/모듈 등 설치 완료[/bold green]")

@app.command()
def install_furiosa():
    """
    Furiosa 드라이버, PE Runtime, furiosa-smi 설치.
    """
    require_root_notice()
    run("apt update", sudo=True)
    run("apt install -y furiosa-driver-rngd furiosa-pert-rngd furiosa-smi", sudo=True)
    print("[bold green]furiosa-driver-rngd / furiosa-pert-rngd / furiosa-smi 설치 완료[/bold green]")

@app.command()
def verify():
    """
    설치 후 NPU 장치 정보 확인.
    """
    require_root_notice()
    print("[bold]furiosa-smi info[/bold]")
    run("furiosa-smi info || echo 'furiosa-smi 실행 실패(설치/권한/장치 상태 확인 필요)'", sudo=True)

@app.command()
def upgrade_firmware():
    """
    펌웨어 툴/이미지 설치(자동 업그레이드 수행). 재부팅 필요할 수 있음.
    """
    require_root_notice()
    run("apt install -y furiosa-firmware-tools-rngd furiosa-firmware-image-rngd", sudo=True)
    print("[bold green]펌웨어 이미지 설치 완료. 장치별 3~5분 소요될 수 있으며, 재부팅이 필요할 수 있습니다.[/bold green]")

@app.command()
def all(include_llm: bool = typer.Option(True, help="LLM 컴파일러도 함께 설치")):
    """
    전체 자동 실행(장치 확인 → APT 등록 → 공용의존성 → 드라이버/Runtime 설치 → 검증 → LLM 컴파일러).
    """
    require_root_notice()
    check_devices()
    setup_apt()
    install_prereqs()
    install_furiosa()
    verify()

    if include_llm:
        print(Panel.fit("[bold cyan]LLM 컴파일러 설치 시작...[/bold cyan]"))
        install_llm(upgrade_torch=False, pip_index_url=None)

    print(Panel.fit("[bold green]모든 단계 완료! 필요 시 upgrade-firmware 명령으로 펌웨어 최신화하세요.[/bold green]"))

# ------------------------------
# Furiosa-LLM install & serve
# ------------------------------

@app.command("install-llm")
def install_llm(upgrade_torch: bool = typer.Option(False, help="PyTorch 2.5.1로 업그레이드 시도"),
                pip_index_url: str = typer.Option(None, help="대체 pip index URL (예: 사내 인덱스)")):
    """
    Furiosa-LLM 및 컴파일러 설치:
      - APT: furiosa-compiler, furiosa-compiler-dev
      - pip: furiosa-llm (+ 선택적으로 torch 2.5.1)
    """
    require_root_notice()
    warn_if_unsupported_os()
    py_ok_for_llm()

    # APT: compiler + dev tools
    print("[bold]FuriosaAI 컴파일러 및 개발 도구 설치 중...[/bold]")
    run("apt update", sudo=True)
    run("apt install -y furiosa-compiler furiosa-compiler-dev", sudo=True)

    # 설치 확인
    print("[bold]설치된 컴파일러 버전 확인...[/bold]")
    run("furiosa-compiler --version || echo 'furiosa-compiler 실행 실패'", sudo=False, check=False)

    # ---- pip 부트스트랩 (uv venv에는 pip가 없을 수 있음) ----

    run("python -m ensurepip --upgrade || true", check=False)
    # pip 존재 확인 후 미존재시 메시지

    chk = subprocess.run(["bash", "-lc", "python - <<'PY'\nimport importlib,sys\nprint(importlib.util.find_spec('pip') is not None)\nPY"], capture_output=True, text=True)
    if "True" not in chk.stdout:
        print(Panel.fit("[bold red]pip 모듈이 없습니다. uv pip로 대체 설치를 시도합니다.[/bold red]"))
        # uv가 PATH에 있어야 함

        run("uv pip install --upgrade pip setuptools wheel", check=True)
    else:
        pip_base = "python -m pip"
        extra_index = f" -i {shlex.quote(pip_index_url)}" if pip_index_url else ""
        run(f"{pip_base} install --upgrade pip setuptools wheel{extra_index}")

    # Torch (선택)

    if upgrade_torch:
        print("[bold]PyTorch 2.5.1 설치/업그레이드 시도...[/bold]")
        # pip 또는 uv pip 둘 다 커버

        run("python -m pip install --upgrade 'torch==2.5.1' || uv pip install --upgrade 'torch==2.5.1'")

    # LLM

    run("python -m pip install --upgrade furiosa-llm || uv pip install --upgrade furiosa-llm")
    tv = torch_version()
    print(Panel.fit(f"[bold green]Furiosa-LLM 설치 완료[/bold green]\nTorch: {tv or '미설치'}"))
@app.command("hf-login")
def hf_login(token: str = typer.Option(None, help="Hugging Face 토큰(옵션). 미지정 시 대화형 로그인")):
    """
    Hugging Face Hub 로그인 (일부 모델 실행 위해 필요).
    """
    run("python -m pip install --upgrade 'huggingface_hub[cli]'")
    if token:
        run(f"huggingface-cli login --token {shlex.quote(token)}")
    else:
        print("[bold yellow]토큰이 없으면 프롬프트가 뜹니다. 브라우저에서 발급 후 붙여넣기하세요.[/bold yellow]")
        run("huggingface-cli login")

@app.command()
def serve(model: str = typer.Argument("furiosa-ai/Llama-3.1-8B-Instruct-FP8"),
          devices: str = typer.Option("npu:0", "--devices", help='예: "npu:0"'),
          host: str = typer.Option("0.0.0.0", "--host"),
          port: int = typer.Option(8000, "--port")):
    """
    OpenAI 호환 서버 기동 (기본: 0.0.0.0:8000)
    """
    cmd = f'furiosa-llm serve {shlex.quote(model)} --devices {shlex.quote(devices)} --host {shlex.quote(host)} --port {port}'
    print(f"[bold]Launching:[/bold] {cmd}")
    run(cmd, sudo=False, check=True)

@app.command("write-examples")
def write_examples(directory: str = typer.Option("examples", help="예제 저장 경로")):
    """
    배치/스트리밍 예제 스크립트 생성.
    """
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)

    offline = d / "offline_batch.py"
    streaming = d / "streaming_infer.py"

    offline.write_text(
        """from furiosa_llm import LLM, SamplingParams

# Load the Llama 3.1 8B Instruct model
llm = LLM.load_artifact("furiosa-ai/Llama-3.1-8B-Instruct-FP8", devices="npu:0")

sampling_params = SamplingParams(min_tokens=10, top_p=0.3, top_k=100)

message = [{"role": "user", "content": "What is the capital of France?"}]
prompt = llm.tokenizer.apply_chat_template(message, tokenize=False)

response = llm.generate([prompt], sampling_params)
print(response[0].outputs[0].text)
""",
        encoding="utf-8",
    )

    streaming.write_text(
        """import asyncio
from furiosa_llm import LLM, SamplingParams

async def main():
    llm = LLM.load_artifact("furiosa-ai/Llama-3.1-8B-Instruct-FP8", devices="npu:0")
    sampling_params = SamplingParams(min_tokens=10, top_p=0.3, top_k=100)

    message = [{"role": "user", "content": "What is the capital of France?"}]
    prompt = llm.tokenizer.apply_chat_template(message, tokenize=False)

    async for output_txt in llm.stream_generate(prompt, sampling_params):
        print(output_txt, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
""",
        encoding="utf-8",
    )

    print(Panel.fit(f"[bold green]예제 생성 완료[/bold green]\n- {offline}\n- {streaming}\n실행:  uv run python {offline}"))

