import { renderWithProviders, screen } from '@/__tests__/utils/test-utils'
import RootLayout from '@/app/layout'

// Mock child components to avoid complex rendering
jest.mock('@/components/layout/sidebar', () => ({
  Sidebar: () => <aside data-testid="sidebar">Sidebar Mock</aside>,
}))

jest.mock('@/components/layout/header', () => ({
  Header: () => <header data-testid="header">Header Mock</header>,
}))

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/dashboard'),
}))

describe('RootLayout', () => {
  describe('Layout Structure', () => {
    it('should render children content', () => {
      renderWithProviders(
        <RootLayout>
          <div data-testid="test-child">Test Content</div>
        </RootLayout>
      )

      expect(screen.getByTestId('test-child')).toBeInTheDocument()
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('should include Sidebar component', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })

    it('should include Header component', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('should render main content area', () => {
      renderWithProviders(
        <RootLayout>
          <div data-testid="page-content">Page</div>
        </RootLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toBeInTheDocument()
      expect(main).toContainElement(screen.getByTestId('page-content'))
    })

    it('should have gray background on main content', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toHaveClass('bg-gray-50')
    })

    it('should have padding on main content', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toHaveClass('p-6')
    })

    it('should have overflow-y-auto on main content', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toHaveClass('overflow-y-auto')
    })

    it('should use flexbox layout', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const main = screen.getByRole('main')
      const contentWrapper = main.parentElement

      expect(contentWrapper).toHaveClass('flex', 'flex-col')
    })
  })

  describe('HTML Document Structure', () => {
    it('should set lang attribute to "en"', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const html = document.documentElement
      expect(html).toHaveAttribute('lang', 'en')
    })

    it('should have antialiased font rendering', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const body = document.body
      expect(body).toHaveClass('antialiased')
    })

    it('should use sans-serif font', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const body = document.body
      expect(body).toHaveClass('font-sans')
    })
  })

  describe('Responsive Layout', () => {
    it('should have full screen height', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const layoutContainer = screen.getByRole('main').closest('.h-screen')
      expect(layoutContainer).toBeInTheDocument()
      expect(layoutContainer).toHaveClass('h-screen')
    })

    it('should hide overflow on container', () => {
      renderWithProviders(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      )

      const layoutContainer = screen.getByRole('main').closest('.overflow-hidden')
      expect(layoutContainer).toBeInTheDocument()
    })
  })
})
