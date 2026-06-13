import { Bell, User, ChevronDown } from 'lucide-react'
import { useAuthStore } from '../../stores/auth-store'
import { useState } from 'react'
import { useLogout } from '../../hooks'
import { Link } from '@tanstack/react-router'

export function Navbar() {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()
  const [showMenu, setShowMenu] = useState(false)

  return (
    <header className="h-14 bg-surface-800 border-b border-surface-600 flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex-1" />
      <div className="flex items-center gap-3">
        <button className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-200 rounded-lg hover:bg-surface-700 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 text-sm text-slate-300 hover:text-white px-2 py-1.5 rounded-lg hover:bg-surface-700 transition-colors"
          >
            <div className="w-7 h-7 bg-brand-600 rounded-full flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="hidden sm:block font-medium">{user?.full_name || 'User'}</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>
          {showMenu && (
            <div className="absolute right-0 mt-1 w-48 card border border-surface-500 shadow-xl py-1 z-50">
              <Link
                to="/dashboard/settings"
                className="block px-4 py-2 text-sm text-slate-300 hover:bg-surface-700 hover:text-white"
                onClick={() => setShowMenu(false)}
              >
                Settings
              </Link>
              <hr className="border-surface-600 my-1" />
              <button
                onClick={() => { logout.mutate(); setShowMenu(false) }}
                className="block w-full text-left px-4 py-2 text-sm text-accent-red hover:bg-accent-red/10"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
