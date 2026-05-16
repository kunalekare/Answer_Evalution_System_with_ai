# Quick Start - How to Use Question-Wise Evaluation

## 🚀 Quick Start (2 minutes)

### Step 1: Open Evaluate Page
```
Navigate to: http://localhost:3000/evaluate
```

### Step 2: Upload PDFs
1. **Drag & drop or click to upload**
   - Model Answer PDF (the teacher's/correct answer)
   - Student Answer PDF (the student's answer)

2. **System extracts text automatically**
   - Cached in `.cache/` folder
   - Used for both evaluation modes

### Step 3: Configure Settings

Set your evaluation parameters:
- **Question Type**: Descriptive (or Factual/Diagram/Mixed)
- **Max Marks**: 40 (or 10/20/50/100)
- **OCR Engine**: EasyOCR (or Ensemble/Tesseract/Sarvam)

**IMPORTANT: Click "Question Wise Evaluate" button** ⭐
- Button should appear in Configure Settings
- Click to toggle it ON (should show as active/highlighted)

### Step 4: Click "Evaluate" Button
```
Wait 2-3 minutes for evaluation to complete
(First run includes model setup - subsequent runs faster)
```

### Step 5: View Per-Question Results

Results page shows:
```
Q1: 9/10 (90% - A+)
    └─ Detailed Feedback
    └─ Suggestions
    └─ Concept Coverage

Q2: 7/10 (70% - B+)
    └─ Detailed Feedback
    └─ Suggestions
    └─ Concept Coverage

Q3: 10/10 (100% - A+)
    └─ Detailed Feedback
    └─ Suggestions
    └─ Concept Coverage

Q4: 8/10 (80% - A)
    └─ Detailed Feedback
    └─ Suggestions
    └─ Concept Coverage

─────────────────────────
OVERALL: 34/40 (85% - A+)
```

---

## 📱 Expected Result Format

### Before (Overall Evaluation Only)
```
Score: 34/40
Percentage: 85%
Grade: A+
Feedback: "Good answer with minor improvements needed"
```

### After (Per-Question Breakdown)
```
Question 1/4
Score: 9/10 | Percentage: 90% | Grade: A+
Details: "Excellent coverage of all key concepts"
Suggestions: ["Add more examples"]

Question 2/4
Score: 7/10 | Percentage: 70% | Grade: B+
Details: "Missing some important points"
Suggestions: ["Explain definition of X", "Provide case study"]

...and so on

OVERALL: 34/40 (85% - A+)
```

---

## ✅ Verification Checklist

Copy this list and check as you go:

```
UPLOADING:
☐ Model answer PDF uploaded successfully
☐ Student answer PDF uploaded successfully
☐ Text extraction complete (shows extracted text preview)

CONFIGURATION:
☐ Question Type selected
☐ Max Marks set to 40 (or your value)
☐ "Question Wise Evaluate" button visible
☐ "Question Wise Evaluate" button toggled ON (highlighted)

EVALUATING:
☐ Clicked Evaluate button
☐ System shows loading/processing message
☐ Waiting 2-3 minutes

RESULTS:
☐ Results page shows per-question breakdown
☐ Each question shows: "Q1: 9/10", "Q2: 7/10", etc.
☐ Each question expandable with detailed feedback
☐ Overall summary shows at bottom: "OVERALL: 34/40 (85%)"
☐ All 4 questions visible with their scores

SUCCESS: All checked ✓
```

---

## 🔧 Troubleshooting

### Q: I don't see "Question Wise Evaluate" button
**A**: 
- Refresh the page (Ctrl+R or Cmd+R)
- Check browser console for errors (F12 → Console tab)
- Try a different browser

### Q: Button is visible but clicking it does nothing
**A**:
- Check that `multiQuestionMode` state is updating
- Open DevTools (F12) → Network tab
- When you click Evaluate, look for POST request to `/api/v1/evaluate/`
- Check if `"multi_question_mode": true` is present in request body

### Q: Evaluation still shows overall score, not per-question
**A**:
1. Check Network tab - is `"multi_question_mode": true` sent?
2. Check backend logs (terminal running backend)
   - Should show: `🔄 [MULTI-QUESTION MODE]`
   - If not showing, flag not being sent
3. Verify PDFs have at least 2 questions
4. Check `.cache/` folder exists with extracted text

### Q: Gets error "Cached text not found"
**A**:
- Re-upload the PDF files
- Ensure model_answer PDF and student_answer PDF are uploaded
- Check that extraction completed successfully

### Q: Evaluation takes much longer than 2-3 minutes
**A**:
- First run: 2-3 minutes is normal (includes model setup)
- Subsequent runs: Faster (models cached)
- Multi-question: Same time as overall (uses cached text)

### Q: Results page blank or crashes
**A**:
- Check browser console for JavaScript errors
- Try opening Fresh evaluation
- Clear browser cache (might have stale code)

---

## 📊 Example Output

### Input PDFs
```
MODEL ANSWER (teacher):
"Q1. Define photosynthesis...
Q2. Explain the water cycle...
Q3. What are the causes of climate change?
Q4. Describe the carbon cycle..."

STUDENT ANSWER:
"Q1. Photosynthesis is when plants make food...
Q2. Water evaporates and forms clouds...
Q3. CO2 emissions and deforestation...
Q4. Carbon moves between atmosphere, soil..."
```

### Output - Per-Question Evaluation
```
Q1: 9/10 (90% - A+)
├─ Semantic Match: 45/50 (Good definition, all key concepts)
├─ Keywords: 25/30 (Covered: photosynthesis, plants, energy)
├─ Structure: 15/15 (Well organized)
├─ Concepts: 5/5 (All required concepts present)
└─ Suggestions: "Could add info on light vs dark reactions"

Q2: 8/10 (80% - A)
├─ Semantic Match: 40/50 (Good explanation, minor gaps)
├─ Keywords: 25/30 (Covered: water, cycle, evaporation)
├─ Structure: 12/15 (Decent structure)
├─ Concepts: 3/5 (Missing: condensation details)
└─ Suggestions: "Explain how clouds lead to precipitation"

...more questions...

OVERALL: 34/40 (85% - A+)
```

---

## 🎯 Use Cases

### For Teachers
- Evaluate student answers question by question
- Identify weak areas (which specific questions students struggle with)
- Provide targeted feedback for each question
- Compare performance across questions in a test

### For Students
- Understand which questions need improvement
- Get specific feedback for each question
- Track understanding of different topics
- Practice weak areas more focused

### For Administrators
- Analyze overall test difficulty
- Identify challenging questions
- Monitor student progress by question
- Generate detailed evaluation reports

---

## ⚡ Performance

```
Single PDF with 4 questions:
- Upload & Extract: 30 seconds
- Per-question Evaluation: 2-3 minutes total (all 4 at once)
- Results rendering: <1 second

Total Time: ~3-4 minutes
```

---

## 📝 Notes

- **Compatible with**: All question types (Factual, Descriptive, Diagram, Mixed)
- **Supported marks**: 10, 20, 40, 50, 100, or any custom value
- **PDF formats**: Any searchable PDF
- **Languages**: English (primary), other languages depends on OCR engine
- **Browser**: Chrome, Firefox, Safari, Edge (tested on Chrome)

---

## 🆘 Getting Help

If something doesn't work:

1. **Check the logs**:
   - Backend terminal: Look for "🔄 [MULTI-QUESTION MODE]"
   - Browser console: F12 → Console tab
   - Network tab: F12 → Network → Check `/api/v1/evaluate/` request

2. **Verify the files**:
   - Check `.cache/model_extracted.txt` exists
   - Check `.cache/student_extracted.txt` exists
   - Check content is not empty

3. **Try again**:
   - Re-upload files
   - Refresh page
   - Restart backend

---

## 🎉 You're Ready!

Now you can:
✓ Upload PDFs
✓ Click "Question Wise Evaluate"
✓ Get per-question scores
✓ See detailed feedback for each question
✓ Track student performance by topic

**Enjoy the new feature!** 🚀
