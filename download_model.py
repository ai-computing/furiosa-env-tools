#!/usr/bin/env python3
"""
Llama-3.1-8B-Instruct 원본 모델 다운로드 스크립트 (Hugging Face)
"""
import os
import shutil
from huggingface_hub import snapshot_download
from pathlib import Path

# 모델 ID (원본 Meta Llama 모델)
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

# 저장 디렉토리
SAVE_DIR = Path("./models/Llama-3.1-8B-Instruct-original")
BACKUP_DIR = Path("./models/Llama-3.1-8B-Instruct-compiled-backup")

# 기존 컴파일된 모델이 있으면 백업
OLD_DIR = Path("./models/Llama-3.1-8B-Instruct")
if OLD_DIR.exists() and (OLD_DIR / "artifact.json").exists():
    print(f"🔄 Backing up compiled model to {BACKUP_DIR}...")
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.move(str(OLD_DIR), str(BACKUP_DIR))
    print(f"✅ Backup completed!")

SAVE_DIR.mkdir(parents=True, exist_ok=True)

print(f"📥 Downloading original Hugging Face model: {MODEL_ID}...")
print(f"📂 Save directory: {SAVE_DIR.absolute()}")
print(f"⚠️  This is the ORIGINAL model, not the pre-compiled FuriosaAI artifact")
print(f"⚠️  You will need to compile this model before inference\n")

try:
    # 모델 다운로드
    model_path = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(SAVE_DIR),
        local_dir_use_symlinks=False,
        resume_download=True,
    )

    print(f"✅ Model downloaded successfully!")
    print(f"📁 Model path: {model_path}")

    # 다운로드된 파일 목록 출력
    print("\n📋 Downloaded files:")
    for file in sorted(SAVE_DIR.rglob("*")):
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.relative_to(SAVE_DIR)}: {size_mb:.2f} MB")

except Exception as e:
    print(f"❌ Error downloading model: {e}")
    raise
