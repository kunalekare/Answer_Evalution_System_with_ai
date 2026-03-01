/**
 * Landing Page Chatbot - PaperEval Assistant
 * ============================================
 * Floating chatbot that answers questions about PaperEval
 * Uses keyword matching for instant, accurate responses
 * Logo button in bottom-right corner
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  Avatar,
  Fade,
  Grow,
  Chip,
  alpha,
  useTheme,
  useMediaQuery,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  Close as CloseIcon,
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  AutoAwesome as SparkleIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const MotionBox = motion(Box);

// =========================================
// Knowledge Base - All PaperEval info
// =========================================
const KNOWLEDGE_BASE = [
  {
    keywords: ['what is papereval', 'what is this', 'about', 'tell me about', 'what does papereval do', 'explain papereval', 'what is paper eval'],
    answer: `**PaperEval** is an AI-powered Answer Evaluation System designed for colleges and universities. It automatically grades student answer sheets using OCR (Optical Character Recognition), NLP (Natural Language Processing), and Machine Learning — making the evaluation process **Smart, Fast & Accurate**.`
  },
  {
    keywords: ['feature', 'what can it do', 'capabilities', 'functionality', 'what all', 'functions'],
    answer: `PaperEval offers these key features:\n\n• **Smart OCR** — Extracts handwritten text from answer sheets using Ensemble OCR (PaddleOCR + EasyOCR + Tesseract)\n• **Semantic Analysis** — AI compares student answers with model answers using NLP\n• **Detailed Scoring** — Breakdown of marks with keyword matching, accuracy & relevance\n• **Manual Checking** — Teachers can annotate, mark & review papers on canvas\n• **AI ChatBot** — Ask questions and get AI-powered assistance\n• **Community Forum** — Students and teachers can discuss and collaborate\n• **Marksheet Generation** — Auto-generate marksheets and send via email\n• **Dashboard & Analytics** — Visual stats, charts and performance tracking`
  },
  {
    keywords: ['how does it work', 'process', 'workflow', 'steps', 'how to use', 'how it works', 'explain process'],
    answer: `Here's how PaperEval works:\n\n1️⃣ **Sign Up** — Create account as Student, Teacher or Admin\n2️⃣ **Upload** — Teachers upload answer sheets (PDF/images)\n3️⃣ **OCR Extraction** — AI extracts text from handwritten answers\n4️⃣ **AI Evaluation** — NLP compares answers with model answers\n5️⃣ **Scoring** — Automatic marks with detailed breakdown\n6️⃣ **Review** — Teachers can manually verify & adjust marks\n7️⃣ **Results** — View detailed results, marksheets & analytics`
  },
  {
    keywords: ['ocr', 'handwriting', 'text extraction', 'scan', 'recognize', 'read handwriting', 'extract text'],
    answer: `PaperEval uses an **Ensemble OCR** system with 3 engines running in parallel:\n\n• **PaddleOCR** — Best for structured text\n• **EasyOCR** — Great for diverse handwriting\n• **Tesseract** — Reliable for printed text\n\nThe engines vote on results using confidence-weighted fusion, achieving **85-90%+ accuracy** on handwritten answers. Each engine uses optimized preprocessing for best results.`
  },
  {
    keywords: ['role', 'user type', 'who can use', 'student', 'teacher', 'admin', 'account type'],
    answer: `PaperEval supports 3 user roles:\n\n👨‍🎓 **Student** — View results, check marksheets, use AI chatbot, join community discussions\n👨‍🏫 **Teacher** — Upload papers, evaluate answers, manual checking, manage students, generate marksheets\n👨‍💼 **Admin** — Full access including user management, system settings, and all teacher features`
  },
  {
    keywords: ['pricing', 'cost', 'free', 'paid', 'subscription', 'price', 'charge', 'plan'],
    answer: `PaperEval is currently available as a **free web application**. You can sign up and start using all features at no cost. Visit **papereval.kunalekare.online** to get started!`
  },
  {
    keywords: ['sign up', 'register', 'create account', 'join', 'login', 'log in', 'sign in', 'get started'],
    answer: `To get started:\n\n1. Click **"Get Started"** or **"Sign In"** on the top right\n2. Choose **Sign Up** tab\n3. Select your role: Student, Teacher, or Admin\n4. Fill in your details (name, email, password)\n5. You're in! Access your personalized dashboard\n\nExisting users can simply Sign In with their credentials.`
  },
  {
    keywords: ['manual check', 'manual marking', 'annotate', 'canvas', 'mark paper', 'review paper', 'manual evaluation'],
    answer: `The **Manual Checking** feature lets teachers:\n\n• View answer sheets on an interactive canvas\n• Add number annotations (marks) directly on papers\n• Auto-fill scores in the evaluation panel\n• Navigate between questions easily\n• Generate marksheets after completing review\n• Send marksheets via email to students\n\nIt's perfect for verifying AI evaluations or grading diagrams/drawings.`
  },
  {
    keywords: ['result', 'score', 'mark', 'grade', 'report', 'marksheet', 'performance'],
    answer: `PaperEval provides detailed results including:\n\n📊 **Score Breakdown** — Marks per question with keyword matching & semantic scores\n📋 **Marksheet** — Professional marksheet with student info, question-wise marks\n📧 **Email** — Send marksheets directly to student's email via Gmail\n📈 **Analytics** — Performance charts, trends, and history tracking\n\nTeachers can view all results in the History section.`
  },
  {
    keywords: ['community', 'forum', 'discuss', 'collaborate', 'post', 'social'],
    answer: `The **Community** section is a discussion forum where:\n\n• Students can ask doubts and get help\n• Teachers can share resources and tips\n• Anyone can post questions, answers, and discussions\n• Like and interact with posts\n\nIt fosters collaboration between students and educators!`
  },
  {
    keywords: ['chatbot', 'ai assistant', 'ai chat', 'ask ai', 'bot'],
    answer: `PaperEval has a built-in **AI ChatBot** (available after login) that can:\n\n• Answer academic questions\n• Help with study-related queries\n• Provide instant AI-powered responses\n\nYou're currently chatting with the **Landing Page Assistant** — I answer questions about PaperEval. For AI academic help, sign in and use the ChatBot from the sidebar!`
  },
  {
    keywords: ['technology', 'tech stack', 'built with', 'framework', 'stack', 'made with'],
    answer: `PaperEval is built with modern technologies:\n\n**Frontend:** React 18, Material-UI, Framer Motion\n**Backend:** Python FastAPI\n**AI/ML:** NLP, Sentence Transformers, Ensemble OCR\n**OCR:** PaddleOCR, EasyOCR, Tesseract\n**Auth:** JWT-based authentication\n**Deployment:** Azure / Render\n\nDesigned & developed by **Kunal Ekare**.`
  },
  {
    keywords: ['contact', 'support', 'help', 'email', 'reach', 'developer', 'who made', 'creator', 'kunal'],
    answer: `PaperEval is created by **Kunal Ekare**.\n\nFor support or queries, you can reach out through the platform or visit the website at **papereval.kunalekare.online**`
  },
  {
    keywords: ['mobile', 'app', 'phone', 'pwa', 'install', 'download', 'android', 'ios'],
    answer: `PaperEval is a **Progressive Web App (PWA)** — you can install it on your phone!\n\n📱 **Android:** Open in Chrome → Tap "Add to Home Screen"\n🍎 **iOS:** Open in Safari → Share → "Add to Home Screen"\n\nIt works like a native app with no browser bar, offline support, and smooth performance. No app store download needed!`
  },
  {
    keywords: ['secure', 'security', 'safe', 'privacy', 'data', 'protect'],
    answer: `PaperEval takes security seriously:\n\n🔒 **JWT Authentication** — Secure token-based login\n🛡️ **Role-based Access** — Students, Teachers & Admins have different permissions\n🔐 **Password Encryption** — All passwords are securely hashed\n📁 **Data Privacy** — Answer sheets are processed securely\n\nYour data is safe with PaperEval!`
  },
  {
    keywords: ['upload', 'file', 'format', 'pdf', 'image', 'submit', 'answer sheet'],
    answer: `Teachers can upload answer sheets in these formats:\n\n📄 **PDF** — Multi-page answer booklets\n🖼️ **Images** — JPG, PNG scanned answer sheets\n\nSimply go to **Evaluate** section, upload the answer sheet along with model answers, and let AI do the rest! You can also use **Manual Checking** for hands-on review.`
  },
  {
    keywords: ['accuracy', 'reliable', 'correct', 'quality', 'good', 'how accurate'],
    answer: `PaperEval delivers high accuracy through:\n\n• **Ensemble OCR** — 3 engines for 85-90%+ text extraction accuracy\n• **Semantic Analysis** — NLP understands meaning, not just exact word matching\n• **Confidence Scoring** — Each answer gets a confidence percentage\n• **Manual Review** — Teachers can always verify and adjust AI marks\n\nThe combination of AI + human review ensures reliable evaluation!`
  },
  {
    keywords: ['hello', 'hi', 'hey', 'good morning', 'good evening', 'greetings', 'howdy'],
    answer: `Hello! 👋 Welcome to **PaperEval** — Smart, Fast & Accurate Answer Evaluation!\n\nI can help you with:\n• What PaperEval does\n• Features & capabilities\n• How to get started\n• Technical details\n\nJust ask me anything!`
  },
  {
    keywords: ['bye', 'goodbye', 'thanks', 'thank you', 'thank', 'okay', 'ok', 'great', 'nice'],
    answer: `You're welcome! 😊 If you have more questions, feel free to ask anytime.\n\nReady to try PaperEval? Click **"Get Started"** to create your account! 🚀`
  },
];

// Quick suggestion chips
const QUICK_SUGGESTIONS = [
  'What is PaperEval?',
  'How does it work?',
  'Features',
  'How to get started?',
  'Is it free?',
  'Mobile app?',
];

// =========================================
// Find best matching answer
// =========================================
function findAnswer(query) {
  const q = query.toLowerCase().trim();
  
  let bestMatch = null;
  let bestScore = 0;

  for (const entry of KNOWLEDGE_BASE) {
    for (const keyword of entry.keywords) {
      // Exact keyword match
      if (q.includes(keyword) || keyword.includes(q)) {
        const score = keyword.length;
        if (score > bestScore) {
          bestScore = score;
          bestMatch = entry.answer;
        }
      }
      // Word overlap matching
      const queryWords = q.split(/\s+/);
      const kwWords = keyword.split(/\s+/);
      const overlap = queryWords.filter(w => kwWords.some(kw => kw.includes(w) || w.includes(kw))).length;
      const overlapScore = overlap / Math.max(queryWords.length, 1) * keyword.length;
      if (overlapScore > bestScore && overlap >= 1) {
        bestScore = overlapScore;
        bestMatch = entry.answer;
      }
    }
  }

  if (bestMatch) return bestMatch;

  return `I'm not sure about that, but I can help you with:\n\n• **What PaperEval is** and how it works\n• **Features** like OCR, AI evaluation, manual checking\n• **Getting started** — sign up, roles, pricing\n• **Technical details** — accuracy, security, tech stack\n\nTry asking one of these topics! 😊`;
}

// =========================================
// Format message text with markdown-like styling
// =========================================
function FormatMessage({ text }) {
  const lines = text.split('\n');
  
  return (
    <Box>
      {lines.map((line, i) => {
        // Bold text
        let formatted = line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        
        // Bullet points
        if (formatted.startsWith('•') || formatted.startsWith('-')) {
          return (
            <Typography
              key={i}
              variant="body2"
              sx={{ pl: 1, py: 0.15, fontSize: '0.84rem', lineHeight: 1.5 }}
              dangerouslySetInnerHTML={{ __html: formatted }}
            />
          );
        }
        
        // Numbered items
        if (/^\d[️⃣]?\s/.test(formatted) || /^\d\.\s/.test(formatted)) {
          return (
            <Typography
              key={i}
              variant="body2"
              sx={{ pl: 1, py: 0.15, fontSize: '0.84rem', lineHeight: 1.5 }}
              dangerouslySetInnerHTML={{ __html: formatted }}
            />
          );
        }

        // Empty line = spacing
        if (formatted.trim() === '') {
          return <Box key={i} sx={{ height: 6 }} />;
        }
        
        return (
          <Typography
            key={i}
            variant="body2"
            sx={{ py: 0.1, fontSize: '0.84rem', lineHeight: 1.5 }}
            dangerouslySetInnerHTML={{ __html: formatted }}
          />
        );
      })}
    </Box>
  );
}

// =========================================
// Main Chatbot Component
// =========================================
export default function LandingChatbot() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: `Hey there! 👋 I'm the **PaperEval Assistant**.\n\nAsk me anything about our AI-powered answer evaluation platform!\n\nOr tap a quick question below to get started.`,
      time: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Pulse animation for unread
  useEffect(() => {
    if (!open) {
      const timer = setTimeout(() => setHasNewMessage(true), 3000);
      return () => clearTimeout(timer);
    } else {
      setHasNewMessage(false);
    }
  }, [open]);

  const handleSend = (text) => {
    const query = text || input.trim();
    if (!query) return;

    // Add user message
    const userMsg = {
      id: Date.now(),
      type: 'user',
      text: query,
      time: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulate bot thinking
    setTimeout(() => {
      const answer = findAnswer(query);
      const botMsg = {
        id: Date.now() + 1,
        type: 'bot',
        text: answer,
        time: new Date(),
      };
      setMessages(prev => [...prev, botMsg]);
      setIsTyping(false);
    }, 600 + Math.random() * 800);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* ===== Chat Window ===== */}
      <AnimatePresence>
        {open && (
          <MotionBox
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.9 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            sx={{
              position: 'fixed',
              bottom: isMobile ? 0 : 100,
              right: isMobile ? 0 : 24,
              width: isMobile ? '100vw' : 380,
              height: isMobile ? '100dvh' : 520,
              zIndex: 9999,
              borderRadius: isMobile ? 0 : 3,
              overflow: 'hidden',
              boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
              display: 'flex',
              flexDirection: 'column',
              bgcolor: '#0f1117',
              border: isMobile ? 'none' : '1px solid rgba(139,92,246,0.3)',
            }}
          >
            {/* Header */}
            <Box
              sx={{
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                px: 2,
                py: 1.5,
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                flexShrink: 0,
              }}
            >
              <Avatar
                src="/logo.png"
                sx={{
                  width: 38,
                  height: 38,
                  bgcolor: 'rgba(255,255,255,0.15)',
                  border: '2px solid rgba(255,255,255,0.3)',
                }}
              >
                <BotIcon sx={{ fontSize: 22 }} />
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography sx={{ color: '#fff', fontWeight: 700, fontSize: '0.95rem', lineHeight: 1.2 }}>
                  PaperEval Assistant
                </Typography>
                <Typography sx={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.72rem' }}>
                  <Box component="span" sx={{
                    display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
                    bgcolor: '#4ade80', mr: 0.5, verticalAlign: 'middle', mb: '1px',
                    boxShadow: '0 0 6px #4ade80',
                  }} />
                  Always online • Ask me anything
                </Typography>
              </Box>
              <IconButton onClick={() => setOpen(false)} sx={{ color: '#fff', '&:hover': { bgcolor: 'rgba(255,255,255,0.15)' } }}>
                <CloseIcon />
              </IconButton>
            </Box>

            {/* Messages */}
            <Box
              sx={{
                flex: 1,
                overflowY: 'auto',
                px: 2,
                py: 1.5,
                display: 'flex',
                flexDirection: 'column',
                gap: 1.5,
                '&::-webkit-scrollbar': { width: 4 },
                '&::-webkit-scrollbar-thumb': { bgcolor: 'rgba(139,92,246,0.3)', borderRadius: 2 },
              }}
            >
              {messages.map((msg) => (
                <Grow key={msg.id} in timeout={400}>
                  <Box
                    sx={{
                      display: 'flex',
                      gap: 1,
                      alignItems: 'flex-start',
                      flexDirection: msg.type === 'user' ? 'row-reverse' : 'row',
                    }}
                  >
                    {msg.type === 'bot' && (
                      <Avatar
                        src="/logo.png"
                        sx={{
                          width: 30, height: 30, mt: 0.3,
                          bgcolor: alpha('#8b5cf6', 0.2),
                          border: '1.5px solid rgba(139,92,246,0.4)',
                        }}
                      >
                        <BotIcon sx={{ fontSize: 16, color: '#a78bfa' }} />
                      </Avatar>
                    )}
                    <Paper
                      elevation={0}
                      sx={{
                        px: 1.8,
                        py: 1.2,
                        maxWidth: '82%',
                        borderRadius: msg.type === 'user'
                          ? '16px 16px 4px 16px'
                          : '16px 16px 16px 4px',
                        bgcolor: msg.type === 'user'
                          ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                          : alpha('#fff', 0.06),
                        background: msg.type === 'user'
                          ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                          : undefined,
                        color: '#fff',
                        border: msg.type === 'bot' ? '1px solid rgba(255,255,255,0.06)' : 'none',
                      }}
                    >
                      {msg.type === 'bot' ? (
                        <FormatMessage text={msg.text} />
                      ) : (
                        <Typography variant="body2" sx={{ fontSize: '0.84rem', lineHeight: 1.5 }}>
                          {msg.text}
                        </Typography>
                      )}
                      <Typography
                        sx={{
                          fontSize: '0.62rem',
                          color: 'rgba(255,255,255,0.35)',
                          mt: 0.5,
                          textAlign: msg.type === 'user' ? 'right' : 'left',
                        }}
                      >
                        {msg.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Paper>
                  </Box>
                </Grow>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <Fade in>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Avatar
                      src="/logo.png"
                      sx={{
                        width: 30, height: 30,
                        bgcolor: alpha('#8b5cf6', 0.2),
                        border: '1.5px solid rgba(139,92,246,0.4)',
                      }}
                    >
                      <BotIcon sx={{ fontSize: 16, color: '#a78bfa' }} />
                    </Avatar>
                    <Paper
                      elevation={0}
                      sx={{
                        px: 2, py: 1.2, borderRadius: '16px 16px 16px 4px',
                        bgcolor: alpha('#fff', 0.06),
                        border: '1px solid rgba(255,255,255,0.06)',
                        display: 'flex', gap: 0.6, alignItems: 'center',
                      }}
                    >
                      {[0, 1, 2].map(i => (
                        <Box
                          key={i}
                          sx={{
                            width: 7, height: 7, borderRadius: '50%', bgcolor: '#8b5cf6',
                            animation: 'typingDot 1.2s infinite',
                            animationDelay: `${i * 0.2}s`,
                            '@keyframes typingDot': {
                              '0%, 60%, 100%': { opacity: 0.3, transform: 'scale(0.8)' },
                              '30%': { opacity: 1, transform: 'scale(1.1)' },
                            },
                          }}
                        />
                      ))}
                    </Paper>
                  </Box>
                </Fade>
              )}

              {/* Quick suggestions on first message */}
              {messages.length === 1 && !isTyping && (
                <Fade in timeout={800}>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.8, mt: 0.5 }}>
                    {QUICK_SUGGESTIONS.map((suggestion) => (
                      <Chip
                        key={suggestion}
                        label={suggestion}
                        size="small"
                        onClick={() => handleSend(suggestion)}
                        sx={{
                          bgcolor: alpha('#8b5cf6', 0.15),
                          color: '#c4b5fd',
                          border: '1px solid rgba(139,92,246,0.25)',
                          fontSize: '0.73rem',
                          fontWeight: 500,
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          '&:hover': {
                            bgcolor: alpha('#8b5cf6', 0.3),
                            color: '#fff',
                            transform: 'translateY(-1px)',
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Fade>
              )}

              <div ref={messagesEndRef} />
            </Box>

            {/* Input Area */}
            <Box
              sx={{
                px: 1.5, py: 1.2, flexShrink: 0,
                borderTop: '1px solid rgba(255,255,255,0.06)',
                bgcolor: alpha('#000', 0.3),
              }}
            >
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                <TextField
                  ref={inputRef}
                  fullWidth
                  multiline
                  maxRows={3}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about PaperEval..."
                  variant="outlined"
                  size="small"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 3,
                      bgcolor: alpha('#fff', 0.05),
                      color: '#fff',
                      fontSize: '0.85rem',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.08)' },
                      '&:hover fieldset': { borderColor: 'rgba(139,92,246,0.4)' },
                      '&.Mui-focused fieldset': { borderColor: '#8b5cf6' },
                    },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.3)' },
                  }}
                />
                <IconButton
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  sx={{
                    bgcolor: input.trim() ? '#8b5cf6' : 'rgba(139,92,246,0.2)',
                    color: '#fff',
                    width: 40, height: 40, mb: 0.1,
                    transition: 'all 0.2s',
                    '&:hover': { bgcolor: '#7c3aed', transform: 'scale(1.05)' },
                    '&.Mui-disabled': { color: 'rgba(255,255,255,0.2)' },
                  }}
                >
                  <SendIcon sx={{ fontSize: 18 }} />
                </IconButton>
              </Box>
              <Typography sx={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.2)', textAlign: 'center', mt: 0.8 }}>
                PaperEval Assistant • Smart-Fast-Accurate
              </Typography>
            </Box>
          </MotionBox>
        )}
      </AnimatePresence>

      {/* ===== Floating Logo Button ===== */}
      <Tooltip title="Chat with PaperEval Assistant" placement="left" arrow>
        <MotionBox
          onClick={() => setOpen(!open)}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 62,
            height: 62,
            borderRadius: '50%',
            cursor: 'pointer',
            zIndex: 9998,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
            boxShadow: '0 6px 30px rgba(99,102,241,0.5), 0 0 20px rgba(139,92,246,0.3)',
            border: '2px solid rgba(255,255,255,0.15)',
            overflow: 'hidden',
            transition: 'box-shadow 0.3s',
            '&:hover': {
              boxShadow: '0 8px 40px rgba(99,102,241,0.6), 0 0 30px rgba(139,92,246,0.4)',
            },
            // Pulse animation when has new message
            ...(hasNewMessage && !open && {
              animation: 'chatPulse 2s infinite',
              '@keyframes chatPulse': {
                '0%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5)' },
                '50%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5), 0 0 0 12px rgba(139,92,246,0.15)' },
                '100%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5)' },
              },
            }),
          }}
        >
      {/* ===== Floating Robot Button ===== */}
      <Tooltip title="Chat with PaperEval Assistant" placement="left" arrow>
        <MotionBox
          onClick={() => setOpen(!open)}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 68,
            height: 68,
            borderRadius: '50%',
            cursor: 'pointer',
            zIndex: 9998,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
            boxShadow: '0 6px 30px rgba(99,102,241,0.5), 0 0 20px rgba(139,92,246,0.3)',
            border: '2px solid rgba(255,255,255,0.2)',
            overflow: 'visible',
            transition: 'box-shadow 0.3s',
            '&:hover': {
              boxShadow: '0 8px 40px rgba(99,102,241,0.6), 0 0 30px rgba(139,92,246,0.4)',
            },
            ...(hasNewMessage && !open && {
              animation: 'chatPulse 2s infinite',
              '@keyframes chatPulse': {
                '0%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5)' },
                '50%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5), 0 0 0 12px rgba(139,92,246,0.15)' },
                '100%': { boxShadow: '0 6px 30px rgba(99,102,241,0.5)' },
              },
            }),
          }}
        >
          {open ? (
            <CloseIcon sx={{ fontSize: 28, color: '#fff' }} />
          ) : (
            /* 3D Robot Character SVG */
            <Box
              sx={{
                width: 48, height: 48,
                animation: 'robotFloat 3s ease-in-out infinite',
                '@keyframes robotFloat': {
                  '0%, 100%': { transform: 'translateY(0)' },
                  '50%': { transform: 'translateY(-4px)' },
                },
              }}
            >
              <svg viewBox="0 0 100 100" width="48" height="48" xmlns="http://www.w3.org/2000/svg">
                {/* Antenna */}
                <line x1="50" y1="8" x2="50" y2="18" stroke="#e0e7ff" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="50" cy="6" r="4" fill="#4ade80">
                  <animate attributeName="r" values="3.5;5;3.5" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle cx="50" cy="6" r="6" fill="none" stroke="#4ade80" strokeWidth="1" opacity="0.3">
                  <animate attributeName="r" values="5;9;5" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.4;0;0.4" dur="2s" repeatCount="indefinite" />
                </circle>

                {/* Head - 3D effect with gradient */}
                <defs>
                  <linearGradient id="headGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#e0e7ff" />
                    <stop offset="50%" stopColor="#c7d2fe" />
                    <stop offset="100%" stopColor="#a5b4fc" />
                  </linearGradient>
                  <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#ddd6fe" />
                    <stop offset="50%" stopColor="#c4b5fd" />
                    <stop offset="100%" stopColor="#a78bfa" />
                  </linearGradient>
                  <linearGradient id="visorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#1e1b4b" />
                    <stop offset="100%" stopColor="#312e81" />
                  </linearGradient>
                  <filter id="shadow3d" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="1" dy="2" stdDeviation="2" floodColor="#4c1d95" floodOpacity="0.35" />
                  </filter>
                </defs>

                {/* Ears */}
                <rect x="18" y="28" width="6" height="14" rx="3" fill="url(#bodyGrad)" filter="url(#shadow3d)" />
                <rect x="76" y="28" width="6" height="14" rx="3" fill="url(#bodyGrad)" filter="url(#shadow3d)" />

                {/* Head */}
                <rect x="26" y="18" width="48" height="38" rx="12" fill="url(#headGrad)" filter="url(#shadow3d)" />

                {/* Visor / Face plate */}
                <rect x="31" y="24" width="38" height="22" rx="8" fill="url(#visorGrad)" />
                <rect x="31" y="24" width="38" height="22" rx="8" fill="none" stroke="#6366f1" strokeWidth="0.8" opacity="0.5" />

                {/* Eyes - glowing */}
                <ellipse cx="41" cy="35" rx="5" ry="5.5" fill="#4ade80">
                  <animate attributeName="ry" values="5.5;1;5.5" dur="4s" repeatCount="indefinite" begin="0s" keyTimes="0;0.03;0.06;1" keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1" calcMode="spline" />
                </ellipse>
                <ellipse cx="59" cy="35" rx="5" ry="5.5" fill="#4ade80">
                  <animate attributeName="ry" values="5.5;1;5.5" dur="4s" repeatCount="indefinite" begin="0s" keyTimes="0;0.03;0.06;1" keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1" calcMode="spline" />
                </ellipse>
                {/* Eye glow */}
                <ellipse cx="41" cy="35" rx="3" ry="3" fill="#86efac" opacity="0.6" />
                <ellipse cx="59" cy="35" rx="3" ry="3" fill="#86efac" opacity="0.6" />
                {/* Eye shine */}
                <circle cx="39" cy="33" r="1.5" fill="#fff" opacity="0.8" />
                <circle cx="57" cy="33" r="1.5" fill="#fff" opacity="0.8" />

                {/* Mouth - smiling */}
                <path d="M43 41 Q50 46 57 41" stroke="#4ade80" strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.8" />

                {/* Neck */}
                <rect x="43" y="55" width="14" height="6" rx="2" fill="url(#bodyGrad)" />

                {/* Body */}
                <rect x="30" y="60" width="40" height="26" rx="8" fill="url(#bodyGrad)" filter="url(#shadow3d)" />

                {/* Chest detail - arc reactor style */}
                <circle cx="50" cy="72" r="7" fill="url(#visorGrad)" />
                <circle cx="50" cy="72" r="5" fill="none" stroke="#8b5cf6" strokeWidth="1.2">
                  <animate attributeName="r" values="3;5;3" dur="2.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite" />
                </circle>
                <circle cx="50" cy="72" r="2.5" fill="#8b5cf6">
                  <animate attributeName="opacity" values="0.6;1;0.6" dur="1.5s" repeatCount="indefinite" />
                </circle>

                {/* Arms */}
                <rect x="18" y="62" width="10" height="20" rx="5" fill="url(#bodyGrad)" filter="url(#shadow3d)">
                  <animateTransform attributeName="transform" type="rotate" values="-5,23,72;5,23,72;-5,23,72" dur="3s" repeatCount="indefinite" />
                </rect>
                <rect x="72" y="62" width="10" height="20" rx="5" fill="url(#bodyGrad)" filter="url(#shadow3d)">
                  <animateTransform attributeName="transform" type="rotate" values="5,77,72;-5,77,72;5,77,72" dur="3s" repeatCount="indefinite" />
                </rect>

                {/* Hand circles */}
                <circle cx="23" cy="83" r="4" fill="url(#headGrad)">
                  <animateTransform attributeName="transform" type="rotate" values="-5,23,72;5,23,72;-5,23,72" dur="3s" repeatCount="indefinite" />
                </circle>
                <circle cx="77" cy="83" r="4" fill="url(#headGrad)">
                  <animateTransform attributeName="transform" type="rotate" values="5,77,72;-5,77,72;5,77,72" dur="3s" repeatCount="indefinite" />
                </circle>

                {/* Legs */}
                <rect x="36" y="85" width="10" height="10" rx="4" fill="url(#bodyGrad)" filter="url(#shadow3d)" />
                <rect x="54" y="85" width="10" height="10" rx="4" fill="url(#bodyGrad)" filter="url(#shadow3d)" />

                {/* Feet */}
                <rect x="33" y="93" width="15" height="5" rx="2.5" fill="url(#headGrad)" />
                <rect x="52" y="93" width="15" height="5" rx="2.5" fill="url(#headGrad)" />
              </svg>
            </Box>
          )}

          {/* Notification badge */}
          {hasNewMessage && !open && (
            <Box
              sx={{
                position: 'absolute',
                top: 2,
                right: 2,
                width: 14,
                height: 14,
                borderRadius: '50%',
                bgcolor: '#ef4444',
                border: '2px solid #0f1117',
                animation: 'badgePulse 1.5s infinite',
                '@keyframes badgePulse': {
                  '0%, 100%': { transform: 'scale(1)' },
                  '50%': { transform: 'scale(1.2)' },
                },
              }}
            />
          )}
        </MotionBox>
      </Tooltip>
    </>
  );
}
