/**
 * ChatBot Page - AI Teaching Assistant
 * =====================================
 * Intelligent chatbot for evaluation feedback, doubt solving,
 * and learning support.
 * 
 * Features:
 * - Context-aware responses about evaluations
 * - Clear explanation of marks
 * - Improvement suggestions
 * - Doubt solving capability
 * - Practice question generation
 * - Personalized responses based on user role
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  CircularProgress,
  Fade,
  Zoom,
  useTheme,
  useMediaQuery,
  alpha,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Psychology as AIIcon,
  Lightbulb as TipIcon,
  School as LearnIcon,
  QuestionAnswer as QuestionIcon,
  TrendingUp as ImproveIcon,
  AutoAwesome as SparkleIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  History as HistoryIcon,
  Grade as GradeIcon,
  MenuBook as BookIcon,
  EmojiObjects as IdeaIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth, ROLES } from '../context/AuthContext';

const MotionBox = motion(Box);

// Quick action suggestions based on role
const getQuickActions = (role) => {
  const baseActions = [
    { icon: <GradeIcon />, text: 'Explain my latest score', category: 'score' },
    { icon: <ImproveIcon />, text: 'How can I improve my answer?', category: 'improve' },
    { icon: <QuestionIcon />, text: 'I have a doubt about a concept', category: 'doubt' },
  ];

  if (role === ROLES.STUDENT) {
    return [
      ...baseActions,
      { icon: <BookIcon />, text: 'Give me a practice question', category: 'practice' },
      { icon: <TipIcon />, text: 'Tips for better answers', category: 'tips' },
    ];
  }

  if (role === ROLES.TEACHER || role === ROLES.ADMIN) {
    return [
      { icon: <GradeIcon />, text: 'Help me evaluate this answer', category: 'evaluate' },
      { icon: <BookIcon />, text: 'Create a rubric for grading', category: 'rubric' },
      { icon: <QuestionIcon />, text: 'Generate practice questions', category: 'generate' },
      { icon: <TipIcon />, text: 'Common mistakes to look for', category: 'mistakes' },
    ];
  }

  return baseActions;
};

// Sample AI responses (in production, this would connect to an AI API)
const getAIResponse = (message, role, context) => {
  const lowerMessage = message.toLowerCase();
  
  // Personalized greeting based on role
  if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
    if (role === ROLES.STUDENT) {
      return {
        text: "Hello! 👋 I'm your AI learning assistant. I can help you understand your evaluation scores, explain concepts, suggest improvements, and even give you practice questions. What would you like to know?",
        suggestions: ['Explain my score', 'Help me improve', 'Practice questions'],
      };
    }
    return {
      text: "Hello! 👋 I'm your AI teaching assistant. I can help you evaluate answers, create rubrics, identify common mistakes, and generate practice materials. How can I assist you today?",
      suggestions: ['Evaluate an answer', 'Create rubric', 'Common mistakes'],
    };
  }

  // Score explanation
  if (lowerMessage.includes('score') || lowerMessage.includes('marks') || lowerMessage.includes('grade')) {
    return {
      text: `📊 **Understanding Your Score**

Based on your recent evaluation, here's a detailed breakdown:

**Score: 7/10**

✅ **What you did well (5 marks):**
• Correctly defined the main concept
• Good use of technical terminology
• Clear introduction and structure

❌ **Areas for improvement (3 marks deducted):**
• Missing a practical example (-1 mark)
• Diagram/illustration would strengthen the answer (-1 mark)
• Conclusion could be more comprehensive (-1 mark)

💡 **Key insight:** Your conceptual understanding is solid. Adding examples and visual aids will significantly boost your score.`,
      suggestions: ['How to add better examples?', 'What diagram should I include?', 'Show me a sample answer'],
    };
  }

  // Improvement suggestions
  if (lowerMessage.includes('improve') || lowerMessage.includes('better') || lowerMessage.includes('suggestion')) {
    return {
      text: `🚀 **Actionable Improvement Tips**

Here's how to enhance your answers:

**1. Structure (PEEL Method)**
• **P**oint - State your main argument
• **E**vidence - Provide supporting facts
• **E**xplanation - Analyze the evidence  
• **L**ink - Connect back to the question

**2. Include Examples**
• Real-world applications
• Case studies when relevant
• Numerical examples if applicable

**3. Visual Elements**
• Diagrams for processes
• Tables for comparisons
• Flowcharts for sequences

**4. Keywords to Include**
Make sure to use subject-specific terminology that markers look for.

Would you like me to show you an improved version of your answer?`,
      suggestions: ['Show improved answer', 'More examples', 'Practice similar question'],
    };
  }

  // Doubt solving
  if (lowerMessage.includes('doubt') || lowerMessage.includes('explain') || lowerMessage.includes('what is') || lowerMessage.includes('define')) {
    return {
      text: `📚 **Concept Explanation**

I'd be happy to explain! Please tell me:

1. **Which subject** is this related to?
2. **What specific concept** are you confused about?
3. **What part** don't you understand?

For example, you could ask:
• "Explain normalization in databases"
• "What is the difference between TCP and UDP?"
• "How does photosynthesis work?"

The more specific your question, the better I can help! 🎯`,
      suggestions: ['Database concepts', 'Programming basics', 'General science'],
    };
  }

  // Practice questions
  if (lowerMessage.includes('practice') || lowerMessage.includes('question') || lowerMessage.includes('quiz')) {
    return {
      text: `📝 **Practice Question**

Here's a medium-difficulty question for you:

---
**Question:** Explain the concept of Object-Oriented Programming (OOP) and describe its four main principles with examples.

**Marks:** 10
**Time:** 15 minutes

**Rubric:**
• Definition of OOP (2 marks)
• Four principles explained (4 marks)
• Examples for each (3 marks)
• Clarity and structure (1 mark)

---

Would you like to:
1. Try answering this question?
2. See a model answer?
3. Get a different question?`,
      suggestions: ['Show model answer', 'Different question', 'Easier question'],
    };
  }

  // Tips
  if (lowerMessage.includes('tip') || lowerMessage.includes('advice') || lowerMessage.includes('strategy')) {
    return {
      text: `💡 **Top Tips for Better Answers**

**Before Writing:**
• Read the question twice
• Identify keywords (Explain, Compare, Analyze)
• Plan your structure (2 mins)

**While Writing:**
• Start with a clear definition
• Use topic sentences for each paragraph
• Include relevant examples
• Draw diagrams where applicable

**After Writing:**
• Review for completeness
• Check spelling and grammar
• Ensure you answered all parts

**Power Words to Use:**
✨ Furthermore, Additionally, Moreover
✨ In contrast, However, Nevertheless  
✨ Consequently, Therefore, Thus
✨ For instance, Such as, Including

Remember: Quality > Quantity! 🎯`,
      suggestions: ['More writing tips', 'Common mistakes', 'Practice now'],
    };
  }

  // Default response
  return {
    text: `I understand you're asking about: "${message}"

I can help you with:

📊 **Score Explanations** - Understand why you got specific marks
📈 **Improvement Tips** - Learn how to write better answers
❓ **Doubt Solving** - Get concepts explained simply
📝 **Practice Questions** - Test your knowledge
💡 **Study Tips** - Learn effective strategies

What would you like to explore? Just type your question or select a quick action below!`,
    suggestions: ['Explain my score', 'How to improve', 'Practice question'],
  };
};

// Message component
const ChatMessage = ({ message, isBot, isTyping }) => {
  const theme = useTheme();
  
  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      sx={{
        display: 'flex',
        justifyContent: isBot ? 'flex-start' : 'flex-end',
        mb: 2,
        px: { xs: 1, md: 2 },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isBot ? 'row' : 'row-reverse',
          alignItems: 'flex-start',
          gap: 1.5,
          maxWidth: { xs: '95%', sm: '85%', md: '75%' },
        }}
      >
        <Avatar
          sx={{
            width: { xs: 32, md: 40 },
            height: { xs: 32, md: 40 },
            bgcolor: isBot ? 'primary.main' : 'secondary.main',
            boxShadow: 2,
          }}
        >
          {isBot ? <BotIcon sx={{ fontSize: { xs: 18, md: 22 } }} /> : <PersonIcon sx={{ fontSize: { xs: 18, md: 22 } }} />}
        </Avatar>
        <Paper
          elevation={0}
          sx={{
            p: { xs: 1.5, md: 2 },
            borderRadius: 3,
            bgcolor: isBot 
              ? alpha(theme.palette.primary.main, 0.08)
              : alpha(theme.palette.secondary.main, 0.08),
            border: '1px solid',
            borderColor: isBot 
              ? alpha(theme.palette.primary.main, 0.2)
              : alpha(theme.palette.secondary.main, 0.2),
          }}
        >
          {isTyping ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Thinking...
              </Typography>
            </Box>
          ) : (
            <Typography
              variant="body2"
              sx={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.7,
                fontSize: { xs: '0.85rem', md: '0.9rem' },
                '& strong': { fontWeight: 600 },
              }}
              dangerouslySetInnerHTML={{
                __html: message.text
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br/>')
              }}
            />
          )}
        </Paper>
      </Box>
    </MotionBox>
  );
};

function ChatBot() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const quickActions = getQuickActions(user?.role);

  // Initial greeting
  useEffect(() => {
    const greeting = user?.role === ROLES.STUDENT
      ? `Welcome back, ${user?.name || 'Student'}! 👋\n\nI'm your AI learning assistant. I can help you:\n\n• 📊 Understand your evaluation scores\n• 💡 Get improvement suggestions\n• ❓ Solve your doubts\n• 📝 Practice with questions\n\nHow can I help you today?`
      : `Hello, ${user?.name || 'Educator'}! 👋\n\nI'm your AI teaching assistant. I can help you:\n\n• 📊 Evaluate student answers\n• 📋 Create grading rubrics\n• ⚠️ Identify common mistakes\n• 📝 Generate practice materials\n\nHow can I assist you today?`;

    setMessages([{
      id: 1,
      text: greeting,
      isBot: true,
      timestamp: new Date(),
    }]);
  }, [user]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (text = inputValue) => {
    if (!text.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: text,
      isBot: false,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response delay
    setTimeout(() => {
      const response = getAIResponse(text, user?.role, {});
      const botMessage = {
        id: Date.now() + 1,
        text: response.text,
        isBot: true,
        timestamp: new Date(),
        suggestions: response.suggestions,
      };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickAction = (action) => {
    handleSendMessage(action.text);
  };

  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion);
  };

  return (
    <Box
      sx={{
        height: 'calc(100vh - 100px)',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, md: 3 },
          borderRadius: 0,
          borderBottom: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              width: { xs: 45, md: 56 },
              height: { xs: 45, md: 56 },
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
            }}
          >
            <AIIcon sx={{ fontSize: { xs: 24, md: 30 } }} />
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography 
              variant="h5" 
              fontWeight={700}
              sx={{ fontSize: { xs: '1.1rem', md: '1.4rem' } }}
            >
              AI Learning Assistant
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'success.main',
                  animation: 'pulse 2s infinite',
                  '@keyframes pulse': {
                    '0%': { opacity: 1 },
                    '50%': { opacity: 0.5 },
                    '100%': { opacity: 1 },
                  },
                }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.85rem' } }}>
                Online • Ready to help
              </Typography>
            </Box>
          </Box>
          <Tooltip title="Clear chat">
            <IconButton
              onClick={() => setMessages([messages[0]])}
              sx={{
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.2) },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Quick Actions */}
      {messages.length <= 1 && (
        <Box sx={{ p: { xs: 2, md: 3 }, bgcolor: 'background.paper' }}>
          <Typography 
            variant="subtitle2" 
            color="text.secondary" 
            gutterBottom
            sx={{ fontSize: { xs: '0.75rem', md: '0.85rem' } }}
          >
            Quick Actions
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1,
            }}
          >
            {quickActions.map((action, index) => (
              <Chip
                key={index}
                icon={action.icon}
                label={action.text}
                onClick={() => handleQuickAction(action)}
                sx={{
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                  border: '1px solid',
                  borderColor: alpha(theme.palette.primary.main, 0.2),
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.15),
                  },
                  fontSize: { xs: '0.75rem', md: '0.85rem' },
                  height: { xs: 32, md: 36 },
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          py: 2,
          bgcolor: alpha(theme.palette.primary.main, 0.02),
        }}
      >
        <AnimatePresence>
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isBot={message.isBot}
            />
          ))}
          {isTyping && (
            <ChatMessage
              message={{ text: '' }}
              isBot={true}
              isTyping={true}
            />
          )}
        </AnimatePresence>
        
        {/* Suggestions */}
        {messages.length > 0 && messages[messages.length - 1]?.suggestions && !isTyping && (
          <Box sx={{ px: { xs: 2, md: 3 }, mt: 1 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {messages[messages.length - 1].suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  size="small"
                  variant="outlined"
                  onClick={() => handleSuggestionClick(suggestion)}
                  sx={{
                    borderRadius: 5,
                    textTransform: 'none',
                    fontSize: { xs: '0.75rem', md: '0.8rem' },
                    borderColor: alpha(theme.palette.primary.main, 0.3),
                    color: 'primary.main',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                >
                  {suggestion}
                </Button>
              ))}
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2, md: 3 },
          borderRadius: 0,
          borderTop: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            gap: 1.5,
            alignItems: 'flex-end',
          }}
        >
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me anything about your evaluation, concepts, or learning..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isTyping}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: alpha(theme.palette.primary.main, 0.03),
                fontSize: { xs: '0.9rem', md: '1rem' },
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                },
                '&.Mui-focused': {
                  bgcolor: 'white',
                },
              },
            }}
          />
          <IconButton
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isTyping}
            sx={{
              width: { xs: 48, md: 56 },
              height: { xs: 48, md: 56 },
              background: inputValue.trim()
                ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
                : alpha(theme.palette.grey[400], 0.3),
              color: 'white',
              boxShadow: inputValue.trim() ? '0 4px 14px rgba(99, 102, 241, 0.4)' : 'none',
              '&:hover': {
                background: inputValue.trim()
                  ? 'linear-gradient(135deg, #5558e3 0%, #7c4fe0 100%)'
                  : alpha(theme.palette.grey[400], 0.3),
              },
              '&.Mui-disabled': {
                color: 'white',
              },
            }}
          >
            {isTyping ? (
              <CircularProgress size={24} sx={{ color: 'white' }} />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </Box>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ 
            display: 'block', 
            textAlign: 'center', 
            mt: 1.5,
            fontSize: { xs: '0.65rem', md: '0.7rem' },
          }}
        >
          AI responses are for learning assistance only. Always verify with your instructor.
        </Typography>
      </Paper>
    </Box>
  );
}

export default ChatBot;
