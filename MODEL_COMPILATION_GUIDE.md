# FuriosaAI NPU를 위한 Llama-3.1-8B-Instruct 컴파일 가이드

이 가이드는 Llama-3.1-8B-Instruct 모델을 FuriosaAI NPU에서 실행하기 위한 준비와 컴파일 과정을 설명합니다.

## 📋 목차

1. [환경 설정](#환경-설정)
2. [모델 다운로드](#모델-다운로드)
3. [컴파일 준비](#컴파일-준비)
4. [모델 컴파일](#모델-컴파일)
5. [추가 리소스](#추가-리소스)

## 🔧 환경 설정

### 필수 요구사항

- **OS**: Ubuntu 22.04 LTS (Jammy) 이상 또는 Debian Bookworm 이상
- **Kernel**: Linux 6.3+
- **Python**: 3.8+
- **FuriosaAI SDK**: 2025.3.1 이상

### 설치된 패키지

이미 설치된 패키지들:
```bash
✅ FuriosaAI Driver (furiosa-driver-rngd 2025.3.1-4)
✅ FuriosaAI Runtime (furiosa-pert-rngd 2025.3.1-4)
✅ FuriosaAI SMI (furiosa-smi 2025.3.0-4)
✅ Transformers 4.57.1
✅ PyTorch 2.9.0
✅ Hugging Face Hub 0.36.0
```

## 📥 모델 다운로드

### 자동 다운로드 스크립트 사용

```bash
# 가상환경 활성화
export PATH="/root/.local/bin:$PATH"
source .venv/bin/activate

# 모델 다운로드 실행
python download_model.py
```

다운로드된 모델 위치: `./models/Llama-3.1-8B-Instruct/`

### 모델 정보

- **Model ID**: `furiosa-ai/Llama-3.1-8B-Instruct`
- **Size**: ~15GB
- **Architecture**: Llama 3.1
- **Parameters**: 8B
- **License**: Llama 3 Community License

## 🛠️ 컴파일 준비

### 1. 모델 구성 확인

```bash
python prepare_compilation.py
```

이 스크립트는 다음을 확인합니다:
- ✅ 모델 파일 존재 확인
- ✅ 토크나이저 로드
- ✅ 모델 configuration 검증
- ✅ 테스트 입력 생성

### 2. 컴파일 설정

`compile_for_furiosa.py`에서 다음 설정을 조정할 수 있습니다:

```python
compile_config = {
    "batch_size": 1,
    "max_seq_length": 2048,
    "precision": "fp16",  # or "int8" for quantization
    "target": "warboy",   # FuriosaAI NPU target
}
```

## 🚀 모델 컴파일

### FuriosaAI LLM SDK 사용

#### 옵션 A: CLI 방식

```bash
furiosa-llm compile \
  --model-path ./models/Llama-3.1-8B-Instruct \
  --output-path ./compiled_models/llama-3.1-8b-furiosa \
  --batch-size 1 \
  --max-seq-length 2048 \
  --target warboy
```

#### 옵션 B: Python API 방식

```python
from furiosa_llm import compile_model

compiled_model = compile_model(
    model_path='./models/Llama-3.1-8B-Instruct',
    output_path='./compiled_models/llama-3.1-8b-furiosa',
    batch_size=1,
    max_seq_length=2048,
    target='warboy'
)
```

### 컴파일 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `batch_size` | 배치 크기 | 1 |
| `max_seq_length` | 최대 시퀀스 길이 | 2048 |
| `precision` | 정밀도 (fp16/int8) | fp16 |
| `blockwise_compile` | 블록별 컴파일 | True |
| `kv_cache` | KV 캐시 활성화 | True |

### 양자화 (Quantization)

INT8 양자화로 모델 크기와 추론 속도 개선:

```python
compile_config = {
    "precision": "int8",
    "quantization": {
        "enabled": True,
        "method": "dynamic",  # "static" 또는 "dynamic"
    }
}
```

## 📁 프로젝트 구조

```
furiosa-env-tools/
├── models/
│   └── Llama-3.1-8B-Instruct/    # 다운로드된 모델
│       ├── config.json
│       ├── tokenizer.json
│       ├── model-*.safetensors
│       └── ...
├── compiled_models/               # 컴파일된 모델
│   └── llama-3.1-8b-furiosa/
│       └── compile_config.json
├── download_model.py              # 모델 다운로드 스크립트
├── prepare_compilation.py         # 컴파일 준비 스크립트
└── compile_for_furiosa.py        # 컴파일 템플릿 스크립트
```

## 🧪 테스트 및 검증

### 1. 컴파일 확인

```bash
# 컴파일된 모델 파일 확인
ls -lh compiled_models/llama-3.1-8b-furiosa/

# FuriosaAI SMI로 NPU 상태 확인
furiosa-smi
```

### 2. 추론 테스트

```python
from transformers import AutoTokenizer

# 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained("./models/Llama-3.1-8B-Instruct")

# 테스트 입력
text = "Hello, I am a language model"
inputs = tokenizer(text, return_tensors="pt")

# FuriosaAI 모델로 추론
# (실제 코드는 furiosa-llm API 사용)
```

## 📚 추가 리소스

### 공식 문서

- [FuriosaAI Developer Center](https://developer.furiosa.ai/)
- [FuriosaAI LLM Documentation](https://developer.furiosa.ai/latest/en/)
- [Optimum FuriosaAI](https://github.com/huggingface/optimum-furiosa)

### Hugging Face

- [Model Card](https://huggingface.co/furiosa-ai/Llama-3.1-8B-Instruct)
- [FuriosaAI Hub](https://huggingface.co/furiosa-ai)

### 참고사항

- 🔴 **FuriosaAI NPU 하드웨어**: 실제 컴파일 및 추론을 위해서는 FuriosaAI WARBOY NPU가 필요합니다
- 📦 **furiosa-llm 패키지**: 모델 컴파일을 위해 `furiosa-llm` 패키지 설치가 필요합니다
- 💾 **디스크 공간**: 원본 모델(~15GB) + 컴파일된 모델(~10-20GB) 공간 필요

## ⚠️ 문제 해결

### WSL2 환경

현재 WSL2 환경에서 실행 중입니다. WSL2에서는:
- ✅ 모델 다운로드 및 준비 가능
- ✅ 컴파일 스크립트 준비 가능
- ⚠️ 실제 NPU 하드웨어 접근 불가능
- ⚠️ 실제 컴파일 및 추론은 실제 하드웨어에서 수행 필요

### 디바이스 미검출

```bash
# NPU 장치 확인
furiosa-smi

# 장치가 없는 경우
# - 하드웨어 연결 확인
# - 드라이버 설치 확인
# - BIOS 설정 확인
```

## 🎯 다음 단계

1. ✅ 모델 다운로드 완료
2. ✅ 컴파일 스크립트 준비 완료
3. ⏳ FuriosaAI NPU 하드웨어에서 실제 컴파일
4. ⏳ 추론 성능 테스트
5. ⏳ 프로덕션 배포

---

**생성일**: 2025-11-11
**SDK 버전**: FuriosaAI SDK 2025.3.1
**모델**: Llama-3.1-8B-Instruct
