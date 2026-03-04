"""Quick runner for strategy tests - runs each category separately."""
import sys, os, io, unittest, logging

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.disable(logging.WARNING)

from tests.test_strategy_production import (
    TestCategory1_PerfectAnswer,
    TestCategory2_PartialAnswer,
    TestCategory3_KeywordOnly,
    TestCategory4_LongIrrelevant,
    TestCategory5_OCRNoise,
    TestCategory6_SynonymBased,
    TestCrossCategory_Ordering,
    TestConfidence_BloomSanity,
    TestEdgeCases,
)

CLASSES = [
    TestCategory1_PerfectAnswer,
    TestCategory2_PartialAnswer,
    TestCategory3_KeywordOnly,
    TestCategory4_LongIrrelevant,
    TestCategory5_OCRNoise,
    TestCategory6_SynonymBased,
    TestCrossCategory_Ordering,
    TestConfidence_BloomSanity,
    TestEdgeCases,
]

total_run = 0
total_fail = 0
total_error = 0
details = []

for cls in CLASSES:
    suite = unittest.TestLoader().loadTestsFromTestCase(cls)
    buf = io.StringIO()
    runner = unittest.TextTestRunner(verbosity=0, stream=buf)
    try:
        result = runner.run(suite)
    except Exception as e:
        print(f"  [SKIP] {cls.__name__}: setup crashed - {e}")
        sys.stdout.flush()
        continue
    buf.close()

    fails = len(result.failures)
    errors = len(result.errors)
    total_run += result.testsRun
    total_fail += fails
    total_error += errors

    status = "PASS" if (fails + errors) == 0 else "FAIL"
    print(f"  [{status}] {cls.__name__}: {result.testsRun} tests, {fails} failures, {errors} errors")
    sys.stdout.flush()

    for test, tb in result.failures:
        short = tb.strip().split('\n')[-1][:120]
        short = short.encode('ascii', 'replace').decode('ascii')
        details.append(f"    FAIL: {test} -> {short}")
    for test, tb in result.errors:
        short = tb.strip().split('\n')[-1][:120]
        short = short.encode('ascii', 'replace').decode('ascii')
        details.append(f"    ERROR: {test} -> {short}")

print(f"\n{'='*60}")
print(f"TOTAL: {total_run} tests | {total_fail} failures | {total_error} errors")
print(f"{'='*60}")

if details:
    print("\nDetails:")
    for d in details:
        print(d)
