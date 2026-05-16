/**
 * Question Segmentation Utilities
 * ================================
 * Helpers for extracting and displaying questions from raw text.
 * Used in the Preview and Results step to show question-wise breakdown.
 */

/**
 * Patterns for detecting questions in text
 */
const QUESTION_PATTERNS = [
  /^[ \t]*[Qq]\.?\s*(\d{1,3})\s*[.):]/,      // Q1. or Q 1)
  /^[ \t]*(?:Question|QUESTION|Ques|Que)\s+(\d{1,3})/,  // Question 1
  /^[ \t]*(\d{1,3})\s*[.):\-]/,               // 1. or 1)
  /^[ \t]*(?:Ans(?:wer)?)\s*\.?\s*(\d{1,3})/,  // Ans 1
];

/**
 * Extract questions from raw text
 * Returns array of question objects with number, header, and content
 */
export const extractQuestions = (text) => {
  if (!text || typeof text !== 'string') return [];

  const lines = text.split('\n');
  const questions = [];
  let currentQuestion = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const stripped = line.trim();

    if (!stripped) {
      if (currentQuestion) {
        currentQuestion.content += '\n';
      }
      continue;
    }

    // Try to match question pattern
    let matched = false;
    for (const pattern of QUESTION_PATTERNS) {
      const match = line.match(pattern);
      if (match) {
        // Save previous question
        if (currentQuestion) {
          questions.push(currentQuestion);
        }

        // Start new question
        currentQuestion = {
          number: parseInt(match[1]),
          header: stripped,
          content: stripped,
          lines: [stripped],
        };
        matched = true;
        break;
      }
    }

    if (!matched && currentQuestion) {
      currentQuestion.content += '\n' + line;
      currentQuestion.lines.push(line);
    }
  }

  // Add last question
  if (currentQuestion) {
    questions.push(currentQuestion);
  }

  return questions;
};

/**
 * Format extracted questions for display
 * Cleans up whitespace and normalizes formatting
 */
export const formatQuestionsForDisplay = (questions) => {
  return questions.map((q) => ({
    ...q,
    displayContent: q.content
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .join('\n'),
  }));
};

/**
 * Detect whether text has proper question structure
 * Returns confidence score (0-1) and details
 */
export const analyzeQuestionStructure = (text) => {
  const questions = extractQuestions(text);

  let score = 0;
  const issues = [];

  // Check if questions were detected
  if (questions.length === 0) {
    score = 0.1;
    issues.push('No questions detected in text');
    return { score, questions: 0, issues };
  }

  // Check for sequential numbering
  const numbers = questions.map((q) => q.number);
  const isSequential = numbers.every((n, i) => n === i + 1);

  if (isSequential) {
    score += 0.5;
  } else {
    score += 0.2;
    issues.push('Question numbers are not sequential');
  }

  // Check average content length
  const avgLength = questions.reduce((sum, q) => sum + q.content.length, 0) / questions.length;
  if (avgLength > 50) {
    score += 0.3;
  } else {
    score += 0.1;
    issues.push('Questions appear too short or fragmented');
  }

  // Check for reasonable number of questions
  if (questions.length >= 2 && questions.length <= 20) {
    score += 0.2;
  } else if (questions.length === 1) {
    score += 0.1;
  } else {
    score -= 0.1;
    issues.push(`Unusual number of questions detected: ${questions.length}`);
  }

  return {
    score: Math.min(1, score),
    questions: questions.length,
    issues,
    details: {
      sequential: isSequential,
      avgContentLength: Math.round(avgLength),
      minContentLength: Math.min(...questions.map((q) => q.content.length)),
      maxContentLength: Math.max(...questions.map((q) => q.content.length)),
    },
  };
};

/**
 * Split text into clean question-answer pairs
 * For display in Configure Settings when Question Wise mode is selected
 */
export const segmentQuestionsForPreview = (modelText, studentText) => {
  const modelQuestions = extractQuestions(modelText);
  const studentQuestions = extractQuestions(studentText);

  const segments = [];

  // Match questions by number
  for (let i = 0; i < Math.max(modelQuestions.length, studentQuestions.length); i++) {
    const modelQ = modelQuestions[i];
    const studentQ = studentQuestions[i];

    segments.push({
      number: i + 1,
      model: modelQ ? modelQ.content : 'Not provided',
      student: studentQ ? studentQ.content : 'Not answered',
      modelContent: modelQ?.displayContent || '',
      studentContent: studentQ?.displayContent || '',
    });
  }

  return segments;
};

/**
 * Check if text needs improvement for question-wise evaluation
 * Returns suggestions for better results
 */
export const getQuestionsQualityFeedback = (modelText, studentText) => {
  const modelAnalysis = analyzeQuestionStructure(modelText);
  const studentAnalysis = analyzeQuestionStructure(studentText);

  const feedback = {
    modelQuality: modelAnalysis.score,
    studentQuality: studentAnalysis.score,
    overallQuality: (modelAnalysis.score + studentAnalysis.score) / 2,
    suggestions: [],
  };

  if (modelAnalysis.score < 0.5) {
    feedback.suggestions.push('Model answer text needs better question formatting');
  }

  if (studentAnalysis.score < 0.5) {
    feedback.suggestions.push('Student answer text needs better question formatting');
  }

  // Check for matching question counts
  if (Math.abs(modelAnalysis.questions - studentAnalysis.questions) > 2) {
    feedback.suggestions.push(
      `Model has ${modelAnalysis.questions} questions, Student has ${studentAnalysis.questions}. Consider reviewing extracted text.`
    );
  }

  if (feedback.overallQuality >= 0.7) {
    feedback.suggestions.push('✓ Text is well-formatted for question-wise evaluation');
  }

  return feedback;
};

export default {
  extractQuestions,
  formatQuestionsForDisplay,
  analyzeQuestionStructure,
  segmentQuestionsForPreview,
  getQuestionsQualityFeedback,
};
