#!/usr/bin/env python3
"""
FuriosaAI NPU를 위한 Llama 모델 컴파일 준비 스크립트
"""
import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 설정
MODEL_DIR = Path("./models/Llama-3.1-8B-Instruct")
OUTPUT_DIR = Path("./compiled_models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("🔧 FuriosaAI Llama Model Compilation Setup")
print("=" * 60)

# 1. 모델 정보 확인
print(f"\n📂 Model directory: {MODEL_DIR.absolute()}")

if not MODEL_DIR.exists():
    print(f"❌ Model directory not found: {MODEL_DIR}")
    print("   Please run download_model.py first!")
    exit(1)

# 2. 토크나이저 로드
print("\n📝 Loading tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    print(f"✅ Tokenizer loaded successfully")
    print(f"   Vocabulary size: {tokenizer.vocab_size}")
except Exception as e:
    print(f"❌ Error loading tokenizer: {e}")
    raise

# 3. 모델 구성 확인
print("\n🔍 Checking model configuration...")
try:
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(str(MODEL_DIR))

    print(f"✅ Model configuration:")
    print(f"   Architecture: {config.architectures[0]}")
    print(f"   Hidden size: {config.hidden_size}")
    print(f"   Num layers: {config.num_hidden_layers}")
    print(f"   Num attention heads: {config.num_attention_heads}")
    print(f"   Vocab size: {config.vocab_size}")
    print(f"   Max position embeddings: {config.max_position_embeddings}")

except Exception as e:
    print(f"❌ Error loading config: {e}")
    raise

# 4. 컴파일 정보
print("\n📋 Next Steps for FuriosaAI Compilation:")
print("   1. Install furiosa-llm package (if available)")
print("      $ pip install furiosa-llm")
print("   2. Use FuriosaAI's LLM compilation tools")
print("   3. Or use optimum-furiosa for integration")
print()
print("📝 Example compilation command structure:")
print("   furiosa-llm compile \\")
print(f"     --model-path {MODEL_DIR} \\")
print(f"     --output-path {OUTPUT_DIR} \\")
print("     --batch-size 1 \\")
print("     --seq-length 2048")
print()

# 5. 테스트 입력 생성
print("\n🧪 Generating test input...")
test_text = "Hello, I am a language model"
inputs = tokenizer(test_text, return_tensors="pt")
print(f"✅ Test input generated:")
print(f"   Text: '{test_text}'")
print(f"   Input IDs shape: {inputs['input_ids'].shape}")
print(f"   Attention mask shape: {inputs['attention_mask'].shape}")

print("\n✅ Compilation preparation complete!")
print(f"📁 Model ready at: {MODEL_DIR.absolute()}")
print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
