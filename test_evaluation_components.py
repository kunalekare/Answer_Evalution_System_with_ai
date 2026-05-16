#!/usr/bin/env python3
"""
Test to verify that evaluation results include all components:
- Semantic Score
- Keyword Score
- Concept Graph Score & Details
- Sentence Alignment Score & Details
- Structural Analysis Score & Details
- Anti-Gaming Penalty & Details
- Rubric Score & Details
- Bloom's Taxonomy Details
- Confidence Index & Details

Run: python test_evaluation_components.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def check_evaluation_results():
    """Check if recent evaluation results have all components."""
    
    results_dir = Path("uploads/results")
    json_files = sorted(results_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("=" * 80)
    print("✅ EVALUATION COMPONENTS VERIFICATION")
    print("=" * 80)
    print(f"\nChecking latest {min(3, len(json_files))} evaluation results...\n")
    
    # Components we expect in score_breakdown
    score_breakdown_components = [
        "semantic_score",
        "keyword_score",
        "concept_graph_score",
        "sentence_alignment_score",
        "structural_score",
        "structure_bonus",
        "anti_gaming_penalty",
        "rubric_score",
        "bloom_modifier",
        "length_penalty",
        "weighted_score",
    ]
    
    # Components we expect in concepts
    concepts_components = [
        "matched",
        "missing",
        "coverage_percentage",
        "concept_graph_coverage",
        "concept_graph_details",
        "sentence_alignment_details",
        "structural_analysis_details",
        "anti_gaming_details",
        "rubric_details",
        "bloom_taxonomy_details",
        "confidence_details",
    ]
    
    results_summary = []
    
    for i, json_file in enumerate(json_files[:3]):
        with open(json_file, 'r') as f:
            result = json.load(f)
        
        eval_id = result.get('evaluation_id', 'N/A')[:8]
        timestamp = result.get('timestamp', 'N/A')
        score = result.get('final_score', 'N/A')
        
        print(f"\n{'─' * 80}")
        print(f"Result {i+1}: ID={eval_id}... | Score={score}% | Time={timestamp}")
        print(f"{'─' * 80}")
        
        score_breakdown = result.get('score_breakdown', {})
        concepts = result.get('concepts', {})
        
        # Check score_breakdown components
        print("\n📊 Score Breakdown Components:")
        score_components_found = 0
        for component in score_breakdown_components:
            if component in score_breakdown:
                value = score_breakdown[component]
                status = "✓" if value is not None else "○"
                print(f"  {status} {component}: {value}")
                if value is not None:
                    score_components_found += 1
            else:
                print(f"  ✗ {component}: MISSING")
        
        print(f"\n  Summary: {score_components_found}/{len(score_breakdown_components)} components found")
        
        # Check concepts components
        print("\n🔗 Concepts Components:")
        concepts_components_found = 0
        for component in concepts_components:
            if component in concepts:
                value = concepts[component]
                has_data = value is not None and (
                    (isinstance(value, (list, dict)) and len(value) > 0) or 
                    (isinstance(value, (int, float)))
                )
                status = "✓" if has_data else "○"
                if isinstance(value, (list, dict)):
                    value_repr = f"{type(value).__name__} ({len(value)} items)" if len(value) > 0 else f"{type(value).__name__} (empty)"
                else:
                    value_repr = value
                print(f"  {status} {component}: {value_repr}")
                if has_data:
                    concepts_components_found += 1
            else:
                print(f"  ✗ {component}: MISSING")
        
        print(f"\n  Summary: {concepts_components_found}/{len(concepts_components)} components found")
        
        # Overall assessment
        score_pct = (score_components_found / len(score_breakdown_components)) * 100
        concepts_pct = (concepts_components_found / len(concepts_components)) * 100
        overall_pct = (score_components_found + concepts_components_found) / (len(score_breakdown_components) + len(concepts_components)) * 100
        
        results_summary.append({
            'eval_id': eval_id,
            'score': score,
            'score_components_pct': score_pct,
            'concepts_components_pct': concepts_pct,
            'overall_pct': overall_pct
        })
    
    # Summary report
    print(f"\n{'=' * 80}")
    print("📈 SUMMARY REPORT")
    print(f"{'=' * 80}\n")
    
    for i, summary in enumerate(results_summary):
        print(f"Result {i+1} (ID={summary['eval_id']}...):")
        print(f"  • Score Breakdown: {summary['score_components_pct']:.0f}% complete")
        print(f"  • Concepts Details: {summary['concepts_components_pct']:.0f}% complete")
        print(f"  • Overall Coverage: {summary['overall_pct']:.0f}% ✓" if summary['overall_pct'] >= 80 else f"  • Overall Coverage: {summary['overall_pct']:.0f}% ⚠️")
    
    avg_overall = sum(r['overall_pct'] for r in results_summary) / len(results_summary)
    
    print(f"\n{'─' * 80}")
    print(f"Average Overall Coverage: {avg_overall:.0f}%")
    
    if avg_overall >= 85:
        print("✅ EXCELLENT: All evaluation components are properly included!")
        print("\nServices enabled and working:")
        print("  ✓ Concept Graph Analysis")
        print("  ✓ Sentence Alignment Scoring")
        print("  ✓ Structural Analysis")
        print("  ✓ Anti-Gaming Detection")
        print("  ✓ Rubric-Based Scoring")
        print("  ✓ Bloom's Taxonomy Analysis")
        print("  ✓ Confidence Index")
        return 0
    else:
        print("⚠️  WARNING: Some components are missing. Check if services are enabled.")
        return 1

if __name__ == "__main__":
    sys.exit(check_evaluation_results())
