import { createRouter, RouterProvider, createRoute, createRootRoute, Outlet, Navigate } from '@tanstack/react-router'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { StocksPage } from './pages/dashboard/StocksPage'
import { CryptoPage } from './pages/dashboard/CryptoPage'
import { PortfolioPage } from './pages/dashboard/PortfolioPage'
import { RiskPage } from './pages/dashboard/RiskPage'
import { NewsPage } from './pages/dashboard/NewsPage'
import { ChatPage } from './pages/dashboard/ChatPage'
import { RagPage } from './pages/dashboard/RagPage'
import { SettingsPage } from './pages/dashboard/SettingsPage'
import { DashboardLayout } from './components/layout/DashboardLayout'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { ErrorBoundary } from './components/ui/EmptyState'

// Root
const rootRoute = createRootRoute({
  component: () => <Outlet />,
})

// Public routes
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: LandingPage })
const loginRoute = createRoute({ getParentRoute: () => rootRoute, path: '/login', component: LoginPage })
const registerRoute = createRoute({ getParentRoute: () => rootRoute, path: '/register', component: RegisterPage })

// Dashboard wrapper
const dashboardLayoutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: () => (
    <ProtectedRoute>
      <ErrorBoundary>
        <DashboardLayout>
          <Outlet />
        </DashboardLayout>
      </ErrorBoundary>
    </ProtectedRoute>
  ),
})

// Dashboard children
const dashboardIndexRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/',
  component: DashboardPage,
})
const stocksRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/stocks',
  component: StocksPage,
})
const cryptoRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/crypto',
  component: CryptoPage,
})
const portfolioRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/portfolio',
  component: PortfolioPage,
})
const riskRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/risk',
  component: RiskPage,
})
const newsRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/news',
  component: NewsPage,
})
const chatRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/chat',
  component: ChatPage,
})
const ragRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/rag',
  component: RagPage,
})
const settingsRoute = createRoute({
  getParentRoute: () => dashboardLayoutRoute,
  path: '/settings',
  component: SettingsPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  registerRoute,
  dashboardLayoutRoute.addChildren([
    dashboardIndexRoute,
    stocksRoute,
    cryptoRoute,
    portfolioRoute,
    riskRoute,
    newsRoute,
    chatRoute,
    ragRoute,
    settingsRoute,
  ]),
])

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

export default function App() {
  return <RouterProvider router={router} />
}
