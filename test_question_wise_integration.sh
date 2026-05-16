#!/bin/bash
# Question-Wise Evaluation - System Test Script
# ================================================
# Verifies all components are properly installed and integrated

echo "═══════════════════════════════════════════════════════════════"
echo "  Question-Wise Evaluation System - Integration Test"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_component() {
    local name="$1"
    local command="$2"
    
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════
# BACKEND TESTS
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}BACKEND COMPONENTS${NC}"
echo "─────────────────────────────────────────────────────────────"

test_component "Text Cleaning Service exists" \
    "test -f 'api/services/text_cleaning_service.py'"

test_component "Text Cleaning Service has clean_text method" \
    "grep -q 'def clean_text' api/services/text_cleaning_service.py"

test_component "Text Cleaning Service has clean_for_question_segmentation method" \
    "grep -q 'def clean_for_question_segmentation' api/services/text_cleaning_service.py"

test_component "Text Cleaning Service has OCR_ERRORS dict" \
    "grep -q 'OCR_ERRORS' api/services/text_cleaning_service.py"

test_component "Upload routes integrated with text cleaning" \
    "grep -q 'TextCleaningService' api/routes/upload.py"

test_component "Upload routes import text cleaning" \
    "grep -q 'from api.services.text_cleaning_service import' api/routes/upload.py"

test_component "Question Segmentation Service exists" \
    "test -f 'api/services/question_segmentation_service.py'"

test_component "Evaluation routes exists" \
    "test -f 'api/routes/evaluation.py'"

echo ""

# ═══════════════════════════════════════════════════════════════════
# FRONTEND TESTS
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}FRONTEND COMPONENTS${NC}"
echo "─────────────────────────────────────────────────────────────"

test_component "Question Segmentation utility exists" \
    "test -f 'frontend/src/utils/questionSegmentation.js'"

test_component "Question Segmentation has extractQuestions" \
    "grep -q 'export const extractQuestions' frontend/src/utils/questionSegmentation.js"

test_component "Question Segmentation has analyzeQuestionStructure" \
    "grep -q 'export const analyzeQuestionStructure' frontend/src/utils/questionSegmentation.js"

test_component "Evaluate page exists" \
    "test -f 'frontend/src/pages/Evaluate.jsx'"

test_component "Evaluate page has multiQuestionMode state" \
    "grep -q 'multiQuestionMode' frontend/src/pages/Evaluate.jsx"

test_component "Evaluate page has Question Wise button UI" \
    "grep -q 'Question Wise Evaluate' frontend/src/pages/Evaluate.jsx"

test_component "Results page exists" \
    "test -f 'frontend/src/pages/Results.jsx'"

test_component "Results page handles per_question data" \
    "grep -q 'per_question' frontend/src/pages/Results.jsx"

echo ""

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}CONFIGURATION & SETTINGS${NC}"
echo "─────────────────────────────────────────────────────────────"

test_component "Documentation: Implementation guide exists" \
    "test -f 'QUESTION_WISE_EVALUATION_COMPLETE.md'"

test_component "Documentation: Quick start guide exists" \
    "test -f 'QUESTION_WISE_QUICK_START.md'"

test_component "Settings file exists" \
    "test -f 'config/settings.py' || test -f 'backend/config/settings.py'"

echo ""

# ═══════════════════════════════════════════════════════════════════
# PYTHON SYNTAX TESTS
# ═════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}PYTHON SYNTAX CHECKS${NC}"
echo "─────────────────────────────────────────────────────────────"

if command -v python3 &> /dev/null; then
    test_component "Text Cleaning Service syntax" \
        "python3 -m py_compile api/services/text_cleaning_service.py"
    
    test_component "Upload routes syntax" \
        "python3 -m py_compile api/routes/upload.py"
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Python3 not in PATH)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# JAVASCRIPT SYNTAX TESTS
# ═════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}JAVASCRIPT CHECKS${NC}"
echo "─────────────────────────────────────────────────────────────"

if command -v node &> /dev/null; then
    test_component "Question Segmentation utils syntax" \
        "node -c frontend/src/utils/questionSegmentation.js"
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Node.js not in PATH)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}INTEGRATION CHECKS${NC}"
echo "─────────────────────────────────────────────────────────────"

test_component "Text cleaning can process sample text" \
    "python3 -c 'from api.services.text_cleaning_service import TextCleaningService; TextCleaningService.clean_text(\"Q1. Test\")' 2>/dev/null"

test_component "Question segmentation patterns defined" \
    "grep -q 'QUESTION_PATTERNS' frontend/src/utils/questionSegmentation.js"

test_component "OCR service is available" \
    "test -f 'api/services/ocr_service.py'"

test_component "Evaluation service handles per_question mode" \
    "grep -q 'per_question\\|multiQuestion\\|question_wise' api/routes/evaluation.py"

echo ""

# ═══════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo -e "  Test Summary"
echo "═══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Passed: ${PASSED}${NC}"
echo -e "  ${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! System is ready for use.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start backend:  python run_backend.py"
    echo "  2. Start frontend: cd frontend && npm start"
    echo "  3. Visit:          http://localhost:3000"
    echo "  4. Upload PDF with questions and select 'Question Wise Evaluate'"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the components above.${NC}"
    echo ""
    echo "Common issues:"
    echo "  • Missing files: Ensure all new files are created"
    echo "  • Syntax errors: Check Python/JS syntax"
    echo "  • Import errors: Verify relative imports are correct"
    exit 1
fi
