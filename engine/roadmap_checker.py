"""
Engine Roadmap Checker: 진화 후 로드맵 완료 상태 자동 체크
==========================================================
진화가 성공하면 현재 Step 완료 여부를 확인하고,
완료되었으면 자동으로 다음 Step으로 이동하고 Git 커밋/푸시
"""

import os
import json
from typing import Dict, Tuple, Optional

from .roadmap_criteria import STEP_COMPLETION_CRITERIA
from .roadmap_git import commit_and_push_roadmap


class RoadmapChecker:
    """로드맵 완료 상태 체커"""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.fact_core_path = os.path.join(base_path, "fact_core.json")

    def check_step_completion(self, step_id: str) -> Tuple[bool, str]:
        """특정 Step의 완료 여부 확인"""
        if step_id not in STEP_COMPLETION_CRITERIA:
            return False, f"알 수 없는 Step: {step_id}"

        criteria = STEP_COMPLETION_CRITERIA[step_id]
        checks = criteria["checks"]
        passed = []
        failed = []

        for file_path, keyword in checks:
            full_path = os.path.join(self.base_path, file_path)
            if self._file_contains(full_path, keyword):
                passed.append(f"✅ {file_path}: {keyword}")
            else:
                failed.append(f"❌ {file_path}: {keyword}")

        if not failed:
            return True, f"{criteria['name']} 완료!\n" + "\n".join(passed)
        else:
            return False, f"{criteria['name']} 미완료\n" + "\n".join(passed + failed)

    def _file_contains(self, file_path: str, keyword: str) -> bool:
        """파일에 특정 키워드가 있는지 확인"""
        try:
            if not os.path.exists(file_path):
                return False
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return keyword in content
        except Exception:
            return False

    def get_current_focus(self) -> Optional[str]:
        """fact_core.json에서 현재 focus 가져오기"""
        try:
            with open(self.fact_core_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("roadmap", {}).get("current_focus")
        except Exception:
            return None

    def update_current_focus(self, new_focus: str) -> bool:
        """fact_core.json의 current_focus 업데이트"""
        try:
            with open(self.fact_core_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            old_focus = data.get("roadmap", {}).get("current_focus")
            data["roadmap"]["current_focus"] = new_focus

            # 이전 Step 완료 표시
            for phase in ["phase_2_memory", "phase_3_awakening"]:
                if old_focus and old_focus in data["roadmap"].get(phase, {}):
                    data["roadmap"][phase][old_focus]["status"] = "completed"

            # 새 Step in_progress 표시
            for phase in ["phase_2_memory", "phase_3_awakening", "phase_4_consciousness"]:
                if new_focus in data["roadmap"].get(phase, {}):
                    data["roadmap"][phase][new_focus]["status"] = "in_progress"

            with open(self.fact_core_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return True
        except Exception as e:
            print(f"⚠️ fact_core.json 업데이트 실패: {e}")
            return False

    def get_current_status_for_dreamer(self) -> str:
        """Dreamer에게 전달할 현재 Step 완료 상태 문자열 반환"""
        current = self.get_current_focus()
        if not current or current not in STEP_COMPLETION_CRITERIA:
            return "현재 Step 정보 없음"

        criteria = STEP_COMPLETION_CRITERIA[current]
        lines = [f"[현재 Step: {criteria['name']} ({current})]"]
        lines.append("완료 조건 체크:")

        for file_path, keyword in criteria["checks"]:
            full_path = os.path.join(self.base_path, file_path)
            if self._file_contains(full_path, keyword):
                lines.append(f"  ✅ {file_path}: {keyword} 존재")
            else:
                lines.append(f"  ❌ {file_path}: {keyword} 없음 → 구현 필요!")

        return "\n".join(lines)

    def check_and_advance(self) -> Dict:
        """현재 Step 완료 여부 확인 후 자동 진행"""
        result = {
            "step_completed": False,
            "old_step": None,
            "new_step": None,
            "message": "",
            "git_pushed": False
        }

        current = self.get_current_focus()
        if not current:
            result["message"] = "current_focus를 찾을 수 없음"
            return result

        result["old_step"] = current

        is_complete, detail = self.check_step_completion(current)

        if is_complete:
            criteria = STEP_COMPLETION_CRITERIA.get(current, {})
            next_step = criteria.get("next_step")

            if next_step:
                if self.update_current_focus(next_step):
                    result["step_completed"] = True
                    result["new_step"] = next_step
                    result["message"] = f"🎉 {criteria['name']} 완료! → {next_step} 시작"

                    success, msg = commit_and_push_roadmap(
                        self.base_path, self.fact_core_path,
                        criteria['name'], next_step
                    )
                    result["git_pushed"] = success
                    print(msg)
                else:
                    result["message"] = f"Step 완료됐지만 fact_core 업데이트 실패"
            else:
                result["step_completed"] = True
                result["message"] = f"🎉 {criteria['name']} 완료! (마지막 Step)"
        else:
            result["message"] = detail

        return result


# 싱글톤 인스턴스
_checker_instance = None


def get_roadmap_checker() -> RoadmapChecker:
    """RoadmapChecker 싱글톤 인스턴스 반환"""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = RoadmapChecker()
    return _checker_instance
