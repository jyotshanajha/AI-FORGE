import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  Stack,
} from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'

interface LoginFormProps {
  onLogin: (email: string, password: string) => Promise<void>
  onRegister: (email: string, password: string) => Promise<void>
  onGoogle: () => Promise<void>
  isLoading: boolean
  loginError?: string
  registerError?: string
}

export function LoginForm({
  onLogin,
  onRegister,
  onGoogle,
  isLoading,
  loginError,
  registerError,
}: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [localError, setLocalError] = useState('')

  // Check for OAuth errors in URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const error = params.get('error')
    const message = params.get('message')
    if (error) {
      setLocalError(message ? `${error}: ${message}` : error)
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  const error = loginError || registerError || localError

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')

    if (!email || !password) {
      setLocalError('Please enter both email and password')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLocalError('Please enter a valid email address')
      return
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters')
      return
    }

    try {
      if (isRegisterMode) {
        await onRegister(email, password)
      } else {
        await onLogin(email, password)
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const handleGoogleClick = async () => {
    setLocalError('')
    try {
      await onGoogle()
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Google sign-in failed')
    }
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          minHeight: '100vh',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
          }}
        >
          <Box>
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
              Amzur AI Chat
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Internal assistant for employee workflows
            </Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@amzur.com"
                disabled={isLoading}
                variant="outlined"
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                disabled={isLoading}
                variant="outlined"
              />
              <Button
                fullWidth
                variant="contained"
                type="submit"
                disabled={isLoading}
                sx={{ py: 1.5 }}
              >
                {isLoading ? <CircularProgress size={24} /> : isRegisterMode ? 'Sign Up' : 'Sign In'}
              </Button>
            </Stack>
          </form>

          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2">
              {isRegisterMode ? 'Already have an account?' : "Don't have an account?"}{' '}
              <Typography
                component="button"
                variant="body2"
                onClick={() => {
                  setIsRegisterMode(!isRegisterMode)
                  setLocalError('')
                }}
                sx={{
                  background: 'none',
                  border: 'none',
                  color: 'primary.main',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  p: 0,
                  '&:hover': {
                    textDecoration: 'none',
                  },
                }}
              >
                {isRegisterMode ? 'Sign In' : 'Sign Up'}
              </Typography>
            </Typography>
          </Box>

          <Divider>or</Divider>

          <Button
            fullWidth
            variant="outlined"
            startIcon={<GoogleIcon />}
            onClick={handleGoogleClick}
            disabled={isLoading}
            sx={{ py: 1.5 }}
          >
            Sign in with Google
          </Button>
        </Paper>
      </Box>
    </Container>
  )
}
