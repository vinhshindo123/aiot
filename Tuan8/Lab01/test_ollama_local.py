#!/usr/bin/env python3
"""
Test nhanh kết nối Ollama local
Đo tốc độ response và kiểm tra JSON output
KHÔNG THINKING - Response nhanh nhất có thể
"""
import json
import time
import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ requests chưa được cài đặt!")
    print("   Chạy: pip install requests")
    sys.exit(1)

# ============================================================
# CẤU HÌNH - TỐI ƯU CHO TỐC ĐỘ
# ============================================================
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:0.6b')  # Dùng model nhẹ hơn cho test nhanh
LLM_TEMPERATURE = 0.0  # Cực kỳ thấp để không suy nghĩ
LLM_TIMEOUT_SEC = int(os.getenv('LLM_TIMEOUT_SEC', '15'))  # Timeout ngắn hơn

# ============================================================
# KIỂM TRA OLLAMA
# ============================================================
def check_ollama():
    """Kiểm tra Ollama có đang chạy không"""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            models = r.json().get('models', [])
            print(f"✅ Ollama đang chạy tại: {OLLAMA_BASE_URL}")
            print(f"📦 Model đã cài đặt:")
            for m in models:
                size_gb = m.get('size', 0) / 1e9
                print(f"   - {m.get('name', 'unknown')} ({size_gb:.1f} GB)")
            return models
        else:
            print(f"❌ Ollama trả về lỗi: {r.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Không thể kết nối tới Ollama tại {OLLAMA_BASE_URL}")
        print("   Vui lòng chạy: ollama serve")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

# ============================================================
# KIỂM TRA MODEL
# ============================================================
def check_model(model_name):
    """Kiểm tra model có tồn tại không"""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m.get('name', '') for m in r.json().get('models', [])]
            # Kiểm tra model chính xác hoặc phiên bản gần đúng
            for m in models:
                if model_name in m or m.startswith(model_name):
                    return True
            
            # Nếu không tìm thấy, hiển thị các model có sẵn
            print(f"⚠️  Model '{model_name}' không tìm thấy")
            if models:
                print(f"   📦 Các model có sẵn:")
                for m in models[:5]:
                    print(f"      - {m}")
                print(f"\n   💡 Tải model: ollama pull {model_name}")
            return False
    except:
        pass
    return False

# ============================================================
# TEST CHAT OLLAMA - KHÔNG THINKING
# ============================================================
def test_chat_ollama(model_name, prompt, temperature=0.0):
    """Gọi Ollama chat API - TỐI ƯU KHÔNG THINKING"""
    
    # System prompt rõ ràng yêu cầu JSON và không thinking
    system_msg = """Bạn là AIoT assistant. 
QUY TẮC BẮT BUỘC:
1. CHỈ trả về JSON, không có văn bản khác
2. KHÔNG suy nghĩ, KHÔNG giải thích
3. Trả lời NGAY LẬP TỨC
4. JSON phải đúng format"""
    
    payload = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': prompt}
        ],
        'stream': False,
        'options': {
            'temperature': temperature,  # 0.0 = deterministic
            'num_predict': 200,          # Giới hạn output ngắn
            'num_ctx': 1024,             # Context nhỏ để nhanh
            'repeat_penalty': 1.0,       # Không penalize
            'stop': ['', '```'], # Dừng tại các token không cần thiết
        }
    }
    
    start_time = time.time()
    try:
        print(f"\n⏳ Gọi Ollama: {model_name}")
        print(f"   📝 {prompt[:60]}...")
        
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=LLM_TIMEOUT_SEC
        )
        r.raise_for_status()
        
        elapsed_ms = (time.time() - start_time) * 1000
        result = r.json()
        
        response = result.get('message', {}).get('content', '').strip()
        
        # Nếu response rỗng hoặc có thinking, thử lại với prompt khác
        if not response or 'thinking' in response.lower():
            return {
                'success': False,
                'error': 'Model trả về thinking hoặc response rỗng',
                'latency_ms': elapsed_ms,
                'response': response
            }
        
        return {
            'success': True,
            'latency_ms': elapsed_ms,
            'response': response,
            'full_result': result
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': f'Timeout sau {LLM_TIMEOUT_SEC}s',
            'latency_ms': (time.time() - start_time) * 1000
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latency_ms': (time.time() - start_time) * 1000
        }

# ============================================================
# TEST ĐƠN GIẢN NHANH NHẤT
# ============================================================
def test_simple(model_name):
    """Test đơn giản nhất - chỉ hỏi 1 câu"""
    print("\n" + "="*60)
    print("⚡ TEST NHANH NHẤT")
    print("="*60)
    
    # Prompt yêu cầu JSON ngay từ đầu
    prompt = '{"status": "ok", "message": "test"}'
    
    result = test_chat_ollama(model_name, prompt, temperature=0.0)
    
    if result['success']:
        print(f"✅ Thành công - {result['latency_ms']:.0f} ms")
        print(f"📝 Response: {result['response']}")
        
        # Kiểm tra JSON
        try:
            json.loads(result['response'])
            print("✅ JSON hợp lệ")
            return True
        except:
            print("⚠️  Không phải JSON hợp lệ")
            return False
    else:
        print(f"❌ Lỗi: {result.get('error', 'Unknown')}")
        return False

