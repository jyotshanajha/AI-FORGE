import { useEffect, useRef, useState } from 'react'
import { Box } from '@mui/material'
import { motion, useMotionValue, useReducedMotion, useSpring } from 'framer-motion'

const STARS = [
  { top: '8%', left: '12%', size: 2.2, delay: 0.2, duration: 2.8 },
  { top: '16%', left: '72%', size: 1.8, delay: 0.6, duration: 3.4 },
  { top: '23%', left: '38%', size: 1.6, delay: 0.9, duration: 2.7 },
  { top: '31%', left: '86%', size: 2.4, delay: 0.4, duration: 3.1 },
  { top: '43%', left: '18%', size: 2, delay: 1.1, duration: 2.9 },
  { top: '52%', left: '61%', size: 1.7, delay: 0.5, duration: 3.2 },
  { top: '64%', left: '28%', size: 2.1, delay: 0.7, duration: 2.6 },
  { top: '72%', left: '77%', size: 1.9, delay: 1.2, duration: 3.3 },
  { top: '81%', left: '44%', size: 1.6, delay: 0.3, duration: 2.5 },
  { top: '89%', left: '9%', size: 2.3, delay: 0.8, duration: 3.5 },
]

type TrailPoint = {
  id: number
  x: number
  y: number
}

export function CosmicBackdrop() {
  const prefersReducedMotion = useReducedMotion()
  const [trailPoints, setTrailPoints] = useState<TrailPoint[]>([])
  const pointerX = useMotionValue(0)
  const pointerY = useMotionValue(0)
  const scrollDepth = useMotionValue(0)
  const driftX = useSpring(pointerX, { stiffness: 28, damping: 20, mass: 0.8 })
  const driftY = useSpring(pointerY, { stiffness: 28, damping: 20, mass: 0.8 })
  const depthY = useSpring(scrollDepth, { stiffness: 24, damping: 20, mass: 1 })
  const driftXSoft = useSpring(driftX, { stiffness: 22, damping: 18, mass: 0.9 })
  const driftYSoft = useSpring(driftY, { stiffness: 22, damping: 18, mass: 0.9 })
  const driftXFar = useSpring(driftX, { stiffness: 16, damping: 17, mass: 1.1 })
  const depthYSoft = useSpring(depthY, { stiffness: 20, damping: 16, mass: 1 })
  const rafRef = useRef<number | null>(null)
  const trailIdRef = useRef(0)
  const lastTrailStampRef = useRef(0)

  useEffect(() => {
    if (prefersReducedMotion || typeof window === 'undefined') {
      return
    }

    const scheduleFromPointer = (clientX: number, clientY: number) => {
      if (rafRef.current !== null) {
        return
      }

      rafRef.current = window.requestAnimationFrame(() => {
        rafRef.current = null
        const nx = clientX / window.innerWidth - 0.5
        const ny = clientY / window.innerHeight - 0.5

        pointerX.set(nx * 18)
        pointerY.set(ny * 14)

        const now = performance.now()
        if (now - lastTrailStampRef.current > 28) {
          trailIdRef.current += 1
          lastTrailStampRef.current = now
          setTrailPoints((prev) => {
            const next = [...prev, { id: trailIdRef.current, x: clientX, y: clientY }]
            return next.slice(-14)
          })
        }
      })
    }

    const onPointerMove = (event: PointerEvent) => {
      scheduleFromPointer(event.clientX, event.clientY)
    }

    const onScroll = () => {
      const nextDepth = Math.min(window.scrollY, 900) * 0.035
      scrollDepth.set(nextDepth)
    }

    window.addEventListener('pointermove', onPointerMove, { passive: true })
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()

    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('scroll', onScroll)
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current)
      }
    }
  }, [pointerX, pointerY, prefersReducedMotion, scrollDepth])

  return (
    <Box
      aria-hidden
      sx={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      <motion.div
        style={{
          position: 'absolute',
          width: 260,
          height: 260,
          top: -80,
          left: -70,
          borderRadius: '50%',
          background:
            'radial-gradient(circle at 30% 30%, rgba(109, 207, 255, 0.45), rgba(19, 26, 57, 0.06) 66%, transparent 72%)',
          filter: 'blur(2px)',
          x: prefersReducedMotion ? 0 : driftX,
          y: prefersReducedMotion ? 0 : driftY,
        }}
        animate={{ opacity: [0.88, 1, 0.9] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
      />

      <motion.div
        style={{
          position: 'absolute',
          width: 180,
          height: 180,
          right: -30,
          top: 90,
          borderRadius: '50%',
          background:
            'radial-gradient(circle at 28% 30%, rgba(241, 167, 255, 0.42), rgba(45, 16, 62, 0.18) 62%, transparent 72%)',
          filter: 'blur(1.5px)',
          x: prefersReducedMotion ? 0 : driftXSoft,
          y: prefersReducedMotion ? 0 : driftYSoft,
        }}
        animate={{ opacity: [0.76, 0.93, 0.8] }}
        transition={{ duration: 7.5, repeat: Infinity, ease: 'easeInOut' }}
      />

      <motion.div
        style={{
          position: 'absolute',
          width: 76,
          height: 76,
          right: 120,
          bottom: 120,
          borderRadius: '50%',
          border: '1px solid rgba(159, 219, 255, 0.35)',
          x: prefersReducedMotion ? 0 : driftXFar,
          y: prefersReducedMotion ? 0 : depthYSoft,
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: -2,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 6,
            height: 6,
            borderRadius: '50%',
            backgroundColor: 'rgba(205, 238, 255, 0.85)',
          }}
        />
      </motion.div>

      {STARS.map((star) => (
        <motion.span
          key={`${star.top}-${star.left}`}
          style={{
            position: 'absolute',
            top: star.top,
            left: star.left,
            width: star.size,
            height: star.size,
            borderRadius: '50%',
            background: 'rgba(231, 244, 255, 0.95)',
            boxShadow: '0 0 8px rgba(196, 230, 255, 0.75)',
          }}
          animate={{ opacity: [0.25, 0.95, 0.4], scale: [1, 1.25, 0.9] }}
          transition={{
            duration: star.duration,
            delay: star.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {!prefersReducedMotion &&
        trailPoints.map((point, index) => {
          const ageFactor = (index + 1) / trailPoints.length
          return (
            <motion.span
              key={point.id}
              style={{
                position: 'fixed',
                left: point.x - 3,
                top: point.y - 3,
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: 'rgba(182, 233, 255, 0.92)',
                boxShadow: '0 0 10px rgba(139, 224, 255, 0.78)',
                pointerEvents: 'none',
                zIndex: 1,
              }}
              initial={{ opacity: 0.72 * ageFactor, scale: 0.95 }}
              animate={{ opacity: 0, scale: 0.45 }}
              transition={{ duration: 0.65, ease: 'easeOut' }}
            />
          )
        })}
    </Box>
  )
}
