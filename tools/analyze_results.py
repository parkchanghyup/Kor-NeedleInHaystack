"""
결과 분석 스크립트
지정된 디렉토리의 테스트 결과를 분석하고 히트맵 그래프를 생성합니다.

사용법:
    python tools/analyze_results.py [결과_디렉토리]
    
예시:
    python tools/analyze_results.py                    # results_kor 디렉토리 분석 (기본값)
    python tools/analyze_results.py gemma3_results     # gemma3_results 디렉토리 분석
    python tools/analyze_results.py my_custom_results  # 사용자 지정 디렉토리 분석

출력:
    - analyze_results/heatmap.png: 컨텍스트 길이 vs 문서 깊이 히트맵
    - analyze_results/summary.json: JSON 형식 요약 통계
    - analyze_results/analysis_report.txt: 텍스트 형식 분석 리포트
"""

import json
import glob
import os
from collections import defaultdict
import statistics
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def analyze_results(results_dir="results_kor", output_dir="analyze_results"):
    """
    테스트 결과를 분석하고 히트맵 그래프 및 요약 통계를 생성합니다.
    
    Args:
        results_dir: 결과 파일이 있는 디렉토리
        output_dir: 분석 결과를 저장할 디렉토리
    """
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(results_dir):
        print(f"오류: {results_dir} 디렉토리를 찾을 수 없습니다.")
        print("먼저 테스트를 실행해주세요.")
        return
    
    results_files = glob.glob(os.path.join(results_dir, "*.json"))
    
    if not results_files:
        print(f"{results_dir} 디렉토리에 결과 파일이 없습니다.")
        print("먼저 테스트를 실행해주세요.")
        return
    
    all_results = []
    scores_by_context_length = defaultdict(list)
    scores_by_depth = defaultdict(list)
    heatmap_data = {}  # (context_length, depth) -> score
    models = set()
    
    # 모든 결과 파일 읽기
    for file in results_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
                
                # 모델 이름 수집
                models.add(data.get('model', 'Unknown'))
                
                # 컨텍스트 길이별 점수
                context_length = data.get('context_length', 0)
                scores_by_context_length[context_length].append(data.get('score', 0))
                
                # 깊이별 점수
                depth = data.get('depth_percent', 0)
                scores_by_depth[depth].append(data.get('score', 0))
                
                # 히트맵 데이터 수집
                heatmap_data[(context_length, depth)] = data.get('score', 0)
        except Exception as e:
            print(f"파일 읽기 오류 ({file}): {e}")
    
    if not all_results:
        print("분석할 결과가 없습니다.")
        return
    
    # 기본 통계
    all_scores = [r.get('score', 0) for r in all_results]
    all_durations = [r.get('test_duration_seconds', 0) for r in all_results]
    
    print("=" * 70)
    print("테스트 결과 분석")
    print("=" * 70)
    
    print(f"\n📊 전체 통계:")
    print(f"  총 테스트 수: {len(all_results)}")
    print(f"  테스트한 모델: {', '.join(models)}")
    print(f"  평균 점수: {statistics.mean(all_scores):.2f}/10")
    print(f"  중앙값 점수: {statistics.median(all_scores):.2f}/10")
    print(f"  최고 점수: {max(all_scores)}/10")
    print(f"  최저 점수: {min(all_scores)}/10")
    
    if len(all_scores) > 1:
        print(f"  표준 편차: {statistics.stdev(all_scores):.2f}")
    
    print(f"\n⏱️  성능 통계:")
    print(f"  평균 테스트 시간: {statistics.mean(all_durations):.2f}초")
    print(f"  총 테스트 시간: {sum(all_durations):.2f}초 ({sum(all_durations)/60:.2f}분)")
    
    # 컨텍스트 길이별 분석
    print(f"\n📏 컨텍스트 길이별 평균 점수:")
    for context_length in sorted(scores_by_context_length.keys()):
        scores = scores_by_context_length[context_length]
        avg_score = statistics.mean(scores)
        print(f"  {context_length:6d} 토큰: {avg_score:5.2f}/10 ({len(scores)}개 테스트)")
    
    # 깊이별 분석
    print(f"\n📍 문서 깊이별 평균 점수:")
    for depth in sorted(scores_by_depth.keys()):
        scores = scores_by_depth[depth]
        avg_score = statistics.mean(scores)
        print(f"  {depth:5.1f}%: {avg_score:5.2f}/10 ({len(scores)}개 테스트)")
    
    # 점수 분포
    print(f"\n📈 점수 분포:")
    score_ranges = {
        "완벽 (10점)": 0,
        "우수 (8-9점)": 0,
        "양호 (6-7점)": 0,
        "보통 (4-5점)": 0,
        "미흡 (2-3점)": 0,
        "불량 (0-1점)": 0
    }
    
    for score in all_scores:
        if score == 10:
            score_ranges["완벽 (10점)"] += 1
        elif score >= 8:
            score_ranges["우수 (8-9점)"] += 1
        elif score >= 6:
            score_ranges["양호 (6-7점)"] += 1
        elif score >= 4:
            score_ranges["보통 (4-5점)"] += 1
        elif score >= 2:
            score_ranges["미흡 (2-3점)"] += 1
        else:
            score_ranges["불량 (0-1점)"] += 1
    
    for range_name, count in score_ranges.items():
        if count > 0:
            percentage = (count / len(all_scores)) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {range_name}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # 최고/최저 성능 테스트
    print(f"\n🏆 최고 성능 테스트:")
    best_result = max(all_results, key=lambda x: x.get('score', 0))
    print(f"  점수: {best_result.get('score', 0)}/10")
    print(f"  컨텍스트 길이: {best_result.get('context_length', 0)} 토큰")
    print(f"  문서 깊이: {best_result.get('depth_percent', 0):.1f}%")
    print(f"  소요 시간: {best_result.get('test_duration_seconds', 0):.2f}초")
    
    print(f"\n⚠️  최저 성능 테스트:")
    worst_result = min(all_results, key=lambda x: x.get('score', 0))
    print(f"  점수: {worst_result.get('score', 0)}/10")
    print(f"  컨텍스트 길이: {worst_result.get('context_length', 0)} 토큰")
    print(f"  문서 깊이: {worst_result.get('depth_percent', 0):.1f}%")
    print(f"  소요 시간: {worst_result.get('test_duration_seconds', 0):.2f}초")
    
    # 히트맵 생성
    print(f"\n🎨 히트맵 생성 중...")
    create_heatmap(heatmap_data, output_dir, list(models)[0] if models else "Unknown")
    
    print("\n" + "=" * 70)
    print(f"분석 완료! 결과 파일 위치: {output_dir}/")
    print("=" * 70)
    
    # 요약 저장
    summary = {
        "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_directory": results_dir,
        "total_tests": len(all_results),
        "models": list(models),
        "average_score": statistics.mean(all_scores),
        "median_score": statistics.median(all_scores),
        "max_score": max(all_scores),
        "min_score": min(all_scores),
        "std_dev": statistics.stdev(all_scores) if len(all_scores) > 1 else 0,
        "average_duration": statistics.mean(all_durations),
        "total_duration": sum(all_durations),
        "scores_by_context_length": {k: statistics.mean(v) for k, v in scores_by_context_length.items()},
        "scores_by_depth": {k: statistics.mean(v) for k, v in scores_by_depth.items()},
        "score_distribution": score_ranges,
        "best_result": {
            "score": best_result.get('score', 0),
            "context_length": best_result.get('context_length', 0),
            "depth_percent": best_result.get('depth_percent', 0),
            "duration": best_result.get('test_duration_seconds', 0)
        },
        "worst_result": {
            "score": worst_result.get('score', 0),
            "context_length": worst_result.get('context_length', 0),
            "depth_percent": worst_result.get('depth_percent', 0),
            "duration": worst_result.get('test_duration_seconds', 0)
        }
    }
    
    summary_file = os.path.join(output_dir, "summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 요약 파일이 저장되었습니다: {summary_file}")
    print(f"📊 히트맵 파일이 저장되었습니다: {output_dir}/heatmap.png")
    
    # 텍스트 리포트 저장
    report_file = os.path.join(output_dir, "analysis_report.txt")
    save_text_report(report_file, summary, scores_by_context_length, scores_by_depth, score_ranges, all_scores)
    print(f"📝 텍스트 리포트가 저장되었습니다: {report_file}")


