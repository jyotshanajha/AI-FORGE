import { useEffect, useRef, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { LoginForm } from './components/auth/LoginForm'
import { EinsteinFlash } from './components/EinsteinFlash'
import { AstronautHelper } from './components/AstronautHelper'
import { useAuth } from './hooks/useAuth'
import ChatPage from './pages/ChatPage'

const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#05091b',
      paper: 'rgba(17,26,56,0.58)',
    },
    text: {
      primary: '#e7f1ff',
      secondary: '#9fb5da',
    },
    primary: {
      main: '#5ba6ff',
    },
    secondary: {
      main: '#9b8dff',
    },
  },
  typography: {
    fontFamily: [
      'SF Pro Display',
      'SF Pro Text',
      'Avenir Next',
      'Segoe UI',
      'Helvetica Neue',
      'Arial',
      'sans-serif',
    ].join(','),
    h5: {
      fontWeight: 640,
      letterSpacing: '-0.02em',
    },
    h6: {
      fontWeight: 620,
      letterSpacing: '-0.015em',
    },
    body1: {
      lineHeight: 1.65,
      letterSpacing: '0.002em',
    },
    button: {
      textTransform: 'none',
      letterSpacing: '0.015em',
      fontWeight: 560,
    },
    caption: {
      letterSpacing: '0.02em',
    },
  },
  shape: {
    borderRadius: 18,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background:
            'radial-gradient(1600px 800px at -12% -10%, rgba(64,128,255,0.22), transparent), radial-gradient(1200px 760px at 108% 12%, rgba(168,117,255,0.2), transparent), radial-gradient(1000px 640px at 50% 110%, rgba(69,189,255,0.16), transparent), linear-gradient(180deg, #040716 0%, #070b1f 35%, #090f2a 100%)',
          minHeight: '100vh',
          color: '#e7f1ff',
        },
        '#root': {
          minHeight: '100vh',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(152, 188, 255, 0.22)',
          boxShadow: '0 14px 36px rgba(6, 10, 30, 0.42)',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          border: '1px solid rgba(255,255,255,0.18)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          '&.MuiAlert-colorError': {
            background:
              'linear-gradient(135deg, rgba(94, 30, 72, 0.66), rgba(41, 16, 52, 0.58))',
            color: '#ffd8f6',
            border: '1px solid rgba(255, 123, 214, 0.4)',
            boxShadow: '0 12px 26px rgba(20, 7, 35, 0.46), inset 0 0 24px rgba(255, 124, 214, 0.08)',
          },
        },
        icon: {
          color: '#ff91df',
        },
      },
    },
  },
})

export default function App() {
  const { user, isLoading, isAuthenticated, loginMutation, registerMutation, googleLoginMutation } = useAuth()
  const [showEinstein, setShowEinstein] = useState(false)
  const prevIsAuthRef = useRef(false)

  useEffect(() => {
    if (!prevIsAuthRef.current && isAuthenticated) {
      setShowEinstein(true)
    }
    prevIsAuthRef.current = isAuthenticated
  }, [isAuthenticated])

  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', fontSize: '1rem', color: '#c2e9ff', fontWeight: 500 }}>
          Loading app...
        </div>
      </ThemeProvider>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AstronautHelper />
        <LoginForm
          isLoading={loginMutation.isPending || registerMutation.isPending || googleLoginMutation.isPending}
          loginError={loginMutation.error?.message}
          registerError={registerMutation.error?.message}
          onLogin={async (email, password) => {
            await loginMutation.mutateAsync({ email, password })
          }}
          onRegister={async (email, password) => {
            await registerMutation.mutateAsync({ email, password })
          }}
          onGoogle={async () => {
            await googleLoginMutation.mutateAsync()
          }}
        />
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AnimatePresence>
        {showEinstein && <EinsteinFlash onComplete={() => setShowEinstein(false)} />}
      </AnimatePresence>
      <ChatPage />
    </ThemeProvider>
  )
}
