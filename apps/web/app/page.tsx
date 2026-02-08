import { redirect } from 'next/navigation'

/**
 * Root page - redirects to Dashboard.
 *
 * This ensures the home page (/) has a defined route
 * while we build out the production web app.
 */
export default function HomePage() {
  redirect('/dashboard')
}
