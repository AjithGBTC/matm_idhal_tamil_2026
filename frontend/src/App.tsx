import { FormEvent, useEffect, useMemo, useState } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Activity, ArrowRight, ArrowUpRight, ChevronDown, ChevronLeft, ChevronRight, HelpCircle, Command, CreditCard, FileText, Gem, LayoutDashboard, LifeBuoy, LogOut, Menu, Plus, Search, Settings2, ShieldCheck, Users, X } from 'lucide-react'
import { apiError, createTenant, getOverview, getPlans, getTenants, Plan, PlatformOverview, setAuthTokens, signOut, Tenant } from './api'
import Login from './Login'

const nav = [
  { label: 'OVERVIEW', items: [{ name: 'Dashboard', icon: LayoutDashboard, path: '/' }, { name: 'Analytics', icon: Activity, path: '/analytics' }] },
  { label: 'SAAS MANAGEMENT', items: [{ name: 'Tenants', icon: Users, path: '/tenants' }, { name: 'Subscriptions', icon: CreditCard, path: '/subscriptions' }, { name: 'Plans & pricing', icon: Gem, path: '/plans' }, { name: 'Billing & invoices', icon: FileText, path: '/billing' }] },
  { label: 'PLATFORM', items: [{ name: 'Admin team', icon: ShieldCheck, path: '/team' }, { name: 'Settings', icon: Settings2, path: '/settings' }] },
]

function initials(name: string) { return name.split(/\s+/).slice(0, 2).map(part => part[0] ?? '').join('').toUpperCase() }
function currency(paise: number | null | undefined) { return paise == null ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(paise / 100) }
const avatarColors = ['rose', 'sage', 'gold', 'blue']

