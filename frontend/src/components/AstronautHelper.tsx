import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Box, Typography } from '@mui/material'

const TIPS = [
  '🚀 Welcome to Amzur AI — sign in to begin',
  '🖼️ Upload images, videos & PDFs for AI analysis',
  '✨ Generate stunning images with a single prompt',
  '💬 Gemini & GPT-4o power your conversations',
  '🔒 Your chats are private & securely stored',
  '📄 Ask questions about your PDFs using RAG',
]

export function AstronautHelper() {
  const [tipIndex, setTipIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setTipIndex((i) => (i + 1) % TIPS.length), 4200)
    return () => clearInterval(id)
  }, [])

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        pointerEvents: 'none',
      }}
    >
      {/* Speech bubble */}
      <AnimatePresence mode="wait">
        <motion.div
          key={tipIndex}
          initial={{ opacity: 0, y: 10, scale: 0.88 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.92 }}
          transition={{ duration: 0.38, ease: 'easeOut' }}
          style={{ marginBottom: 10 }}
        >
          <Box
            sx={{
              background: 'linear-gradient(135deg, rgba(22, 38, 88, 0.96), rgba(14, 26, 60, 0.94))',
              border: '1px solid rgba(130, 180, 255, 0.42)',
              borderRadius: 3,
              px: 2,
              py: 1.25,
              maxWidth: 210,
              boxShadow: '0 8px 24px rgba(4, 8, 28, 0.55)',
              backdropFilter: 'blur(14px)',
              position: 'relative',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: -9,
                left: '50%',
                transform: 'translateX(-50%)',
                border: '5px solid transparent',
                borderTopColor: 'rgba(130, 180, 255, 0.42)',
              },
            }}
          >
            <Typography
              variant="caption"
              sx={{ color: '#c4dcff', lineHeight: 1.45, display: 'block', textAlign: 'center' }}
            >
              {TIPS[tipIndex]}
            </Typography>
          </Box>
        </motion.div>
      </AnimatePresence>

      {/* Floating astronaut */}
      <motion.div
        animate={{ y: [0, -9, 0] }}
        transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut' }}
      >
        <svg width="88" height="108" viewBox="0 0 100 125" xmlns="http://www.w3.org/2000/svg">
          {/* Helmet outer */}
          <circle cx="50" cy="33" r="27" fill="#c8ddf0" />
          {/* Visor */}
          <ellipse cx="50" cy="35" rx="19" ry="21" fill="#0d1b3e" />
          {/* Visor reflections */}
          <ellipse cx="43" cy="27" rx="6" ry="8" fill="white" opacity="0.18" />
          <ellipse cx="58" cy="30" rx="3" ry="4" fill="white" opacity="0.1" />
          {/* Helmet ring */}
          <circle cx="50" cy="33" r="27" fill="none" stroke="#9bb8d8" strokeWidth="2.5" />
          {/* Neck connector */}
          <rect x="43" y="58" width="14" height="7" rx="3" fill="#a8c0d8" />
          {/* Body */}
          <rect x="23" y="63" width="54" height="46" rx="19" fill="#ddeaf8" />
          {/* Body stripe */}
          <rect x="23" y="76" width="54" height="2" fill="#b8ccec" opacity="0.45" />
          {/* Chest panel */}
          <rect x="36" y="70" width="28" height="22" rx="6" fill="#5878a8" />
          {/* Panel lights */}
          <circle cx="44" cy="78" r="4" fill="#40d8c8" />
          <circle cx="56" cy="78" r="4" fill="#ff7878" />
          <rect x="43" y="86" width="14" height="3" rx="1.5" fill="#8090b8" />
          {/* Left arm */}
          <rect x="7" y="65" width="18" height="13" rx="6.5" fill="#ddeaf8" />
          <circle cx="8" cy="71" r="8" fill="#b8ccec" />
          {/* Right arm */}
          <rect x="75" y="65" width="18" height="13" rx="6.5" fill="#ddeaf8" />
          <circle cx="92" cy="71" r="8" fill="#b8ccec" />
          {/* Legs */}
          <rect x="31" y="105" width="16" height="16" rx="8" fill="#c0d0e8" />
          <rect x="53" y="105" width="16" height="16" rx="8" fill="#c0d0e8" />
          {/* Boots */}
          <ellipse cx="39" cy="120" rx="12" ry="5.5" fill="#8090b0" />
          <ellipse cx="61" cy="120" rx="12" ry="5.5" fill="#8090b0" />
          {/* Antenna */}
          <line x1="50" y1="4" x2="50" y2="14" stroke="#9bb8d8" strokeWidth="3" strokeLinecap="round" />
          <circle cx="50" cy="4" r="5" fill="#40d8c8" />
          <circle cx="50" cy="4" r="8" fill="none" stroke="#40d8c8" strokeWidth="1.5" opacity="0.5" />
        </svg>
      </motion.div>

      {/* Orbiting stars */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          style={{
            position: 'absolute',
            width: 3,
            height: 3,
            borderRadius: '50%',
            background: '#90c4ff',
            left: [12, 70, 42][i],
            top: [84, 78, 107][i],
          }}
          animate={{ opacity: [0.25, 1, 0.25], scale: [0.7, 1.4, 0.7] }}
          transition={{ duration: 1.8 + i * 0.55, repeat: Infinity, delay: i * 0.45 }}
        />
      ))}
    </Box>
  )
}
