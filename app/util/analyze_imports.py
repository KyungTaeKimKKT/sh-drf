import os
import re
import subprocess
from collections import Counter

def count_imports(path="."):
    """프로젝트 전체 import 횟수 집계"""
    imports = Counter()
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), encoding="utf-8") as f:
                    for line in f:
                        match = re.match(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", line)
                        if match:
                            imports[match.group(1).split(".")[0]] += 1
    return imports

def find_unused_imports(path="."):
    """flake8 으로 unused import 탐지"""
    try:
        result = subprocess.run(
            ["flake8", "--select=F401", path],
            capture_output=True,
            text=True,
            check=False
        )
        unused = []
        for line in result.stdout.splitlines():
            # 예: myproject/app.py:3:1: F401 'requests' imported but unused
            if "F401" in line:
                parts = line.split()
                if len(parts) >= 4:
                    unused.append(parts[3].strip("'"))
        return unused
    except FileNotFoundError:
        print("⚠️ flake8 이 설치되어 있지 않습니다. pip install flake8 으로 설치하세요.")
        return []

def main(project_path:str="./"):

    print("📊 Import 빈도 분석 중...")
    counts = count_imports(project_path)
    for pkg, n in counts.most_common():
        print(f"  {pkg}: {n}")

    print("\n🧹 사용되지 않은 import 탐지 중...")
    unused = find_unused_imports(project_path)
    if unused:
        print("  사용되지 않은 import 후보:")
        for pkg in set(unused):
            print(f"   - {pkg}")
    else:
        print("  불필요한 import 없음 ✅")

if __name__ == "__main__":
    main()

### from util.analyze_imports import main
### main()