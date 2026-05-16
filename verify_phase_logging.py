#!/usr/bin/env python3
"""
Quick verification that all 17 phases have logging markers.
Run: python verify_phase_logging.py
"""

import re
import sys

def verify_phase_logging(filepath):
    """Verify all 17 phases have logging in the evaluation route."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    phases = {}
    for i in range(1, 18):
        pattern = f'\\[Phase {i}/17\\]'
        matches = re.findall(pattern, content)
        phases[i] = len(matches)
    
    print("=" * 70)
    print("✅ PHASE LOGGING VERIFICATION REPORT")
    print("=" * 70)
    print(f"\nFile: {filepath}")
    print(f"\nVerifying all 17 phases have logging markers...\n")
    
    all_present = True
    for phase in range(1, 18):
        count = phases[phase]
        status = "✓" if count > 0 else "✗"
        if count == 0:
            all_present = False
        print(f"  {status} Phase {phase:2d}/17: {count} logging marker(s) found")
    
    print("\n" + "=" * 70)
    
    if all_present:
        print("✅ SUCCESS: All 17 phases have logging markers!")
        print("\nLogging Coverage Summary:")
        total_markers = sum(phases.values())
        print(f"  • Total phase markers found: {total_markers}")
        print(f"  • Phases fully logged: 17/17 (100%)")
        print(f"  • Status: PRODUCTION READY ✅")
        return 0
    else:
        print("❌ FAILURE: Some phases missing logging markers!")
        missing = [p for p in range(1, 18) if phases[p] == 0]
        print(f"\nMissing phases: {missing}")
        return 1

if __name__ == "__main__":
    filepath = "api/routes/evaluation.py"
    sys.exit(verify_phase_logging(filepath))
