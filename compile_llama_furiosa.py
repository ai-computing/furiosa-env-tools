#!/usr/bin/env python3
"""
FuriosaAI NPU용 Llama-3.1-8B-Instruct 모델 컴파일

이 스크립트는 furiosa_llm.artifact.builder를 사용하여
Llama 모델을 FuriosaAI WARBOY NPU에서 실행 가능한 형태로 컴파일합니다.
"""

from furiosa_llm.artifact.builder import ArtifactBuilder
from pathlib import Path
import sys
import os

# 오프라인 모드 활성화 (Hugging Face Hub 접근 차단)
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# 출력 디렉토리 설정
OUTPUT_DIR = Path("./Output-Llama-3.1-8B-Instruct")

print("=" * 70)
print("🚀 FuriosaAI Llama-3.1-8B-Instruct Compilation")
print("=" * 70)

# Prefill 버킷: (batch_size, sequence_length)
# 다양한 입력 크기에 최적화된 모델 생성
RELEASE_PREFILL_BUCKETS = [
    (1, 256), (1, 320), (1, 384), (1, 512), (1, 640),
    (1, 768), (1, 1024), (2, 1024), (4, 1024),
]

# Decode 버킷: (batch_size, kv_cache_length)
# 디코딩 단계에서 사용할 KV 캐시 크기 설정
RELEASE_DECODE_BUCKETS = [
    # 1K context
    *[(1, 1024),  (4, 1024),   (8, 1024), (16, 1024), (32, 1024), (64, 1024)],
    # 2K context
    *[(1, 2048),  (4, 2048),   (8, 2048), (16, 2048), (32, 2048)],
    # 4K context
    *[(1, 4096),  (4, 4096),   (8, 4096), (16, 4096), (32, 4096)],
    # 8K context
    *[(1, 8192),  (4, 8192),   (8, 8192), (16, 8192)],
    # 16K context
    *[(1, 16384), (4, 16384), (8, 16384)],
    # 32K context
    *[(1, 32768), (4, 32768)],
]

print("\n📋 Compilation Configuration:")
print(f"   Model: meta-llama/Llama-3.1-8B-Instruct")
print(f"   Tensor Parallel Size: 8")
print(f"   Max Sequence Length: 32,768 tokens")
print(f"   Prefill Chunk Size: 8,192 tokens")
print(f"   Output Directory: {OUTPUT_DIR.absolute()}")
print(f"   Prefill Buckets: {len(RELEASE_PREFILL_BUCKETS)} configurations")
print(f"   Decode Buckets: {len(RELEASE_DECODE_BUCKETS)} configurations")

print("\n🔍 Prefill Buckets (batch, seq_len):")
for i, (bs, sl) in enumerate(RELEASE_PREFILL_BUCKETS, 1):
    print(f"   {i}. Batch={bs}, SeqLen={sl}")

print("\n🔍 Decode Buckets (first 10):")
for i, (bs, kv) in enumerate(RELEASE_DECODE_BUCKETS[:10], 1):
    print(f"   {i}. Batch={bs}, KV_Cache={kv}")
print(f"   ... and {len(RELEASE_DECODE_BUCKETS) - 10} more configurations")

print("\n" + "=" * 70)
print("⚙️  Initializing ArtifactBuilder...")
print("=" * 70)

try:
    # 로컬 모델 경로 확인 (원본 HF 모델)
    LOCAL_MODEL_PATH = Path("./models/Llama-3.1-8B-Instruct-original").resolve()

    # 백업된 컴파일 모델 경로도 확인
    COMPILED_BACKUP = Path("./models/Llama-3.1-8B-Instruct-compiled-backup").resolve()

    if LOCAL_MODEL_PATH.exists():
        print(f"   Using local model: {LOCAL_MODEL_PATH}")
        print(f"   Offline mode: Enabled (no Hugging Face connection)")
        model_path = str(LOCAL_MODEL_PATH)
    else:
        print(f"   ❌ Error: Original model not found at {LOCAL_MODEL_PATH}")
        print("   Please download the model first:")
        print("   $ python3 download_model.py")
        print()
        if COMPILED_BACKUP.exists():
            print(f"   ℹ️  Note: Pre-compiled model is backed up at {COMPILED_BACKUP}")
            print("      If you want to use the pre-compiled model without recompiling,")
            print("      you can use it directly for inference.")
        sys.exit(1)

    # ArtifactBuilder 초기화
    builder = ArtifactBuilder(
        model_id_or_path=model_path,
        artifact_name="Llama-3.1-8B-Instruct-FuriosaAI",
        tensor_parallel_size=8,              # 8개 NPU로 병렬 처리
        prefill_buckets=RELEASE_PREFILL_BUCKETS,
        decode_buckets=RELEASE_DECODE_BUCKETS,
        max_seq_len_to_capture=32 * 1024,    # 최대 32K 토큰
        prefill_chunk_size=8 * 1024,          # 8K 토큰 청크
    )

    print("\n✅ ArtifactBuilder initialized successfully!")
    print("\n" + "=" * 70)
    print("🔨 Starting compilation process...")
    print("=" * 70)
    print("\n⚠️  This may take a significant amount of time (hours).")
    print("⚠️  Progress will be displayed below.\n")

    # 컴파일 실행
    builder.build(
        str(OUTPUT_DIR),
        num_pipeline_builder_workers=8,      # 8개 워커로 병렬 컴파일
    )

    print("\n" + "=" * 70)
    print("✅ Compilation completed successfully!")
    print("=" * 70)
    print(f"\n📁 Compiled artifacts saved to: {OUTPUT_DIR.absolute()}")

    # 출력 파일 확인
    if OUTPUT_DIR.exists():
        print("\n📋 Generated files:")
        for file in sorted(OUTPUT_DIR.rglob("*")):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   - {file.relative_to(OUTPUT_DIR)}: {size_mb:.2f} MB")

    print("\n🎉 Model is ready for inference on FuriosaAI NPU!")

except ImportError as e:
    print("\n❌ Error: furiosa_llm package not found!")
    print("\n📦 Please install furiosa-llm:")
    print("   $ pip install furiosa-llm")
    print("\n📚 Documentation: https://developer.furiosa.ai/")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Compilation failed with error:")
    print(f"   {type(e).__name__}: {e}")
    print("\n🔍 Troubleshooting tips:")
    print("   1. Ensure FuriosaAI NPU hardware is available")
    print("   2. Check that all drivers are properly installed")
    print("   3. Verify sufficient disk space (>50GB recommended)")
    print("   4. Check system memory (>64GB recommended)")
    print("\n📚 For more help, visit: https://developer.furiosa.ai/")
    sys.exit(1)
