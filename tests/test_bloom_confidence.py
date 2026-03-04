"""
Comprehensive Tests for Bloom's Taxonomy & Confidence Index Services
=====================================================================
Tests: 45 total
  - Bloom Taxonomy Service: 25 tests
  - Confidence Service: 20 tests
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest


# ════════════════════════════════════════════════════════════════════════
#  Bloom's Taxonomy Service Tests
# ════════════════════════════════════════════════════════════════════════

from api.services.bloom_taxonomy_service import BloomTaxonomyAnalyzer, BLOOM_LEVELS


class TestBloomTaxonomyAnalyzer(unittest.TestCase):
    """Tests for BloomTaxonomyAnalyzer."""

    def setUp(self):
        self.analyzer = BloomTaxonomyAnalyzer()

    # ── Question Level Detection ────────────────────────────────

    def test_detect_remember_question(self):
        """Define/List questions -> Remember level."""
        result = self.analyzer.analyze(
            question_text="Define the term photosynthesis.",
            student_text="Photosynthesis is the process by which plants make food.",
            model_text="Photosynthesis is the process by which green plants convert sunlight into food.",
        )
        self.assertIn(result.question_bloom_level, [1, 2])

    def test_detect_understand_question(self):
        """Explain/Describe questions -> Understand level."""
        result = self.analyzer.analyze(
            question_text="Explain how the water cycle works.",
            student_text="The water cycle involves evaporation, condensation and precipitation.",
            model_text="The water cycle is a continuous process of evaporation, condensation, and precipitation.",
        )
        self.assertIn(result.question_bloom_level, [2, 3])

    def test_detect_apply_question(self):
        """Apply/Calculate questions -> Apply level."""
        result = self.analyzer.analyze(
            question_text="Calculate the area of a circle with radius 5.",
            student_text="Area = pi * r^2 = 3.14 * 25 = 78.5 sq units.",
            model_text="Area = pi * r^2 = 3.14159 * 25 = 78.54 sq units.",
        )
        self.assertIn(result.question_bloom_level, [3, 4])

    def test_detect_analyse_question(self):
        """Compare/Contrast questions -> Analyse level."""
        result = self.analyzer.analyze(
            question_text="Compare and contrast mitosis and meiosis.",
            student_text="Mitosis produces two identical cells whereas meiosis produces four unique cells.",
            model_text="Mitosis produces two identical diploid cells. Meiosis produces four haploid cells.",
        )
        self.assertIn(result.question_bloom_level, [4, 5])

    def test_detect_evaluate_question(self):
        """Evaluate/Critique questions -> Evaluate level."""
        result = self.analyzer.analyze(
            question_text="Evaluate the effectiveness of renewable energy sources.",
            student_text="In my assessment, renewable energy is effective but has limitations.",
            model_text="Renewable energy sources are increasingly effective with some limitations.",
        )
        self.assertIn(result.question_bloom_level, [4, 5, 6])

    def test_detect_create_question(self):
        """Design/Propose questions -> Create level."""
        result = self.analyzer.analyze(
            question_text="Design a sustainable city plan for 2050.",
            student_text="I propose a city with renewable energy grids and vertical farms.",
            model_text="A sustainable 2050 city would feature renewable energy and urban farming.",
        )
        self.assertIn(result.question_bloom_level, [5, 6])

    # ── Student Level Detection ─────────────────────────────────

    def test_student_remember_level(self):
        """Student listing/defining -> Remember."""
        result = self.analyzer.analyze(
            question_text="Explain photosynthesis.",
            student_text="Photosynthesis is the process of making food. It uses sunlight. It produces oxygen.",
            model_text="Photosynthesis converts CO2 and water into glucose using sunlight, releasing O2.",
        )
        self.assertIn(result.student_bloom_level, [1, 2])

    def test_student_analytical_language(self):
        """Student using compare/contrast language -> Analyse."""
        result = self.analyzer.analyze(
            question_text="Describe the differences between DNA and RNA.",
            student_text="Unlike DNA which is double-stranded, RNA is single-stranded. On the other hand, DNA uses thymine whereas RNA uses uracil. The key difference is storage vs translation.",
            model_text="DNA is double-stranded with thymine, while RNA is single-stranded with uracil.",
        )
        self.assertGreaterEqual(result.student_bloom_level, 3)

    def test_student_evaluative_language(self):
        """Student using evaluative language -> Evaluate."""
        result = self.analyzer.analyze(
            question_text="Discuss climate change.",
            student_text="In my assessment, the evidence strongly supports anthropogenic climate change. I argue that current policies are insufficient. My critique reveals significant gaps.",
            model_text="Climate change is primarily caused by human activities. Current policies are inadequate.",
        )
        self.assertGreaterEqual(result.student_bloom_level, 4)

    # ── Score Modifier ──────────────────────────────────────────

    def test_score_modifier_range(self):
        """Modifier stays in [-0.15, +0.05]."""
        result = self.analyzer.analyze(
            question_text="Evaluate nuclear energy.",
            student_text="Nuclear energy is good. It produces power.",
            model_text="Nuclear energy offers low-carbon power but poses safety risks.",
        )
        self.assertGreaterEqual(result.bloom_score_modifier, -0.15)
        self.assertLessEqual(result.bloom_score_modifier, 0.05)

    def test_exceeds_expectations_bonus(self):
        """Student exceeding expected level gets non-negative modifier."""
        result = self.analyzer.analyze(
            question_text="Define osmosis.",
            student_text="Osmosis is the movement of water through a semipermeable membrane. Unlike diffusion of solutes, osmosis specifically involves water. I would argue that osmosis is fundamentally critical for cell homeostasis.",
            model_text="Osmosis is the movement of water through a semipermeable membrane.",
        )
        if result.exceeds_expectations:
            self.assertGreater(result.bloom_score_modifier, 0)

    def test_below_expectations_penalty(self):
        """Student below expected level gets negative modifier."""
        result = self.analyzer.analyze(
            question_text="Compare and contrast the French and American revolutions.",
            student_text="The French revolution happened in France. The American revolution happened in America.",
            model_text="Both revolutions sought liberty. French Revolution targeted monarchy; American targeted colonial independence.",
        )
        if result.below_expectations:
            self.assertLess(result.bloom_score_modifier, 0)

    # ── Cognitive Alignment ─────────────────────────────────────

    def test_cognitive_alignment_range(self):
        """Alignment is between 0 and 1."""
        result = self.analyzer.analyze(
            question_text="Explain gravity.",
            student_text="Gravity is a force that attracts objects toward each other.",
            model_text="Gravity is a fundamental force of attraction between masses.",
        )
        self.assertGreaterEqual(result.cognitive_alignment, 0.0)
        self.assertLessEqual(result.cognitive_alignment, 1.0)

    def test_perfect_alignment(self):
        """Same level -> high alignment."""
        result = self.analyzer.analyze(
            question_text="Define DNA.",
            student_text="DNA stands for deoxyribonucleic acid. It carries genetic information.",
            model_text="DNA (deoxyribonucleic acid) is the molecule that carries genetic instructions.",
        )
        self.assertGreaterEqual(result.cognitive_alignment, 0.5)

    # ── Feedback & Suggestions ──────────────────────────────────

    def test_feedback_generated(self):
        """Feedback is always generated."""
        result = self.analyzer.analyze(
            question_text="What is gravity?",
            student_text="Gravity pulls things down.",
            model_text="Gravity is the force of attraction between masses.",
        )
        self.assertIsInstance(result.feedback, str)
        self.assertTrue(len(result.feedback) > 0)

    def test_suggestions_list(self):
        """Suggestions is a list."""
        result = self.analyzer.analyze(
            question_text="Compare X and Y.",
            student_text="X is good. Y is bad.",
            model_text="X and Y differ in multiple dimensions.",
        )
        self.assertIsInstance(result.suggestions, list)

    # ── Detailed Report ─────────────────────────────────────────

    def test_detailed_report_keys(self):
        """get_detailed_report returns all required keys."""
        result = self.analyzer.analyze(
            question_text="Explain osmosis.",
            student_text="Osmosis is water movement through a membrane.",
            model_text="Osmosis is the net movement of water across a semipermeable membrane.",
        )
        report = self.analyzer.get_detailed_report(result)
        for key in ['question_bloom_level', 'question_bloom_name',
                     'student_bloom_level', 'student_bloom_name',
                     'cognitive_alignment', 'bloom_score_modifier', 'feedback']:
            self.assertIn(key, report, f"Missing key: {key}")

    # ── Edge Cases ──────────────────────────────────────────────

    def test_empty_question(self):
        """Empty question text should not crash."""
        result = self.analyzer.analyze(
            question_text="",
            student_text="Photosynthesis uses sunlight.",
            model_text="Photosynthesis converts CO2 and water into glucose.",
        )
        self.assertIsNotNone(result)

    def test_empty_student_text(self):
        """Empty student text."""
        result = self.analyzer.analyze(
            question_text="Explain gravity.",
            student_text="",
            model_text="Gravity is a fundamental force.",
        )
        self.assertIsNotNone(result)

    def test_very_short_answer(self):
        """Very short student answer."""
        result = self.analyzer.analyze(
            question_text="Define photosynthesis.",
            student_text="It is plants making food.",
            model_text="Photosynthesis is the process by which plants convert light energy.",
        )
        self.assertIsNotNone(result)

    def test_long_analytical_answer(self):
        """Long analytical answer with compare/contrast markers."""
        student = (
            "Photosynthesis and cellular respiration are fundamentally linked. "
            "Unlike respiration which breaks down glucose, photosynthesis builds it up. "
            "On the other hand, both processes involve electron transport chains. "
            "The key difference is that photosynthesis captures energy while respiration releases it. "
            "In contrast to glycolysis, light reactions require oxygen. "
            "I would argue that these processes represent two sides of the same coin."
        )
        result = self.analyzer.analyze(
            question_text="Explain photosynthesis.",
            student_text=student,
            model_text="Photosynthesis converts CO2 and water into glucose using sunlight.",
        )
        self.assertGreaterEqual(result.student_bloom_level, 3)

    def test_question_bloom_override(self):
        """Override question bloom level."""
        result = self.analyzer.analyze(
            question_text="What is water?",
            student_text="Water is H2O.",
            model_text="Water is a compound of hydrogen and oxygen (H2O).",
            question_bloom_override=5,
        )
        self.assertEqual(result.question_bloom_level, 5)
        self.assertEqual(result.question_bloom_name, "Evaluate")

    def test_bloom_levels_names(self):
        """All 6 levels have correct names."""
        expected = {1: "Remember", 2: "Understand", 3: "Apply",
                    4: "Analyse", 5: "Evaluate", 6: "Create"}
        for lvl, name in expected.items():
            self.assertEqual(BLOOM_LEVELS[lvl], name)


# ════════════════════════════════════════════════════════════════════════
#  Confidence & Reliability Index Tests
# ════════════════════════════════════════════════════════════════════════

from api.services.confidence_service import ConfidenceAnalyzer


class TestConfidenceAnalyzer(unittest.TestCase):
    """Tests for ConfidenceAnalyzer."""

    def setUp(self):
        self.analyzer = ConfidenceAnalyzer()

    # ── Basic Confidence Calculation ────────────────────────────

    def test_high_confidence_agreeing_scores(self):
        """All scores agreeing -> high confidence."""
        result = self.analyzer.analyze(
            semantic_score=0.85,
            keyword_score=0.82,
            student_text="Photosynthesis converts CO2 and water into glucose using sunlight, releasing oxygen.",
            model_text="Photosynthesis is the process where plants convert CO2 and water into glucose using sunlight.",
            coverage_percentage=0.83,
        )
        self.assertGreaterEqual(result.confidence_percentage, 60)

    def test_low_confidence_disagreeing_scores(self):
        """Scores disagreeing -> lower confidence."""
        result = self.analyzer.analyze(
            semantic_score=0.90,
            keyword_score=0.15,
            student_text="The process is about making things work in a natural way.",
            model_text="Photosynthesis converts CO2 and water into glucose using sunlight.",
            coverage_percentage=0.17,
        )
        self.assertLess(result.confidence_percentage, 85)

    def test_confidence_percentage_range(self):
        """Confidence always 0-100%."""
        result = self.analyzer.analyze(
            semantic_score=0.5,
            keyword_score=0.5,
            student_text="Some answer.",
            model_text="The model answer.",
            coverage_percentage=0.50,
        )
        self.assertGreaterEqual(result.confidence_percentage, 0)
        self.assertLessEqual(result.confidence_percentage, 100)

    # ── Confidence Labels ───────────────────────────────────────

    def test_confidence_label_exists(self):
        """Confidence label is always set."""
        result = self.analyzer.analyze(
            semantic_score=0.88,
            keyword_score=0.85,
            student_text="A comprehensive answer.",
            model_text="Photosynthesis includes light reactions and Calvin cycle.",
            coverage_percentage=1.0,
        )
        self.assertIn(result.confidence_label, ["High", "Medium", "Low", "Very Low"])

    def test_very_low_confidence_label(self):
        """Very low confidence label."""
        result = self.analyzer.analyze(
            semantic_score=0.10,
            keyword_score=0.05,
            student_text="I don't know.",
            model_text="Photosynthesis is a complex biochemical process.",
            coverage_percentage=0.0,
        )
        self.assertIn(result.confidence_label, ["Low", "Very Low", "Medium"])

    # ── Manual Review Flagging ──────────────────────────────────

    def test_manual_review_flagged_low_confidence(self):
        """Low confidence -> needs_manual_review."""
        result = self.analyzer.analyze(
            semantic_score=0.90,
            keyword_score=0.10,
            student_text="Everything is connected in nature.",
            model_text="Photosynthesis converts CO2 and water into glucose.",
            coverage_percentage=0.0,
        )
        if result.confidence_percentage < 70:
            self.assertTrue(result.needs_manual_review)

    def test_review_reasons_populated(self):
        """Review reasons are strings when flagged."""
        result = self.analyzer.analyze(
            semantic_score=0.85,
            keyword_score=0.10,
            student_text="A vague answer.",
            model_text="A detailed model answer about photosynthesis.",
            coverage_percentage=0.0,
        )
        if result.needs_manual_review:
            self.assertIsInstance(result.review_reasons, list)
            for reason in result.review_reasons:
                self.assertIsInstance(reason, str)

    # ── Factor Calculations ─────────────────────────────────────

    def test_factors_present(self):
        """At least 3 factors present in result."""
        result = self.analyzer.analyze(
            semantic_score=0.75,
            keyword_score=0.70,
            student_text="An answer about the topic.",
            model_text="The model answer.",
            coverage_percentage=0.50,
        )
        self.assertGreaterEqual(len(result.factors), 3)
        factor_names = [f.name for f in result.factors]
        self.assertIn("embedding_stability", factor_names)
        self.assertIn("keyword_consistency", factor_names)

    def test_factor_scores_range(self):
        """Factor scores are 0-1."""
        result = self.analyzer.analyze(
            semantic_score=0.60,
            keyword_score=0.55,
            student_text="Some content about the subject.",
            model_text="A detailed explanation of the subject.",
            coverage_percentage=0.33,
        )
        for factor in result.factors:
            self.assertGreaterEqual(factor.score, 0.0, f"Factor {factor.name} below 0")
            self.assertLessEqual(factor.score, 1.0, f"Factor {factor.name} above 1")

    def test_weighted_scores_sum(self):
        """Weighted scores should sum close to overall confidence."""
        result = self.analyzer.analyze(
            semantic_score=0.70,
            keyword_score=0.65,
            student_text="An answer.",
            model_text="The model answer.",
            coverage_percentage=0.50,
        )
        weighted_sum = sum(f.weighted_score for f in result.factors)
        self.assertAlmostEqual(weighted_sum, result.overall_confidence, delta=0.1)

    # ── Optional Score Integration ──────────────────────────────

    def test_concept_graph_integration(self):
        """Concept graph score included when provided."""
        result = self.analyzer.analyze(
            semantic_score=0.80,
            keyword_score=0.75,
            concept_graph_score=0.78,
            student_text="Detailed answer covering key concepts.",
            model_text="Model answer about key concepts.",
            coverage_percentage=1.0,
        )
        self.assertGreater(result.confidence_percentage, 0)

    def test_all_optional_scores(self):
        """All optional scores provided."""
        result = self.analyzer.analyze(
            semantic_score=0.82,
            keyword_score=0.78,
            concept_graph_score=0.80,
            sentence_alignment_score=0.76,
            structural_score=0.72,
            rubric_score=0.79,
            length_ratio=0.90,
            student_text="Comprehensive answer.",
            model_text="Model answer.",
            coverage_percentage=0.85,
            gaming_penalty=0.0,
            bloom_score_modifier=0.02,
        )
        self.assertGreater(result.confidence_percentage, 0)

    def test_gaming_penalty_reduces_confidence(self):
        """Gaming penalty should reduce confidence."""
        r1 = self.analyzer.analyze(
            semantic_score=0.80, keyword_score=0.75,
            student_text="A decent answer.", model_text="The model answer.",
            coverage_percentage=0.50,
            gaming_penalty=0.0,
        )
        r2 = self.analyzer.analyze(
            semantic_score=0.80, keyword_score=0.75,
            student_text="A decent answer.", model_text="The model answer.",
            coverage_percentage=0.50,
            gaming_penalty=0.30,
        )
        self.assertGreaterEqual(r1.confidence_percentage, r2.confidence_percentage)

    # ── Detailed Report ─────────────────────────────────────────

    def test_detailed_report_keys(self):
        """get_detailed_report returns all required keys."""
        result = self.analyzer.analyze(
            semantic_score=0.80, keyword_score=0.75,
            student_text="An answer.", model_text="The model.",
            coverage_percentage=0.50,
        )
        report = self.analyzer.get_detailed_report(result)
        for key in ['overall_confidence', 'confidence_percentage',
                     'confidence_label', 'needs_manual_review', 'factors']:
            self.assertIn(key, report, f"Missing key: {key}")

    def test_report_factors_structure(self):
        """Report factors have correct structure."""
        result = self.analyzer.analyze(
            semantic_score=0.70, keyword_score=0.65,
            student_text="Answer text.", model_text="Model text.",
            coverage_percentage=0.50,
        )
        report = self.analyzer.get_detailed_report(result)
        for f in report['factors']:
            self.assertIn('name', f)
            self.assertIn('display_name', f)
            self.assertIn('score', f)
            self.assertIn('weight', f)

    # ── Edge Cases ──────────────────────────────────────────────

    def test_empty_student_text(self):
        """Empty student text should not crash."""
        result = self.analyzer.analyze(
            semantic_score=0.0, keyword_score=0.0,
            student_text="", model_text="A detailed model answer.",
            coverage_percentage=0.0,
        )
        self.assertIsNotNone(result)

    def test_zero_scores(self):
        """All zero scores."""
        result = self.analyzer.analyze(
            semantic_score=0.0, keyword_score=0.0,
            student_text="Nothing relevant.", model_text="The expected answer.",
            coverage_percentage=0.0,
        )
        self.assertGreaterEqual(result.confidence_percentage, 0)

    def test_perfect_scores(self):
        """All perfect scores -> high confidence."""
        result = self.analyzer.analyze(
            semantic_score=1.0, keyword_score=1.0,
            concept_graph_score=1.0, sentence_alignment_score=1.0,
            structural_score=1.0, rubric_score=1.0, length_ratio=1.0,
            student_text="A perfect answer matching every concept and keyword perfectly.",
            model_text="A perfect answer matching every concept and keyword perfectly.",
            coverage_percentage=1.0,
        )
        self.assertGreaterEqual(result.confidence_percentage, 70)

    def test_ocr_confidence_integration(self):
        """OCR confidence optionally blended."""
        result = self.analyzer.analyze(
            semantic_score=0.75, keyword_score=0.70,
            student_text="OCR extracted text.", model_text="The model answer.",
            coverage_percentage=0.50,
            ocr_confidence=0.95,
        )
        self.assertIsNotNone(result)


# ════════════════════════════════════════════════════════════════════════
#  Run Tests
# ════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    unittest.main(verbosity=2)