# ============================================================
# TEST JSON OUTPUT - NHANH
# ============================================================
def test_json_output(model_name):
    """Test LLM trả về JSON - Yêu cầu JSON ngay từ đầu"""
    
    test_prompt = """CHỈ trả về JSON, không có văn bản khác.
{"situation_summary": "Phòng đông người, CO2 cao", "risk_level": "HIGH", "recommended_action": "Mở cửa sổ", "need_human_review": true}"""
    
    print("\n" + "="*60)
    print("🧪 TEST JSON OUTPUT (NO THINKING)")
    print("="*60)
    
    result = test_chat_ollama(model_name, test_prompt, temperature=0.0)
    
    if not result['success']:
        print(f"❌ Lỗi: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"⏱️  Latency: {result['latency_ms']:.0f} ms")
    print(f"\n📝 Response:\n{result['response']}")
    
    # Thử parse JSON
    try:
        response_text = result['response'].strip()
        
        # Nếu response có markdown, lấy phần JSON
        if '```json' in response_text:
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        elif '```' in response_text:
            import re
            json_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        data = json.loads(response_text)
        
        print("\n✅ JSON hợp lệ!")
        print(f"   - situation_summary: {data.get('situation_summary', 'N/A')}")
        print(f"   - risk_level: {data.get('risk_level', 'N/A')}")
        print(f"   - recommended_action: {data.get('recommended_action', 'N/A')}")
        return True
    except Exception as e:
        print(f"\n❌ JSON không hợp lệ: {e}")
        return False

# ============================================================
# TEST ĐA DẠNG PROMPT
# ============================================================
def test_various_prompts(model_name):
    """Test với nhiều prompt khác nhau"""
    
    prompts = [
        '{"status": "ok", "message": "hello"}',
        '{"action": "ventilate", "priority": 1, "reason": "CO2 high"}',
        '{"summary": "Room crowded", "risk": "HIGH", "suggest": "Open window"}',
    ]
    
    print("\n" + "="*60)
    print("🧪 TEST NHIỀU PROMPT (NO THINKING)")
    print("="*60)
    
    results = []
    for i, prompt in enumerate(prompts, 1):
        print(f"\n📝 Test {i}: {prompt[:40]}...")
        result = test_chat_ollama(model_name, prompt, temperature=0.0)
        
        if result['success']:
            print(f"   ✅ {result['latency_ms']:.0f} ms")
            # Kiểm tra JSON
            try:
                json.loads(result['response'])
                print(f"   📝 {result['response'][:60]}...")
                results.append(result['latency_ms'])
            except:
                print(f"   ⚠️  Không phải JSON: {result['response'][:40]}...")
        else:
            print(f"   ❌ {result.get('error', 'Unknown')}")
    
    if results:
        print(f"\n📊 Thống kê:")
        print(f"   - Thành công: {len(results)}/{len(prompts)}")
        print(f"   - Latency TB: {sum(results)/len(results):.0f} ms")
        print(f"   - Nhanh nhất: {min(results):.0f} ms")
        print(f"   - Chậm nhất: {max(results):.0f} ms")
    
    return len(results) > 0

# ============================================================
# MAIN
# ============================================================
def main():
    print("="*60)
    print("⚡ OLLAMA LOCAL TEST - NO THINKING")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 1. Kiểm tra Ollama
    print("\n📌 Bước 1: Kiểm tra kết nối Ollama")
    models = check_ollama()
    if models is None:
        print("\n💡 Hướng dẫn:")
        print("   1. Cài đặt Ollama: https://ollama.com/download")
        print("   2. Ollama đang chạy: kiểm tra task manager")
        print("   3. Tải model: ollama pull qwen3:0.6b")
        sys.exit(1)
    
    # 2. Kiểm tra model - thử nhiều model
    test_models = [OLLAMA_MODEL, 'qwen3:0.6b', 'gemma3:1b']
    found_model = None
    
    print(f"\n📌 Bước 2: Tìm model phù hợp")
    for model in test_models:
        if check_model(model):
            found_model = model
            break
    
    if not found_model:
        print("\n❌ Không tìm thấy model nào phù hợp!")
        print("   💡 Tải model: ollama pull qwen3:0.6b")
        print("      (Nhẹ nhất, chạy nhanh nhất)")
        sys.exit(1)
    
    OLLAMA_MODEL = found_model
    print(f"✅ Dùng model: {OLLAMA_MODEL}")
    
    # 3. Test nhanh nhất
    test_simple(OLLAMA_MODEL)
    
    # 4. Test JSON output
    test_json_output(OLLAMA_MODEL)
    
    # 5. Test đa dạng
    test_various_prompts(OLLAMA_MODEL)
    
    # 6. Tóm tắt
    print("\n" + "="*60)
    print("📊 TÓM TẮT")
    print("="*60)
    print(f"✅ Ollama: {OLLAMA_BASE_URL}")
    print(f"✅ Model: {OLLAMA_MODEL}")
    print(f"✅ Temperature: 0.0 (không suy nghĩ)")
    print("✅ Không có thinking trong response")
    print("\n💡 Để chạy local trong Lab 8:")
    print("   1. Chọn mode 'local' trên dashboard")
    print("   2. Bấm 'So sánh 3 tầng'")
    print("   3. Xem tốc độ response")

if __name__ == "__main__":
    main()