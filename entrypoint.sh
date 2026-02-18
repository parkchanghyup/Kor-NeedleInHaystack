#!/bin/bash
set -e

# ========================================================================================
# Needle In A Haystack - Docker Entrypoint Script
# ========================================================================================

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 사용법 함수
usage() {
    echo -e "${BLUE}사용법: docker-compose run --rm needle-test [COMMAND]${NC}"
    echo -e "명령어:"
    echo -e "  ${GREEN}test${NC}            : Gemini 모델로 통합 테스트 시나리오 실행 (기본 설정)"
    echo -e "  ${GREEN}python ...${NC}      : 임의의 Python 명령어 실행 (예: python needle_test.py --help)"
    echo -e "  ${GREEN}bash${NC}            : 대화형 쉘 실행"
    echo -e ""
    echo -e "예시:"
    echo -e "  1. 기본 테스트 실행 (Gemini 2.5 Flash Lite + 3 Flash Preview)"
    echo -e "     ${YELLOW}docker-compose run --rm needle-test test${NC}"
    echo -e ""
    echo -e "  2. 특정 파라미터로 직접 실행"
    echo -e "     ${YELLOW}docker-compose run --rm needle-test python needle_test.py --provider openai ...${NC}"
}

# 'test' 명령어가 입력되면 통합 테스트 실행
if [ "$1" = "test" ]; then
    echo -e "${BLUE}[Needle In A Haystack] 통합 테스트를 시작합니다.${NC}"
    echo -e "사용 모델: ${GREEN}Gemini 2.5 Flash Lite${NC} (Tester) / ${GREEN}Gemini 3 Flash Preview${NC} (Evaluator)"
    
    # 환경 점검
    echo -e "\n${BLUE}[1/4] 환경 설정 점검${NC}"
    python tools/setup_check.py

    # 단일 Needle 테스트
    echo -e "\n${BLUE}[2/4] 단일 Needle 테스트 실행 (Small Scale)${NC}"
    python needle_test.py \
        --provider gemini \
        --model_name "gemini-2.5-flash-lite" \
        --evaluator gemini \
        --evaluator_model_name "gemini-3-flash-preview" \
        --context_lengths_min 1000 \
        --context_lengths_max 5000 \
        --context_lengths_num_intervals 3 \
        --document_depth_percent_intervals 3 \
        --save_results true \
        --save_contexts true

    # 다중 Needle 테스트
    echo -e "\n${BLUE}[3/4] 다중 Needle 테스트 실행${NC}"
    python needle_test.py \
        --multi_needle true \
        --provider gemini \
        --model_name "gemini-2.5-flash-lite" \
        --evaluator gemini \
        --evaluator_model_name "gemini-3-flash-preview" \
        --context_lengths_min 1000 \
        --context_lengths_max 5000 \
        --context_lengths_num_intervals 3 \
        --document_depth_percent_intervals 3 \
        --save_results true

    # 결과 분석
    echo -e "\n${BLUE}[4/4] 결과 분석 및 시각화${NC}"
    python tools/analyze_results.py

    echo -e "\n${GREEN}🎉 모든 테스트가 완료되었습니다!${NC}"
    exit 0
fi

# 인자가 없으면 사용법 출력
if [ -z "$1" ]; then
    usage
    exit 0
fi

# 그 외 명령어는 그대로 실행
exec "$@"