function App() {
  const [token, setToken] = useState<string | null>(null)
  const [overview, setOverview] = useState<PlatformOverview | null>(null)
  const [tenantPage, setTenantPage] = useState<{ items: Tenant[]; total: number; page: number; page_size: number } | null>(null)
  const [plans, setPlans] = useState<Plan[]>([])
  const [loadError, setLoadError] = useState('')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const location = useLocation()
  const selected = nav.flatMap(section => section.items).find(item => item.path === location.pathname)
  const title = selected?.name ?? 'Dashboard'

  useEffect(() => {
    if (!token) return
    let alive = true
    const timeout = window.setTimeout(() => {
      Promise.all([getOverview(token), getTenants(token, search, page)])
        .then(([nextOverview, nextTenants]) => {
          if (!alive) return
          setOverview(nextOverview)
          setTenantPage(nextTenants)
          setLoadError('')
        })
        .catch(reason => { if (alive) setLoadError(apiError(reason)) })
    }, 180)
    return () => { alive = false; window.clearTimeout(timeout) }
  }, [token, search, page])

  useEffect(() => {
    if (!token || (!showCreate && location.pathname !== '/plans')) return
    getPlans(token).then(setPlans).catch(reason => setLoadError(apiError(reason)))
  }, [token, showCreate, location.pathname])

  const metrics = useMemo(() => {
    const data = overview?.tenants
    return [
      { label: 'Total tenants', value: data ? data.total.toLocaleString('en-IN') : '—', note: `${data?.active ?? '—'} active`, icon: Users, tone: 'pink' },
      { label: 'Active subscriptions', value: overview?.active_subscriptions.toLocaleString('en-IN') ?? '—', note: 'Current platform total', icon: CreditCard, tone: 'green' },
      { label: 'Monthly recurring revenue', value: currency(overview?.monthly_recurring_revenue_paise), note: 'Billing data not connected', icon: ArrowUpRight, tone: 'violet' },
      { label: 'Pending approvals', value: data?.pending.toLocaleString('en-IN') ?? '—', note: 'Tenants awaiting review', icon: ShieldCheck, tone: 'amber' },
    ]
  }, [overview])

  if (!token) return <Login onLogin={tokens => { setAuthTokens(tokens); setToken(tokens.access_token) }} />

  async function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    const form = new FormData(event.currentTarget)
    const body = {
      business_name: String(form.get('business_name') ?? '').trim(),
      owner_name: String(form.get('owner_name') ?? '').trim(),
      email: String(form.get('email') ?? '').trim(),
      mobile: String(form.get('mobile') ?? '').trim(),
      district: String(form.get('district') ?? '').trim(),
      plan_id: Number(form.get('plan_id')),
      initial_password: String(form.get('initial_password') ?? ''),
    }
    try {
      await createTenant(token, body)
      setShowCreate(false)
      setSearch('')
      setPage(1)
      const [nextOverview, nextTenants] = await Promise.all([getOverview(token), getTenants(token, '', 1)])
      setOverview(nextOverview)
      setTenantPage(nextTenants)
      setLoadError('')
    } catch (reason) { setLoadError(apiError(reason)) }
  }

  const tenantRows = tenantPage?.items ?? []
  const totalPages = Math.max(1, Math.ceil((tenantPage?.total ?? 0) / (tenantPage?.page_size ?? 6)))
  const planDistribution = overview?.plan_distribution ?? []
  const maxPlanCount = Math.max(1, ...planDistribution.map(item => item.subscriptions))

  return <div className="app-shell">
    {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close menu"/>}
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><span>ம</span><i/></div>{!collapsed && <div className="brand-copy"><b>manam<span>.</span></b><small>PLATFORM ADMIN</small></div>}<button className="mobile-close icon-btn" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18}/></button></div>
      <div className="workspace-switch"><div className="workspace-symbol"><Command size={15}/></div>{!collapsed && <><span><b>Manam Platform</b><small>Super Admin</small></span><ChevronDown size={15} className="muted-icon"/></>}</div>
      <div className="nav-sections">{nav.map(section => <section key={section.label}><div className="nav-label">{!collapsed && section.label}</div>{section.items.map(item => { const Icon = item.icon; return <NavLink key={item.name} to={item.path} title={collapsed ? item.name : undefined} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={17} strokeWidth={1.8}/>{!collapsed && <span>{item.name}</span>}</NavLink> })}</section>)}</div>
      <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><HelpCircle size={17}/></div>{!collapsed && <div><b>Need a hand?</b><span>Visit our help center</span></div>}{!collapsed && <ArrowRight size={15}/>}</div><div className="profile-row"><div className="avatar admin-avatar">SA</div>{!collapsed && <><span className="profile-text"><b>Platform Admin</b><small>Super Administrator</small></span><button className="icon-btn logout-btn" title="Sign out" onClick={async()=>{await signOut().catch(()=>undefined);setToken(null)}}><LogOut size={15}/></button></>}</div></div>
      <button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">{collapsed ? <ChevronRight size={16}/> : <ChevronLeft size={16}/>}{!collapsed && 'Collapse sidebar'}</button>
    </aside>
    <main className="main-area"><header className="topbar"><div className="top-left"><button className="mobile-menu icon-btn" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={20}/></button><div className="breadcrumbs"><span>Platform</span><ChevronRight size={13}/><b>{title}</b></div></div><div className="top-actions"><label className="global-search"><Search size={16}/><input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} placeholder="Search tenants..."/><kbd>⌘ K</kbd></label><span className={`connection-indicator ${loadError?'connection-error':''}`} title={loadError?'API request failed':overview?'Connected to the platform API':'Connecting to the platform API'}><i/></span></div></header>
      <div className="page-content"><Routes>
        <Route path="/" element={<>
          <div className="page-heading"><div><div className="eyebrow"><span className="live-dot"/> PLATFORM OVERVIEW</div><h1>Platform overview <span>✳</span></h1><p>Current tenant and subscription activity across the Manam network.</p></div><button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={16}/> Add new tenant</button></div>
          <div className="date-toolbar"><div className="date-copy"><span className="date-dot"/>{overview ? `Data updated ${new Date(overview.generated_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}` : 'Loading platform data'}<span className="date-divider">·</span> Live platform data</div><span className="read-only-tag">SUPER ADMIN</span></div>
          {loadError&&<div className="api-alert" role="alert">{loadError}</div>}
          <section className="metrics-grid">{metrics.map(({label,value,note,icon:Icon,tone}) => <article className="metric-card" key={label}><div className="metric-top"><span>{label}</span><div className={`metric-icon ${tone}`}><Icon size={17} strokeWidth={1.8}/></div></div><div className="metric-value">{value}</div><div className="metric-bottom"><span className="metric-note">{note}</span></div></article>)}</section>
          <section className="insights-grid"><article className="panel revenue-panel"><div className="panel-heading"><div><div className="panel-title">Revenue overview</div><div className="panel-subtitle">Revenue reporting will appear when billing is configured</div></div></div><div className="revenue-empty"><div className="revenue-empty-icon"><CreditCard size={19}/></div><b>Billing data is not connected yet</b><span>No payment records are available for this platform.</span></div></article>
            <article className="panel plan-panel"><div className="panel-heading"><div><div className="panel-title">Subscription plans</div><div className="panel-subtitle">Active and trial tenant distribution</div></div><Gem size={16} className="muted-icon"/></div><div className="plan-total"><b>{overview?.active_subscriptions ?? '—'}</b><span>active subscriptions</span></div><div className="plan-bars">{planDistribution.length ? planDistribution.map((item,index)=><div className="bar-row" key={item.plan}><span>{item.plan}</span><div className="bar-track"><i className={`bar-${['rose','coral','gold','sage'][index%4]}`} style={{width:`${item.subscriptions ? Math.max(5,item.subscriptions/maxPlanCount*100) : 0}%`}}/></div><b>{item.subscriptions}</b></div>) : <div className="no-plan-data">No plan subscriptions yet</div>}</div><NavLink className="text-link" to="/plans">View plans <ArrowRight size={14}/></NavLink></article></section>
          <TenantTable rows={tenantRows} total={tenantPage?.total ?? 0} page={page} pages={totalPages} search={search} setSearch={setSearch} setPage={setPage} onCreate={()=>setShowCreate(true)} />
          <footer className="page-footer"><span>© 2026 Manam Platform</span><span><i className="footer-status"/> API connected</span><a href="mailto:support@manam.in">Need help? <LifeBuoy size={13}/></a></footer>
        </>}/>
        <Route path="/tenants" element={<><div className="page-heading"><div><div className="eyebrow">SAAS MANAGEMENT</div><h1>Tenant accounts</h1><p>Manage matrimony businesses on the platform.</p></div><button className="primary-button" onClick={()=>setShowCreate(true)}><Plus size={16}/> Add new tenant</button></div>{loadError&&<div className="api-alert" role="alert">{loadError}</div>}<TenantTable rows={tenantRows} total={tenantPage?.total ?? 0} page={page} pages={totalPages} search={search} setSearch={setSearch} setPage={setPage} onCreate={()=>setShowCreate(true)}/></>}/>
        <Route path="/plans" element={<><div className="page-heading"><div><div className="eyebrow">SAAS MANAGEMENT</div><h1>Plans & pricing</h1><p>Platform subscription catalog.</p></div></div>{loadError&&<div className="api-alert" role="alert">{loadError}</div>}<section className="plan-cards">{plans.map(plan=><article className="panel plan-card" key={plan.id}><div className="panel-title">{plan.name}</div><div className="plan-price">{currency(plan.monthly_price_paise)}<small> / month</small></div><p>{plan.trial_days} day trial · Up to {plan.max_users.toLocaleString()} members</p><div className="plan-limit">{plan.max_staff} staff seats <span>·</span> {plan.max_agents} agents</div><span className={`status-tag ${plan.is_active?'active':'trial'}`}><i/>{plan.is_active?'Available':'Disabled'}</span></article>)}</section></>}/>
        <Route path="*" element={<div className="panel phase-placeholder"><div className="metric-icon pink"><Settings2 size={17}/></div><h2>{title}</h2><p>This module is scheduled in the next implementation phase.</p></div>}/>
      </Routes></div>
    </main>
    {showCreate&&<div className="modal-backdrop" onClick={()=>setShowCreate(false)}><form className="modal" onClick={e=>e.stopPropagation()} onSubmit={submitTenant}><div className="modal-head"><div><div className="eyebrow">SAAS MANAGEMENT</div><h2>Add a tenant</h2></div><button type="button" className="icon-btn" onClick={()=>setShowCreate(false)} aria-label="Close"><X size={18}/></button></div><p className="modal-copy">Create a matrimony workspace and its first tenant administrator.</p><div className="form-grid"><label className="form-label">Business name <span>*</span><input name="business_name" required minLength={2} maxLength={180} placeholder="e.g. Chennai Matrimony"/></label><label className="form-label">Owner name <span>*</span><input name="owner_name" required minLength={2} maxLength={160} placeholder="Business owner"/></label><label className="form-label">Owner email <span>*</span><input name="email" required type="email" placeholder="owner@business.com"/></label><label className="form-label">Mobile number <span>*</span><input name="mobile" required minLength={7} maxLength={24} placeholder="+91 98765 43210"/></label><label className="form-label">District <span>*</span><input name="district" required placeholder="e.g. Chennai"/></label><label className="form-label">Subscription plan <span>*</span><select name="plan_id" required defaultValue=""><option value="" disabled>Choose a plan</option>{plans.filter(plan=>plan.is_active).map(plan=><option key={plan.id} value={plan.id}>{plan.name}</option>)}</select></label><label className="form-label form-wide">Temporary admin password <span>*</span><input name="initial_password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" placeholder="At least 12 characters"/></label></div><div className="modal-note"><ShieldCheck size={15}/> The tenant is created as pending approval. Password is hashed before storage.</div>{loadError&&<div className="form-error" role="alert">{loadError}</div>}<div className="modal-actions"><button type="button" className="outline-button" onClick={()=>setShowCreate(false)}>Cancel</button><button type="submit" className="primary-button">Create tenant <ArrowRight size={15}/></button></div></form></div>}
  </div>
}

