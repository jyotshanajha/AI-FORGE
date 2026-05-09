import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { LoginForm } from './components/auth/LoginForm'
import { useAuth } from './hooks/useAuth'
import ChatPage from './pages/ChatPage'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1e3a8a',
    },
    secondary: {
      main: '#06b6d4',
    },
  },
})

export default function App() {
  const { user, isLoading, isAuthenticated, loginMutation, registerMutation, googleLoginMutation } = useAuth()

  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', fontSize: '0.875rem', color: 'rgba(0,0,0,0.7)' }}>
          Loading...
        </div>
      </ThemeProvider>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
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
      <ChatPage />
    </ThemeProvider>
  )
}
