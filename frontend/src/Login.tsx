import { FormEvent, useState } from 'react'
import { ArrowRight, LockKeyhole, Mail, ShieldCheck } from 'lucide-react'
import { apiError, AuthResponse, signIn } from './api'

export default function Login({ onLogin }: { onLogin: (tokens: AuthResponse) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try { const result = await signIn(email, password); onLogin(result) }
    catch (reason) { setError(apiError(reason)) }
    finally { setBusy(false) }
  }
  return <main className="login-screen"><div className="login-card"><div className="login-logo"><div className="brand-mark"><span>ம</span><i/></div><div className="brand-copy"><b>manam<span>.</span></b><small>PLATFORM ADMIN</small></div></div><div className="login-heading"><div className="eyebrow"><ShieldCheck size={13}/> SECURE PLATFORM ACCESS</div><h1>Welcome back</h1><p>Sign in with your platform administrator account.</p></div><form onSubmit={submit}><label className="login-label">Email address<div className="login-input"><Mail size={16}/><input required type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} placeholder="admin@yourplatform.com"/></div></label><label className="login-label">Password<div className="login-input"><LockKeyhole size={16}/><input required type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password"/></div></label>{error&&<div className="login-error" role="alert">{error}</div>}<button className="primary-button login-submit" disabled={busy}>{busy?'Signing in…':'Sign in'}{!busy&&<ArrowRight size={15}/>}</button></form><div className="login-foot"><ShieldCheck size={14}/> Your session is protected with short-lived access tokens.</div></div><div className="login-copyright">© 2026 Manam Platform · Tamil Nadu matrimony network</div></main>
}
