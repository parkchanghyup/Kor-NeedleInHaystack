"""
설치 및 설정 확인 스크립트
한국어 버전 LLM Needle In A Haystack 테스트를 실행하기 전에
필요한 모든 것이 올바르게 설정되었는지 확인합니다.
"""

import os
import sys
import glob

def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (권장: 3.8+)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (3.8+ 필요)")
        return False

def check_packages():
    """필수 패키지 확인"""
    print("\n📦 필수 패키지 확인...")
    required_packages = [
        'numpy',
        'dotenv',
        'jsonargparse',
        'openai',
        'asyncio'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (설치 필요)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   ⚠️  누락된 패키지를 설치하려면 다음을 실행하세요:")
        print(f"   pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """환경 변수 파일 확인"""
    print("\n🔑 환경 변수 (.env) 확인...")
    
    # 프로젝트 루트에서 .env 파일 찾기
    env_paths = [
        ".env",
        "../.env",
        "../../.env"
    ]
    
    env_found = False
    for path in env_paths:
        if os.path.exists(path):
            env_found = True
            print(f"   ✅ .env 파일 발견: {os.path.abspath(path)}")
            
            # API 키 확인
            try:
                from dotenv import load_dotenv
                load_dotenv(path)
                
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key and openai_key != 'your_openai_api_key_here':
                    print(f"   ✅ OPENAI_API_KEY 설정됨")
                else:
                    print(f"   ⚠️  OPENAI_API_KEY가 설정되지 않았습니다")
                    print(f"      .env 파일에 API 키를 추가하세요")
            except Exception as e:
                print(f"   ⚠️  .env 파일 읽기 오류: {e}")
            break
    
    if not env_found:
        print(f"   ⚠️  .env 파일을 찾을 수 없습니다")
        print(f"      kor_version/.env.example을 참고하여 프로젝트 루트에 .env 파일을 생성하세요")
        return False
    
    return True

def check_korean_texts():
    """한국어 텍스트 파일 확인"""
    print("\n📄 한국어 텍스트 파일 확인...")
    
    text_dir = os.path.join(os.path.dirname(__file__), "..", "data", "texts")
    
    if not os.path.exists(text_dir):
        print(f"   ❌ output_texts 디렉토리를 찾을 수 없습니다: {text_dir}")
        return False
    
    text_files = glob.glob(os.path.join(text_dir, "*.txt"))
    
    if len(text_files) == 0:
        print(f"   ❌ data/texts 디렉토리에 텍스트 파일이 없습니다")
        print(f"      data/texts/ 디렉토리에 한국어 텍스트 파일(.txt)을 추가하세요")
        return False
    
    print(f"   ✅ {len(text_files)}개의 한국어 텍스트 파일 발견")
    
    # 첫 번째 파일의 크기 확인
    first_file = text_files[0]
    file_size = os.path.getsize(first_file)
    print(f"   ℹ️  예시 파일: {os.path.basename(first_file)} ({file_size} bytes)")
    
    return True


def check_output_directories():
    """결과 디렉토리 확인"""
    print("\n📁 출력 디렉토리 확인...")
    
    dirs_to_check = ['results_kor', 'contexts_kor']
    
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            file_count = len(os.listdir(dir_name))
            print(f"   ✅ {dir_name}/ (파일 {file_count}개)")
        else:
            print(f"   ℹ️  {dir_name}/ (아직 생성되지 않음, 테스트 실행 시 자동 생성됨)")
    
    return True

def main():
    """모든 확인 실행"""
    print("=" * 70)
    print("한국어 버전 LLM Needle In A Haystack - 설정 확인")
    print("=" * 70)
    
    checks = [
        ("Python 버전", check_python_version),
        ("필수 패키지", check_packages),
        ("환경 변수 파일", check_env_file),
        ("한국어 텍스트", check_korean_texts),
        ("출력 디렉토리", check_output_directories)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n   ❌ {name} 확인 중 오류 발생: {e}")
            results[name] = False
    
    # 최종 결과
    print("\n" + "=" * 70)
    print("최종 결과")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{status}: {name}")
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 모든 확인이 완료되었습니다!")
        print("다음 명령으로 테스트를 시작할 수 있습니다:")
        print("\n  python needle_test.py")
        print("  또는")
        print("  python examples/example_single_needle.py")
    else:
        print("\n⚠️  일부 확인이 실패했습니다.")
        print("위의 오류 메시지를 확인하고 문제를 해결한 후 다시 시도하세요.")
        print("\n도움이 필요하면 README.md 파일을 참고하세요.")
    
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