function TenantTable({ rows, total, page, pages, search, setSearch, setPage, onCreate }: { rows: Tenant[]; total: number; page: number; pages: number; search: string; setSearch: (value:string)=>void; setPage: (value:number)=>void; onCreate:()=>void }) {
  return <section className="panel tenants-panel"><div className="table-heading"><div><div className="panel-title">Tenant accounts <span className="count-pill">{total}</span></div><div className="panel-subtitle">Tenant records stored on the platform</div></div><button className="view-all" onClick={onCreate}><Plus size={14}/> Add tenant</button></div><div className="table-tools"><label className="table-search"><Search size={15}/><input value={search} onChange={e=>{setSearch(e.target.value);setPage(1)}} placeholder="Search tenants..."/></label><div className="table-tool-spacer"/><span className="rows-label">{total ? `Showing ${(page-1)*6+1}–${Math.min(page*6,total)} of ${total}` : 'No tenants yet'}</span></div><div className="table-scroll"><table><thead><tr><th>BUSINESS NAME</th><th>PLAN</th><th>MEMBERS</th><th>STATUS</th><th>MONTHLY PRICE</th></tr></thead><tbody>{rows.map((tenant,index)=><tr key={tenant.id}><td><div className="tenant-cell"><div className={`tenant-avatar ${avatarColors[index%avatarColors.length]}`}>{initials(tenant.business_name)}</div><div><b>{tenant.business_name}</b><small>{tenant.district}, Tamil Nadu</small></div></div></td><td>{tenant.plan_name?<span className={`plan-tag ${tenant.plan_name.toLowerCase()}`}>{tenant.plan_name}</span>:'—'}</td><td className="users-cell">—</td><td><span className={`status-tag ${tenant.status==='active'?'active':'trial'}`}><i/>{tenant.status}</span></td><td className="billing-cell">{currency(tenant.monthly_price_paise)}</td></tr>)}</tbody></table>{rows.length===0&&<div className="empty-state">{search?`No tenants match “${search}”.`:'No tenant accounts have been created.'}</div>}</div><div className="table-pagination"><span>Page <b>{page}</b> of <b>{pages}</b></span><div><button aria-label="Previous page" disabled={page<=1} onClick={()=>setPage(page-1)}><ChevronLeft size={15}/></button><button className="page-active">{page}</button><button aria-label="Next page" disabled={page>=pages} onClick={()=>setPage(page+1)}><ChevronRight size={15}/></button></div></div></section>
}

export default App
