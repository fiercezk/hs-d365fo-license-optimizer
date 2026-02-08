import { renderWithProviders, screen } from '@/__tests__/utils/test-utils'
import { Sidebar } from '@/components/layout/sidebar'
import { usePathname } from 'next/navigation'

// Mock Next.js navigation hooks
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}))

const mockUsePathname = usePathname as jest.MockedFunction<typeof usePathname>

describe('Sidebar', () => {
  beforeEach(() => {
    // Default to dashboard path
    mockUsePathname.mockReturnValue('/dashboard')
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Logo and Branding', () => {
    it('should render the logo with initials "LA"', () => {
      renderWithProviders(<Sidebar />)
      const logo = screen.getByText('LA')
      expect(logo).toBeInTheDocument()
      expect(logo).toHaveClass('text-white')
    })

    it('should render the brand name "License Agent"', () => {
      renderWithProviders(<Sidebar />)
      expect(screen.getByText('License Agent')).toBeInTheDocument()
    })

    it('should render the subtitle "D365 FO Optimizer"', () => {
      renderWithProviders(<Sidebar />)
      expect(screen.getByText('D365 FO Optimizer')).toBeInTheDocument()
    })

    it('should have a link to /dashboard on the logo', () => {
      renderWithProviders(<Sidebar />)
      const logoLink = screen.getByText('License Agent').closest('a')
      expect(logoLink).toHaveAttribute('href', '/dashboard')
    })
  })

  describe('Navigation Items', () => {
    it('should render all primary navigation items', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('License Optimization')).toBeInTheDocument()
      expect(screen.getByText('Security & Compliance')).toBeInTheDocument()
      expect(screen.getByText('New User Wizard')).toBeInTheDocument()
      expect(screen.getByText('Recommendations')).toBeInTheDocument()
      expect(screen.getByText('Administration')).toBeInTheDocument()
    })

    it('should render License Optimization submenu items', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('Overview')).toBeInTheDocument()
      expect(screen.getByText('Read-Only Users')).toBeInTheDocument()
      expect(screen.getByText('License Minority')).toBeInTheDocument()
      expect(screen.getByText('Cross-Role Optimization')).toBeInTheDocument()
    })

    it('should render Security & Compliance submenu items', () => {
      renderWithProviders(<Sidebar />)

      expect(screen.getByText('SoD Violations')).toBeInTheDocument()
      expect(screen.getByText('Anomalous Activity')).toBeInTheDocument()
      expect(screen.getByText('Compliance Reports')).toBeInTheDocument()
    })

    it('should have correct href attributes for navigation links', () => {
      renderWithProviders(<Sidebar />)

      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink).toHaveAttribute('href', '/dashboard')

      const wizardLink = screen.getByText('New User Wizard').closest('a')
      expect(wizardLink).toHaveAttribute('href', '/wizard')

      const recsLink = screen.getByText('Recommendations').closest('a')
      expect(recsLink).toHaveAttribute('href', '/recommendations')

      const adminLink = screen.getByText('Administration').closest('a')
      expect(adminLink).toHaveAttribute('href', '/admin')
    })

    it('should have correct href attributes for submenu links', () => {
      renderWithProviders(<Sidebar />)

      const readOnlyLink = screen.getByText('Read-Only Users').closest('a')
      expect(readOnlyLink).toHaveAttribute('href', '/algorithms/readonly')

      const sodLink = screen.getByText('SoD Violations').closest('a')
      expect(sodLink).toHaveAttribute('href', '/algorithms/security/sod')
    })
  })

  describe('Active State', () => {
    it('should highlight Dashboard when on /dashboard', () => {
      mockUsePathname.mockReturnValue('/dashboard')
      renderWithProviders(<Sidebar />)

      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink).toHaveClass('bg-brand-50', 'text-brand-700')
    })

    it('should highlight License Optimization when on /algorithms', () => {
      mockUsePathname.mockReturnValue('/algorithms')
      renderWithProviders(<Sidebar />)

      const algoLink = screen.getByText('License Optimization').closest('a')
      expect(algoLink).toHaveClass('bg-brand-50', 'text-brand-700')
    })

    it('should highlight License Optimization when on /algorithms/readonly', () => {
      mockUsePathname.mockReturnValue('/algorithms/readonly')
      renderWithProviders(<Sidebar />)

      const algoLink = screen.getByText('License Optimization').closest('a')
      expect(algoLink).toHaveClass('bg-brand-50', 'text-brand-700')
    })

    it('should highlight submenu item when active', () => {
      mockUsePathname.mockReturnValue('/algorithms/readonly')
      renderWithProviders(<Sidebar />)

      const readOnlyLink = screen.getByText('Read-Only Users').closest('a')
      expect(readOnlyLink).toHaveClass('text-brand-700', 'font-medium')
    })

    it('should not highlight inactive links', () => {
      mockUsePathname.mockReturnValue('/dashboard')
      renderWithProviders(<Sidebar />)

      const wizardLink = screen.getByText('New User Wizard').closest('a')
      expect(wizardLink).not.toHaveClass('bg-brand-50')
      expect(wizardLink).toHaveClass('text-gray-600')
    })
  })

  describe('Agent Health Status', () => {
    it('should render agent health footer', () => {
      renderWithProviders(<Sidebar />)
      expect(screen.getByText('Agent Healthy')).toBeInTheDocument()
    })

    it('should display green status indicator', () => {
      renderWithProviders(<Sidebar />)
      const healthText = screen.getByText('Agent Healthy')
      const healthContainer = healthText.parentElement

      // Status indicator should be in the same container
      expect(healthContainer).toBeInTheDocument()

      // Query for the green dot by its classes
      const statusIndicator = healthContainer?.querySelector('.bg-green-400')
      expect(statusIndicator).toBeInTheDocument()
      expect(statusIndicator).toHaveClass('rounded-full')
    })
  })

  describe('Accessibility', () => {
    it('should have navigation role', () => {
      renderWithProviders(<Sidebar />)
      const nav = screen.getByRole('navigation')
      expect(nav).toBeInTheDocument()
    })

    it('should have complementary role on aside element', () => {
      renderWithProviders(<Sidebar />)
      const aside = screen.getByRole('complementary')
      expect(aside).toBeInTheDocument()
    })
  })

  describe('Layout Structure', () => {
    it('should have fixed height sidebar', () => {
      renderWithProviders(<Sidebar />)
      const aside = screen.getByRole('complementary')
      expect(aside).toHaveClass('h-screen')
    })

    it('should have fixed width of 64 (256px)', () => {
      renderWithProviders(<Sidebar />)
      const aside = screen.getByRole('complementary')
      expect(aside).toHaveClass('w-64')
    })

    it('should have right border', () => {
      renderWithProviders(<Sidebar />)
      const aside = screen.getByRole('complementary')
      expect(aside).toHaveClass('border-r')
    })

    it('should have white background', () => {
      renderWithProviders(<Sidebar />)
      const aside = screen.getByRole('complementary')
      expect(aside).toHaveClass('bg-white')
    })
  })
})
