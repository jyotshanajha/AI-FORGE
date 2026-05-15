import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { Box, Typography } from '@mui/material'

interface EinsteinFlashProps {
  onComplete: () => void
}

export function EinsteinFlash({ onComplete }: EinsteinFlashProps) {
  useEffect(() => {
    const timer = setTimeout(onComplete, 1800)
    return () => clearTimeout(timer)
  }, [onComplete])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.04 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'grid',
        placeItems: 'center',
        background:
          'radial-gradient(ellipse 80% 60% at 50% 40%, rgba(40, 70, 180, 0.97), rgba(4, 7, 22, 0.99))',
      }}
    >
      <Box sx={{ textAlign: 'center', userSelect: 'none' }}>
        <motion.div
          initial={{ scale: 0.25, rotate: -25, y: 40 }}
          animate={{ scale: 1, rotate: 0, y: 0 }}
          transition={{ type: 'spring', stiffness: 240, damping: 18, delay: 0.05 }}
        >
          <Typography sx={{ fontSize: '9rem', lineHeight: 1, filter: 'drop-shadow(0 0 40px rgba(120,180,255,0.5))' }}>
            😜
          </Typography>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.38, duration: 0.45 }}
        >
          <Typography
            variant="h5"
            sx={{
              mt: 2,
              fontStyle: 'italic',
              color: '#aaccff',
              letterSpacing: '0.01em',
              textShadow: '0 0 30px rgba(120,180,255,0.4)',
            }}
          >
            "Imagination is more important than knowledge."
          </Typography>
          <Typography variant="caption" sx={{ color: '#5a78a8', mt: 0.75, display: 'block' }}>
            — Albert Einstein
          </Typography>
        </motion.div>

        {/* Decorative stars */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            style={{
              position: 'absolute',
              width: 4,
              height: 4,
              borderRadius: '50%',
              background: '#7ab4ff',
              left: `${15 + i * 14}%`,
              top: `${20 + (i % 3) * 20}%`,
            }}
            animate={{ opacity: [0.2, 1, 0.2], scale: [0.7, 1.4, 0.7] }}
            transition={{ duration: 1.4 + i * 0.3, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </Box>
    </motion.div>
  )
}
