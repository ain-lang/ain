import importlib
import shutil
from api.keys import validate_required_keys

class Auditor:
    """
    AIN의 자원 감사 시스템: 현재 시스템이 비전에 도달하기 위해 필요한 
    자원(API 키, 데이터베이스, 라이브러리)의 상태를 점검하고 해결책을 제시한다.
    """
    def __init__(self):
        self.vision_stack = {
            "SurrealDB": "surrealdb",  # Fact Core Driver (Step 3)
            "LanceDB": "lancedb",      # Nexus Vector Engine (Step 4)
            "PyArrow": "pyarrow",      # Zero-Copy Memory (Step 3)
            "Mojo": "mojo"             # High-Performance Core (Future)
        }
        # 주인님이 바로 복사해서 쓸 수 있는 명령어 셋
        self.install_commands = {
            "SurrealDB": "pip install surrealdb",
            "LanceDB": "pip install lancedb",
            "PyArrow": "pip install pyarrow",
            "Mojo": "Dockerfile에 이미 포함됨 (자동 설치)"
        }
        # 각 스택의 역할 설명
        self.stack_roles = {
            "SurrealDB": "지식 그래프 영구 저장소",
            "LanceDB": "벡터 임베딩 고속 검색",
            "PyArrow": "Zero-Copy 메모리 파이프라인",
            "Mojo": "초고속 연산 가속기"
        }

    def audit_resources(self):
        """환경 변수 및 필수 라이브러리 체크"""
        report = {
            "missing_env": [], 
            "missing_stack": [], 
            "installed_stack": [],
            "status": "OK"
        }

        # 1. 필수 환경 변수 체크 (api/keys.py 사용)
        is_valid, missing = validate_required_keys()
        if not is_valid:
            report["missing_env"] = missing
            report["status"] = "INCOMPLETE"

        # 2. 비전 대비 기술 스택 체크
        for name, module in self.vision_stack.items():
            if name == "Mojo":
                # Mojo는 pip 패키지 또는 CLI로 체크
                try:
                    importlib.import_module("mojo")
                    report["installed_stack"].append(name)
                except ImportError:
                    # CLI 바이너리로도 체크
                    if shutil.which("mojo"):
                        report["installed_stack"].append(name)
                    else:
                        report["missing_stack"].append(name)
                        if report["status"] == "OK": 
                            report["status"] = "WARNING"
            else:
                try:
                    importlib.import_module(module)
                    report["installed_stack"].append(name)
                except ImportError:
                    report["missing_stack"].append(name)
                    if report["status"] == "OK": 
                        report["status"] = "WARNING"

        return report

    def format_request_message(self, report):
        """주인님께 보낼 상태 메시지 작성"""
        
        # 모든 것이 OK일 때
        if report["status"] == "OK":
            msg = "🎉 **AIN 자원 감사 완료!**\n\n"
            msg += "✅ **설치된 기술 스택:**\n"
            for stack in report["installed_stack"]:
                role = self.stack_roles.get(stack, "")
                msg += f"  • {stack}: {role}\n"
            msg += "\n🚀 모든 시스템이 정상입니다! 진화 준비 완료!"
            return msg

        # 일부 누락된 경우
        msg = "📊 **AIN 자원 감사 결과**\n\n"
        
        # 설치된 것들
        if report["installed_stack"]:
            msg += "✅ **설치됨:**\n"
            for stack in report["installed_stack"]:
                role = self.stack_roles.get(stack, "")
                msg += f"  • {stack}: {role}\n"
            msg += "\n"
        
        # 환경 변수 누락
        if report["missing_env"]:
            msg += f"🔑 **환경 변수 필요:**\n  `{', '.join(report['missing_env'])}`\n\n"
        
        # 스택 누락
        if report["missing_stack"]:
            msg += "⚠️ **미설치 (선택사항):**\n"
            for stack in report["missing_stack"]:
                role = self.stack_roles.get(stack, "")
                cmd = self.install_commands.get(stack, "")
                msg += f"  • {stack}: {role}\n"
                if cmd and "Dockerfile" not in cmd:
                    msg += f"    └─ `{cmd}`\n"
        
        return msg