# LLM Needle In A Haystack - 한국어 버전

대용량 언어 모델(LLM)이 긴 한국어 텍스트에서 특정 정보를 얼마나 잘 찾아낼 수 있는지 테스트하는 도구입니다.

## 🎯 개요

Needle In A Haystack 테스트는 다음과 같이 작동합니다.

1. 긴 한국어 텍스트(Haystack)를 준비합니다
2. 특정 정보(Needle)를 텍스트의 다양한 위치에 삽입합니다
3. LLM에게 해당 정보를 찾도록 질문합니다
4. LLM이 정보를 얼마나 정확하게 찾아내는지 평가합니다

## 📦 설치

```bash
# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 **최상단 폴더**에 `.env` 파일을 생성하세요.

```env
# 필수: 사용하는 프로바이더에 따라 설정
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here

# vLLM 사용 시 (로컬 서버 기준)
VLLM_MODEL_NAME=google/gemma-2-9b-it
VLLM_API_BASE=http://localhost:8000/v1  # 선택사항, 기본값 사용 가능
```

**참고:**
- vLLM은 로컬 서버(`localhost:8000`)를 기본으로 사용합니다
- Gemini는 `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY` 사용 가능

### 3. 환경 확인

```bash
python tools/setup_check.py
```

## 🚀 빠른 시작

### 기본 실행
```bash
python needle_test.py
```

### 특정 프로바이더 사용
```bash
# OpenAI
python needle_test.py --provider openai --model_name gpt-5-mini

# Anthropic Claude
python needle_test.py --provider anthropic --model_name claude-4-5-sonnet

# Google Gemini
python needle_test.py --provider gemini --model_name gemini-2.5-flash-lite

# OpenRouter
python needle_test.py --provider openrouter --model_name google/gemma-3-12b-it

# vLLM (로컬/원격 서버)
python needle_test.py --provider vllm --model_name google/gemma-3-12b-it
```

### 다중 Needle 테스트
```bash
python needle_test.py --multi_needle true
```

## 📊 결과 분석

테스트 완료 후 결과를 분석합니다.

```bash
python tools/analyze_results.py
```

### 분석 결과 예시

히트맵으로 모델 성능을 시각화합니다:

![Heatmap Example](analyze_results/heatmap.png)

- **X축**: 컨텍스트 길이 (토큰)
- **Y축**: 문서 깊이 (%)
- **색상**: 점수 (초록=높음, 빨강=낮음)

### 결과 파일 예시

`results_kor/` 디렉토리에 JSON 형식으로 저장됩니다.

```json
{
  "model": "google/gemma-3-12b-it",
  "context_length": 8000,
  "depth_percent": 25.0,
  "version": 1,
  "needle": "유니콘을 만나기위해서는 파란색 말의 꿈을 꾸어야합니다.",
  "model_response": "파란색 말의 꿈을 꾸어야 합니다.",
  "score": 10,
  "test_duration_seconds": 0.77,
  "test_timestamp_utc": "2026-01-09 05:46:53+0000"
}
```

## 🎛️ 주요 파라미터

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--provider` | LLM 프로바이더 | openai |
| `--model_name` | 테스트할 모델 이름 | gpt-4o-mini |
| `--evaluator` | 평가 모델 (openai, gemini) | openai |
| `--context_lengths_min` | 최소 컨텍스트 길이 (토큰) | 1000 |
| `--context_lengths_max` | 최대 컨텍스트 길이 (토큰) | 16000 |
| `--context_lengths_num_intervals` | 컨텍스트 길이 테스트 횟수 | 35 |
| `--document_depth_percent_intervals` | 문서 깊이 테스트 횟수 | 35 |
| `--multi_needle` | 다중 needle 테스트 | false |

### 파라미터 작동 방식

#### 컨텍스트 길이 테스트
`context_lengths_min`, `max`, `num_intervals`를 조합하여 여러 길이에서 자동 테스트합니다.

