import { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Shield, Bell, Palette, LogOut, Trash2, Save, Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '../../stores/auth-store'
import { useLogout } from '../../hooks'
import toast from 'react-hot-toast'

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [notifications, setNotifications] = useState({
    priceAlerts: true,
    newsDigest: false,
    portfolioSummary: true,
    riskAlerts: true,
  })

  const handleSaveProfile = () => {
    toast.success('Profile updated')
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <User className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-semibold text-slate-200">Profile</h2>
        </div>
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-brand-600/20 rounded-full flex items-center justify-center text-2xl font-bold text-brand-400">
            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div>
            <div className="font-semibold text-slate-200">{user?.full_name}</div>
            <div className="text-sm text-slate-500">{user?.email}</div>
            <div className="text-xs text-slate-600 mt-0.5">
              Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Full name</label>
            <input
              type="text"
              defaultValue={user?.full_name || ''}
              className="input w-full"
            />
          </div>
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              defaultValue={user?.email || ''}
              className="input w-full"
              disabled
            />
          </div>
        </div>
        <button onClick={handleSaveProfile} className="btn-primary mt-4 flex items-center gap-2">
          <Save className="w-4 h-4" /> Save changes
        </button>
      </motion.div>

      {/* Security */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <Shield className="w-5 h-5 text-accent-yellow" />
          <h2 className="text-base font-semibold text-slate-200">Security</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="label">Current password</label>
            <div className="relative">
              <input type={showPassword ? 'text' : 'password'} placeholder="••••••••" className="input w-full pr-10" />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">New password</label>
              <input type="password" placeholder="••••••••" className="input w-full" />
            </div>
            <div>
              <label className="label">Confirm new password</label>
              <input type="password" placeholder="••••••••" className="input w-full" />
            </div>
          </div>
          <button
            onClick={() => toast.success('Password updated')}
            className="btn-secondary flex items-center gap-2"
          >
            <Shield className="w-4 h-4" /> Update password
          </button>
        </div>
      </motion.div>

      {/* Notifications */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <Bell className="w-5 h-5 text-accent-purple" />
          <h2 className="text-base font-semibold text-slate-200">Notifications</h2>
        </div>
        <div className="space-y-4">
          {[
            { key: 'priceAlerts', label: 'Price alerts', desc: 'Get notified when tracked stocks hit your targets' },
            { key: 'newsDigest', label: 'Daily news digest', desc: 'Morning summary of market-moving news' },
            { key: 'portfolioSummary', label: 'Portfolio summary', desc: 'Weekly portfolio performance report' },
            { key: 'riskAlerts', label: 'Risk alerts', desc: 'Alerts when portfolio risk exceeds thresholds' },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-slate-200">{label}</div>
                <div className="text-xs text-slate-500">{desc}</div>
              </div>
              <button
                onClick={() => setNotifications((prev) => ({ ...prev, [key]: !prev[key as keyof typeof prev] }))}
                className={`w-10 h-5 rounded-full transition-colors relative ${
                  notifications[key as keyof typeof notifications] ? 'bg-brand-600' : 'bg-surface-500'
                }`}
              >
                <div
                  className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${
                    notifications[key as keyof typeof notifications] ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Theme */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <Palette className="w-5 h-5 text-accent-cyan" />
          <h2 className="text-base font-semibold text-slate-200">Appearance</h2>
        </div>
        <div className="flex gap-3">
          {['Dark', 'Darker', 'System'].map((theme) => (
            <button
              key={theme}
              onClick={() => toast.success(`Theme: ${theme}`)}
              className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                theme === 'Dark'
                  ? 'border-brand-500 bg-brand-600/10 text-brand-400'
                  : 'border-surface-500 text-slate-400 hover:border-surface-400'
              }`}
            >
              {theme}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Sessions & Danger Zone */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card p-6 border-accent-red/20">
        <h2 className="text-base font-semibold text-slate-200 mb-4">Account</h2>
        <div className="space-y-3">
          <button
            onClick={() => logout.mutate()}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-accent-red transition-colors"
          >
            <LogOut className="w-4 h-4" /> Sign out of all sessions
          </button>
          <div className="border-t border-surface-600 pt-3">
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 text-sm text-accent-red hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-4 h-4" /> Delete account
              </button>
            ) : (
              <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4">
                <p className="text-sm text-accent-red font-medium mb-2">Are you sure? This cannot be undone.</p>
                <div className="flex gap-2">
                  <button className="btn-primary bg-accent-red hover:bg-red-500 text-xs px-3 py-1.5">
                    Delete permanently
                  </button>
                  <button onClick={() => setShowDeleteConfirm(false)} className="btn-secondary text-xs px-3 py-1.5">
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
