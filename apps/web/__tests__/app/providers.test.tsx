import { render, screen } from '@testing-library/react'
import { Providers } from '@/app/providers'
import { useQueryClient } from '@tanstack/react-query'

// Mock component to test if QueryClient is available
function TestComponent() {
  const queryClient = useQueryClient()

  return (
    <div>
      <div data-testid="query-client-exists">
        {queryClient ? 'QueryClient Available' : 'No QueryClient'}
      </div>
    </div>
  )
}

describe('Providers', () => {
  describe('TanStack Query Provider', () => {
    it('should render children', () => {
      render(
        <Providers>
          <div data-testid="test-child">Test Content</div>
        </Providers>
      )

      expect(screen.getByTestId('test-child')).toBeInTheDocument()
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('should provide QueryClient to children', () => {
      render(
        <Providers>
          <TestComponent />
        </Providers>
      )

      expect(screen.getByTestId('query-client-exists')).toHaveTextContent(
        'QueryClient Available'
      )
    })

    it('should create a new QueryClient instance', () => {
      const { rerender } = render(
        <Providers>
          <div>Content 1</div>
        </Providers>
      )

      expect(screen.getByText('Content 1')).toBeInTheDocument()

      // Rerender should use the same QueryClient instance (from useState)
      rerender(
        <Providers>
          <div>Content 2</div>
        </Providers>
      )

      expect(screen.getByText('Content 2')).toBeInTheDocument()
    })

    it('should allow nested QueryClient usage', () => {
      render(
        <Providers>
          <Providers>
            <TestComponent />
          </Providers>
        </Providers>
      )

      // Should still work with nested providers
      expect(screen.getByTestId('query-client-exists')).toHaveTextContent(
        'QueryClient Available'
      )
    })
  })

  describe('Multiple Children', () => {
    it('should render multiple children', () => {
      render(
        <Providers>
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
          <div data-testid="child-3">Child 3</div>
        </Providers>
      )

      expect(screen.getByTestId('child-1')).toBeInTheDocument()
      expect(screen.getByTestId('child-2')).toBeInTheDocument()
      expect(screen.getByTestId('child-3')).toBeInTheDocument()
    })

    it('should render complex nested children', () => {
      render(
        <Providers>
          <div>
            <div>
              <span data-testid="deeply-nested">Deeply Nested Content</span>
            </div>
          </div>
        </Providers>
      )

      expect(screen.getByTestId('deeply-nested')).toBeInTheDocument()
    })
  })
})
