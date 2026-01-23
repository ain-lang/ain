"""
Nexus Storage: JSON 파일 I/O 유틸리티
"""
import json
import os


def load_json(filename: str):
    """범용 JSON 로드 (깨진 파일 복구 로직 포함)"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 파일 끝에 쓰레기 데이터가 붙어있는 경우 처리
                    last_brace = content.rfind("}")
                    last_bracket = content.rfind("]")
                    cut_point = max(last_brace, last_bracket)
                    
                    if cut_point != -1:
                        try:
                            fixed_data = json.loads(content[:cut_point+1])
                            print(f"⚠️ Nexus: {filename} 복구 로드 성공")
                            return fixed_data
                        except:
                            pass
                    raise
        except Exception as e:
            print(f"⚠️ Nexus load_data error ({filename}): {e}")
    return None


def save_json(filename: str, data) -> bool:
    """범용 JSON 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Nexus save_data error ({filename}): {e}")
        return False