def create_heatmap(heatmap_data, output_dir, model_name):
    """
    컨텍스트 길이와 문서 깊이에 따른 점수 히트맵을 생성합니다.
    
    Args:
        heatmap_data: (context_length, depth) -> score 딕셔너리
        output_dir: 출력 디렉토리
        model_name: 모델 이름
    """
    if not heatmap_data:
        print("히트맵을 생성할 데이터가 없습니다.")
        return
    
    # 고유한 컨텍스트 길이와 깊이 추출
    context_lengths = sorted(set(k[0] for k in heatmap_data.keys()))
    depths = sorted(set(k[1] for k in heatmap_data.keys()))
    
    # 히트맵 매트릭스 생성
    matrix = np.full((len(depths), len(context_lengths)), np.nan)
    
    for i, depth in enumerate(depths):
        for j, context_length in enumerate(context_lengths):
            if (context_length, depth) in heatmap_data:
                matrix[i, j] = heatmap_data[(context_length, depth)]
    
    # 한글 폰트 설정 (Windows)
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    # 히트맵 그리기
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 색상 맵 설정 (빨강-노랑-초록)
    cmap = sns.diverging_palette(10, 130, as_cmap=True)
    
    sns.heatmap(
        matrix,
        xticklabels=[f"{cl//1000}K" for cl in context_lengths],
        yticklabels=[f"{d:.0f}%" for d in depths],
        annot=True,
        fmt='.1f',
        cmap=cmap,
        vmin=0,
        vmax=10,
        cbar_kws={'label': '점수 (Score)'},
        linewidths=0.5,
        linecolor='gray',
        ax=ax
    )
    
    ax.set_xlabel('컨텍스트 길이 (Context Length)', fontsize=12, fontweight='bold')
    ax.set_ylabel('문서 깊이 (Document Depth)', fontsize=12, fontweight='bold')
    ax.set_title(f'Needle In Haystack 테스트 결과 히트맵\n모델: {model_name}', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # 저장
    heatmap_file = os.path.join(output_dir, "heatmap.png")
    plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ 히트맵 생성 완료: {heatmap_file}")


def save_text_report(report_file, summary, scores_by_context_length, scores_by_depth, score_ranges, all_scores):
    """
    텍스트 형식의 분석 리포트를 저장합니다.
    """
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("Needle In Haystack 테스트 결과 분석 리포트\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"분석 시간: {summary['analysis_timestamp']}\n")
        f.write(f"소스 디렉토리: {summary['source_directory']}\n\n")
        
        f.write("📊 전체 통계:\n")
        f.write(f"  총 테스트 수: {summary['total_tests']}\n")
        f.write(f"  테스트한 모델: {', '.join(summary['models'])}\n")
        f.write(f"  평균 점수: {summary['average_score']:.2f}/10\n")
        f.write(f"  중앙값 점수: {summary['median_score']:.2f}/10\n")
        f.write(f"  최고 점수: {summary['max_score']}/10\n")
        f.write(f"  최저 점수: {summary['min_score']}/10\n")
        f.write(f"  표준 편차: {summary['std_dev']:.2f}\n\n")
        
        f.write("⏱️  성능 통계:\n")
        f.write(f"  평균 테스트 시간: {summary['average_duration']:.2f}초\n")
        f.write(f"  총 테스트 시간: {summary['total_duration']:.2f}초 ({summary['total_duration']/60:.2f}분)\n\n")
        
        f.write("📏 컨텍스트 길이별 평균 점수:\n")
        for context_length in sorted(scores_by_context_length.keys()):
            scores = scores_by_context_length[context_length]
            avg_score = statistics.mean(scores)
            f.write(f"  {context_length:6d} 토큰: {avg_score:5.2f}/10 ({len(scores)}개 테스트)\n")
        
        f.write("\n📍 문서 깊이별 평균 점수:\n")
        for depth in sorted(scores_by_depth.keys()):
            scores = scores_by_depth[depth]
            avg_score = statistics.mean(scores)
            f.write(f"  {depth:5.1f}%: {avg_score:5.2f}/10 ({len(scores)}개 테스트)\n")
        
        f.write("\n📈 점수 분포:\n")
        for range_name, count in score_ranges.items():
            if count > 0:
                percentage = (count / len(all_scores)) * 100
                f.write(f"  {range_name}: {count:3d} ({percentage:5.1f}%)\n")
        
        f.write("\n🏆 최고 성능 테스트:\n")
        f.write(f"  점수: {summary['best_result']['score']}/10\n")
        f.write(f"  컨텍스트 길이: {summary['best_result']['context_length']} 토큰\n")
        f.write(f"  문서 깊이: {summary['best_result']['depth_percent']:.1f}%\n")
        f.write(f"  소요 시간: {summary['best_result']['duration']:.2f}초\n")
        
        f.write("\n⚠️  최저 성능 테스트:\n")
        f.write(f"  점수: {summary['worst_result']['score']}/10\n")
        f.write(f"  컨텍스트 길이: {summary['worst_result']['context_length']} 토큰\n")
        f.write(f"  문서 깊이: {summary['worst_result']['depth_percent']:.1f}%\n")
        f.write(f"  소요 시간: {summary['worst_result']['duration']:.2f}초\n")
        
        f.write("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    import sys
    
    # 커맨드 라인 인자로 결과 디렉토리 지정 가능
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results_kor"
    output_dir = "analyze_results"
    
    print(f"📂 분석할 디렉토리: {results_dir}")
    print(f"📂 결과 저장 디렉토리: {output_dir}\n")
    
    analyze_results(results_dir, output_dir)

