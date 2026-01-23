"""
Import Validator
================
Python 코드의 import 문을 검증하여 존재하지 않는 모듈 import를 방지한다.

주요 기능:
- 상대 import (from .X import Y) 검증
- 대상 파일이 실제로 존재하는지 확인
- __init__.py 파일 수정 시 특히 중요

Usage:
    from utils.import_validator import validate_imports

    success, error = validate_imports(code, "engine/__init__.py")
    if not success:
        print(f"Import 검증 실패: {error}")
"""

import re
import os
from typing import Tuple, List, Optional


def validate_imports(
    code: str,
    filename: str,
    base_path: str = "."
) -> Tuple[bool, Optional[str]]:
    """
    코드 내 import 문을 검증한다.

    Args:
        code: 검증할 Python 코드
        filename: 코드가 저장될 파일 경로
        base_path: 프로젝트 루트 경로

    Returns:
        (성공 여부, 에러 메시지 또는 None)
    """
    if not filename.endswith(".py"):
        return True, None

    # 파일이 속한 디렉토리 계산
    file_dir = os.path.dirname(filename)
    if not file_dir:
        file_dir = "."

    # 상대 import 패턴 찾기
    # from .module import Class
    # from .module import func1, func2
    relative_import_pattern = r'from\s+\.(\w+)\s+import'

    matches = re.findall(relative_import_pattern, code)

    missing_modules = []

    for module_name in matches:
        # 예상 파일 경로 계산
        expected_file = os.path.join(base_path, file_dir, f"{module_name}.py")
        expected_package = os.path.join(base_path, file_dir, module_name, "__init__.py")

        # 파일 또는 패키지로 존재하는지 확인
        if not os.path.exists(expected_file) and not os.path.exists(expected_package):
            missing_modules.append(module_name)

    if missing_modules:
        modules_str = ", ".join(missing_modules)
        return False, f"🚨 존재하지 않는 모듈 import: {modules_str} (위치: {file_dir}/)"

    return True, None


def get_imported_modules(code: str) -> List[str]:
    """
    코드에서 import된 모든 모듈명을 추출한다.

    Args:
        code: Python 코드

    Returns:
        import된 모듈명 리스트
    """
    modules = []

    # import X
    import_pattern = r'^import\s+([\w.]+)'
    modules.extend(re.findall(import_pattern, code, re.MULTILINE))

    # from X import Y
    from_pattern = r'^from\s+([\w.]+)\s+import'
    modules.extend(re.findall(from_pattern, code, re.MULTILINE))

    return list(set(modules))


def validate_package_init(
    code: str,
    init_file: str,
    base_path: str = "."
) -> Tuple[bool, Optional[str]]:
    """
    __init__.py 파일의 import를 특별히 검증한다.

    패키지 초기화 파일은 상대 import가 많으므로 더 엄격하게 검증.

    Args:
        code: __init__.py 코드
        init_file: __init__.py 파일 경로 (예: engine/__init__.py)
        base_path: 프로젝트 루트 경로

    Returns:
        (성공 여부, 에러 메시지 또는 None)
    """
    if not init_file.endswith("__init__.py"):
        return True, None

    return validate_imports(code, init_file, base_path)
