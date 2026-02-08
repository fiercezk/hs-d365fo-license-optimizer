import { renderWithProviders, screen } from '@/__tests__/utils/test-utils'
import { Header } from '@/components/layout/header'
import userEvent from '@testing-library/user-event'

describe('Header', () => {
  describe('Search Functionality', () => {
    it('should render search input', () => {
      renderWithProviders(<Header />)
      const searchInput = screen.getByPlaceholderText(
        /search users, roles, recommendations/i
      )
      expect(searchInput).toBeInTheDocument()
    })

    it('should have search input type', () => {
      renderWithProviders(<Header />)
      const searchInput = screen.getByPlaceholderText(
        /search users, roles, recommendations/i
      )
      expect(searchInput).toHaveAttribute('type', 'search')
    })

    it('should allow typing in search input', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Header />)

      const searchInput = screen.getByPlaceholderText(
        /search users, roles, recommendations/i
      ) as HTMLInputElement

      await user.type(searchInput, 'john.doe@contoso.com')

      expect(searchInput.value).toBe('john.doe@contoso.com')
    })

    it('should have proper styling classes', () => {
      renderWithProviders(<Header />)
      const searchInput = screen.getByPlaceholderText(
        /search users, roles, recommendations/i
      )

      expect(searchInput).toHaveClass('rounded-lg', 'border', 'border-gray-200')
    })
  })

  describe('Notifications', () => {
    it('should render notification button', () => {
      renderWithProviders(<Header />)
      const notificationButton = screen.getByRole('button', {
        name: /notifications/i,
      })
      expect(notificationButton).toBeInTheDocument()
    })

    it('should have screen reader text for accessibility', () => {
      renderWithProviders(<Header />)
      const srText = screen.getByText('Notifications')
      expect(srText).toHaveClass('sr-only')
    })

    it('should display notification badge', () => {
      renderWithProviders(<Header />)
      const notificationButton = screen.getByRole('button', {
        name: /notifications/i,
      })

      const badge = notificationButton.querySelector('.bg-red-500')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('rounded-full')
    })

    it('should render bell icon SVG', () => {
      renderWithProviders(<Header />)
      const notificationButton = screen.getByRole('button', {
        name: /notifications/i,
      })

      const svg = notificationButton.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveClass('h-5', 'w-5')
    })

    it('should be clickable', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Header />)

      const notificationButton = screen.getByRole('button', {
        name: /notifications/i,
      })

      await user.click(notificationButton)
      // Button should still be in the document after click
      expect(notificationButton).toBeInTheDocument()
    })
  })

  describe('User Profile', () => {
    it('should display user avatar with initials "SA"', () => {
      renderWithProviders(<Header />)
      expect(screen.getByText('SA')).toBeInTheDocument()
    })

    it('should display user name "System Admin"', () => {
      renderWithProviders(<Header />)
      expect(screen.getByText('System Admin')).toBeInTheDocument()
    })

    it('should display user email "admin@contoso.com"', () => {
      renderWithProviders(<Header />)
      expect(screen.getByText('admin@contoso.com')).toBeInTheDocument()
    })

    it('should have circular avatar', () => {
      renderWithProviders(<Header />)
      const avatar = screen.getByText('SA')
      expect(avatar).toHaveClass('rounded-full', 'bg-brand-100')
    })

    it('should have proper text styling for user name', () => {
      renderWithProviders(<Header />)
      const userName = screen.getByText('System Admin')
      expect(userName).toHaveClass('font-medium', 'text-gray-900')
    })

    it('should have proper text styling for email', () => {
      renderWithProviders(<Header />)
      const email = screen.getByText('admin@contoso.com')
      expect(email).toHaveClass('text-xs', 'text-gray-500')
    })
  })

  describe('Layout Structure', () => {
    it('should have header role', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('should have fixed height', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('h-16')
    })

    it('should have bottom border', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('border-b')
    })

    it('should have white background', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('bg-white')
    })

    it('should use flexbox for layout', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('flex', 'items-center', 'justify-between')
    })

    it('should have horizontal padding', () => {
      renderWithProviders(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('px-6')
    })
  })

  describe('Responsive Behavior', () => {
    it('should have wide search input on desktop', () => {
      renderWithProviders(<Header />)
      const searchInput = screen.getByPlaceholderText(
        /search users, roles, recommendations/i
      )
      expect(searchInput).toHaveClass('w-80')
    })
  })
})