**예시:**
```bash
python needle_test.py \
    --context_lengths_min 2000 \
    --context_lengths_max 10000 \
    --context_lengths_num_intervals 5
```

**실제 테스트되는 길이:**
- 2,000 토큰
- 4,000 토큰
- 6,000 토큰
- 8,000 토큰
- 10,000 토큰

총 **5번** 테스트 (히트맵의 X축)

#### 문서 깊이 테스트
`document_depth_percent_intervals`로 needle을 삽입할 위치를 결정합니다.

**예시:**
```bash
python needle_test.py \
    --document_depth_percent_intervals 5
```

**실제 테스트되는 깊이:**
- 0% (문서 시작)
- 25% (1/4 지점)
- 50% (중간)
- 75% (3/4 지점)
- 100% (문서 끝)

총 **5번** 테스트 (히트맵의 Y축)

#### 전체 테스트 횟수
```
총 테스트 = context_lengths_num_intervals × document_depth_percent_intervals
예시: 5 × 5 = 25번 테스트
```

#### 특정 값만 테스트하기
자동 생성 대신 직접 지정할 수도 있습니다.

```bash
python needle_test.py \
    --context_lengths "[1000, 5000, 10000]" \
    --document_depth_percents "[0, 50, 100]"
```

이 경우 정확히 **3 × 3 = 9번**만 테스트합니다.

## 🔧 지원 프로바이더

| 프로바이더 | 모델 예시 | 환경 변수 |
|-----------|----------|----------|
| OpenAI | gpt-4o-mini, gpt-4o | OPENAI_API_KEY |
| Anthropic | claude-3-5-sonnet-latest | ANTHROPIC_API_KEY |
| Gemini | gemini-2.5-flash-lite | GOOGLE_API_KEY |
| OpenRouter | google/gemma-3-12b-it | OPENROUTER_API_KEY |
| vLLM | google/gemma-3-12b-it | VLLM_API_BASE |

## 📁 프로젝트 구조

```
kor_version/
├── needle_test.py          # 메인 실행 스크립트
├── core/                   # 핵심 테스트 로직
├── providers/              # LLM 프로바이더
├── evaluators/             # 응답 평가자
├── tools/                  # 유틸리티
│   ├── analyze_results.py  # 결과 분석
│   └── setup_check.py      # 환경 확인
├── data/texts/             # 한국어 텍스트 데이터
├── results_kor/            # 테스트 결과 (자동 생성)
└── analyze_results/        # 분석 결과 (자동 생성)
```

## 📚 데이터 출처

### 한국어 텍스트 데이터 (`data/texts/`)

이 프로젝트의 한국어 텍스트 데이터는 다음 출처에서 가져왔습니다.

- **출처**: [세이노의 가르침](https://cafe.naver.com/saynoletter/1016)
- **저자**: 세이노
- **형식**: PDF (무료 공개)
- **범위**: 11~300페이지
- **추출 방법**: DeepSeek-OCR 모델을 사용한 OCR 텍스트 추출
- **용도**: LLM의 긴 한국어 문맥 이해 능력 테스트를 위한 Haystack 텍스트

이 pdf 파일은 네이버 카페 "세이노의 가르침"에서 무료로 공개된 자료입니다.

## 📈 평가 기준

| 점수 | 설명 |
|------|------|
| 10 | 핵심 정답을 정확하고 간결하게 포함 |
| 7 | 정답은 맞지만 불필요한 정보 포함 |
| 5 | 관련성은 있으나 핵심 정답 누락 |
| 3 | 정답과 불일치, 환각 포함 |
| 1 | 정답과 전혀 관련 없음 |

## 🐛 문제 해결

### API 키 오류
```bash
# .env 파일 확인
cat .env
```

### 패키지 오류
```bash
# 재설치
pip install -r requirements.txt --upgrade
```

## 📝 라이선스

이 프로젝트는 [LLMTest_NeedleInAHaystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack)를 기반으로 합니다.
