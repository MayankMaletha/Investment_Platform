import { motion } from 'framer-motion'
import { Link } from '@tanstack/react-router'
import {
  Zap, TrendingUp, Shield, Brain, FileText, BarChart2,
  ArrowRight, Star, ChevronRight, Activity, Globe, Lock
} from 'lucide-react'

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } }
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <motion.div variants={fadeUp} className="card-hover p-6">
      <div className="w-10 h-10 bg-brand-600/10 rounded-xl flex items-center justify-center text-brand-400 mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
      <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
    </motion.div>
  )
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface-900 text-slate-100">
      {/* Nav */}
      <nav className="border-b border-surface-700 bg-surface-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">InvestAI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="btn-ghost text-sm">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm">Get started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-24 pb-20 px-6">
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-600/5 rounded-full blur-3xl" />
          <div className="absolute top-20 right-10 w-72 h-72 bg-accent-purple/5 rounded-full blur-3xl" />
          <div className="absolute top-40 left-10 w-56 h-56 bg-accent-green/5 rounded-full blur-3xl" />
        </div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 bg-brand-600/10 border border-brand-600/20 text-brand-400 text-xs px-4 py-2 rounded-full mb-8">
              <Star className="w-3.5 h-3.5" />
              Powered by LangGraph + FinBERT + RAG
            </div>
            <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight tracking-tight">
              AI-Powered{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-accent-cyan">
                Investment Intelligence
              </span>
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              Institutional-grade stock analysis, crypto insights, portfolio risk management,
              and document intelligence — all powered by multi-agent AI.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Link
                to="/register"
                className="btn-primary flex items-center gap-2 px-8 py-3 text-base"
              >
                Start investing smarter <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="btn-secondary flex items-center gap-2 px-8 py-3 text-base"
              >
                Sign in
              </Link>
            </div>
          </motion.div>

          {/* Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mt-16 relative"
          >
            <div className="bg-surface-800 border border-surface-600 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-accent-red/60" />
                <div className="w-3 h-3 rounded-full bg-accent-yellow/60" />
                <div className="w-3 h-3 rounded-full bg-accent-green/60" />
                <div className="ml-4 bg-surface-700 rounded text-xs text-slate-500 px-3 py-1">InvestAI Dashboard</div>
              </div>
              <div className="grid grid-cols-4 gap-3 mb-4">
                {[
                  { label: 'Portfolio Value', value: '$124,832', change: '+2.4%', color: 'text-accent-green' },
                  { label: 'Today P&L', value: '+$2,940', change: '+2.41%', color: 'text-accent-green' },
                  { label: 'Risk Score', value: '42.3', change: 'LOW', color: 'text-accent-green' },
                  { label: 'Sharpe Ratio', value: '1.84', change: 'Good', color: 'text-accent-yellow' },
                ].map(({ label, value, change, color }) => (
                  <div key={label} className="bg-surface-700 rounded-xl p-3">
                    <div className="text-xs text-slate-500 mb-1">{label}</div>
                    <div className="text-base font-bold text-slate-100">{value}</div>
                    <div className={`text-xs ${color}`}>{change}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2 bg-surface-700 rounded-xl p-3 h-24 flex items-center justify-center">
                  <div className="w-full h-12 relative">
                    <svg viewBox="0 0 200 40" className="w-full h-full">
                      <defs>
                        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.3" />
                          <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      <path d="M0,30 L20,25 L40,28 L60,20 L80,22 L100,15 L120,18 L140,10 L160,12 L180,8 L200,5" stroke="#0ea5e9" strokeWidth="1.5" fill="none" />
                      <path d="M0,30 L20,25 L40,28 L60,20 L80,22 L100,15 L120,18 L140,10 L160,12 L180,8 L200,5 L200,40 L0,40Z" fill="url(#chartGrad)" />
                    </svg>
                  </div>
                </div>
                <div className="bg-surface-700 rounded-xl p-3 space-y-1.5">
                  {['AAPL +1.2%', 'MSFT +0.8%', 'NVDA +3.1%'].map((s) => (
                    <div key={s} className="text-xs text-accent-green font-medium">{s}</div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-surface-800/30">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-slate-100 mb-3">Everything you need to invest smarter</h2>
            <p className="text-slate-500 max-w-xl mx-auto">
              A complete suite of AI tools covering every aspect of investment analysis
            </p>
          </motion.div>
          <motion.div
            variants={stagger}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
          >
            <FeatureCard
              icon={<TrendingUp className="w-5 h-5" />}
              title="Stock Analysis"
              desc="AI-powered technical and fundamental analysis with RSI, MACD, Bollinger Bands, and multi-agent recommendations."
            />
            <FeatureCard
              icon={<Activity className="w-5 h-5" />}
              title="Crypto Intelligence"
              desc="Real-time crypto prices, trend analysis, and FinBERT sentiment scoring for all major cryptocurrencies."
            />
            <FeatureCard
              icon={<Brain className="w-5 h-5" />}
              title="LangGraph AI Agents"
              desc="Six specialized agents — Technical, News, Sentiment, Risk, Memory, and Recommendation — collaborate for deeper insights."
            />
            <FeatureCard
              icon={<Shield className="w-5 h-5" />}
              title="Risk Management"
              desc="Portfolio VaR, beta, Sharpe ratio, max drawdown, and diversification scoring with actionable recommendations."
            />
            <FeatureCard
              icon={<FileText className="w-5 h-5" />}
              title="Document RAG"
              desc="Upload annual reports, 10-Ks, and research papers. Query them with AI and get answers with exact citations."
            />
            <FeatureCard
              icon={<BarChart2 className="w-5 h-5" />}
              title="Portfolio Analytics"
              desc="Track holdings, P&L, sector allocation, performance charts, and risk-adjusted metrics in one place."
            />
          </motion.div>
        </div>
      </section>

      {/* AI Agent Section */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
          >
            <div>
              <div className="text-brand-400 text-sm font-semibold uppercase tracking-widest mb-3">Multi-Agent AI</div>
              <h2 className="text-3xl font-bold text-slate-100 mb-4">
                Six specialized agents, one intelligent recommendation
              </h2>
              <p className="text-slate-400 leading-relaxed mb-6">
                Our LangGraph pipeline coordinates specialized AI agents that each analyze different dimensions
                of an investment, then synthesize their findings into a clear, confident recommendation.
              </p>
              <div className="space-y-3">
                {[
                  { agent: 'Technical Agent', color: 'bg-brand-400', result: 'BULLISH · 82% confidence' },
                  { agent: 'News Agent', color: 'bg-accent-purple', result: 'POSITIVE · 78% confidence' },
                  { agent: 'Sentiment Agent', color: 'bg-accent-cyan', result: 'POSITIVE · 74% confidence' },
                  { agent: 'Risk Agent', color: 'bg-accent-yellow', result: 'MODERATE · 88% confidence' },
                  { agent: 'Recommendation Agent', color: 'bg-accent-green', result: 'BUY · 84% confidence' },
                ].map(({ agent, color, result }) => (
                  <div key={agent} className="flex items-center gap-3 p-3 bg-surface-800 rounded-lg border border-surface-600">
                    <div className={`w-2 h-2 rounded-full ${color}`} />
                    <span className="text-sm text-slate-300 flex-1">{agent}</span>
                    <span className="text-xs text-slate-500">{result}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card p-6 border border-brand-600/20">
              <div className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Agent Trace — AAPL Analysis</div>
              <div className="space-y-3">
                <div className="bg-surface-700 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-brand-400 font-medium">Technical Agent</span>
                    <span className="text-xs text-accent-green">BULLISH</span>
                  </div>
                  <p className="text-xs text-slate-500">Price above SMA50 and SMA200. RSI at 58 (healthy). MACD bullish crossover.</p>
                </div>
                <div className="bg-surface-700 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-accent-purple font-medium">News Agent</span>
                    <span className="text-xs text-accent-green">POSITIVE</span>
                  </div>
                  <p className="text-xs text-slate-500">Strong iPhone cycle reports. Services revenue beat estimates by 4%.</p>
                </div>
                <div className="bg-surface-700 rounded-lg p-3 border border-accent-green/20">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-accent-green font-medium">Final Recommendation</span>
                    <span className="text-xs font-bold text-accent-green">BUY</span>
                  </div>
                  <p className="text-xs text-slate-500">Confidence: 84%. Strong technical setup with positive macro catalysts.</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* RAG Section */}
      <section className="py-20 px-6 bg-surface-800/30">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
          >
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-4 h-4 text-brand-400" />
                <span className="text-sm font-medium text-slate-300">Document Intelligence</span>
              </div>
              <div className="bg-surface-700 rounded-lg p-3 mb-3">
                <div className="text-xs text-slate-500 mb-1">Query</div>
                <p className="text-sm text-slate-200">"What are Apple's key supply chain risks mentioned in the 2024 annual report?"</p>
              </div>
              <div className="bg-surface-700 rounded-lg p-3 mb-3 border border-brand-600/20">
                <div className="text-xs text-brand-400 mb-1">AI Answer</div>
                <p className="text-sm text-slate-300">Apple highlighted three primary supply chain risks: concentration in Taiwan for TSMC manufacturing, geopolitical tension impact on logistics, and single-source component dependencies for certain camera modules...</p>
              </div>
              <div className="space-y-1.5">
                <div className="text-xs text-slate-600 mb-1">Sources</div>
                {[
                  { file: 'Apple_Annual_Report_2024.pdf', page: 37 },
                  { file: 'Apple_10K_2024.pdf', page: 112 },
                ].map(({ file, page }) => (
                  <div key={file} className="flex items-center gap-2 text-xs text-slate-500">
                    <FileText className="w-3 h-3 text-brand-400" />
                    {file} · Page {page}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="text-brand-400 text-sm font-semibold uppercase tracking-widest mb-3">RAG Pipeline</div>
              <h2 className="text-3xl font-bold text-slate-100 mb-4">
                Query your financial documents with AI
              </h2>
              <p className="text-slate-400 leading-relaxed mb-6">
                Upload annual reports, 10-K filings, earnings transcripts, and research papers.
                Our RAG pipeline indexes them and answers your questions with precise citations.
              </p>
              <div className="space-y-3">
                {['PDF Annual Reports', 'Word Documents (DOCX)', 'Excel Spreadsheets (XLSX)', 'Plain Text Files'].map((f) => (
                  <div key={f} className="flex items-center gap-2 text-sm text-slate-400">
                    <ChevronRight className="w-4 h-4 text-brand-400" />
                    {f}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-slate-100 mb-4">
              Ready to invest with AI?
            </h2>
            <p className="text-slate-500 mb-8">
              Join investors using AI-powered analysis to make better decisions.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Link to="/register" className="btn-primary flex items-center gap-2 px-8 py-3 text-base">
                Create free account <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login" className="btn-ghost flex items-center gap-2 px-8 py-3 text-base">
                Sign in
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-700 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-brand-600 rounded flex items-center justify-center">
              <Zap className="w-3 h-3 text-white" />
            </div>
            <span className="font-bold text-slate-300">InvestAI</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <Lock className="w-3 h-3" />
            <span>Not financial advice. For educational purposes only.</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-slate-500">
            <span>© 2025 InvestAI</span>
            <span className="flex items-center gap-1">
              <Globe className="w-3 h-3" /> AI Investment Platform
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
