import { useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { ChatDrawer } from './components/ChatDrawer'
import { ConnectionBanner } from './components/ConnectionBanner'
import { RailNav } from './components/RailNav'
import { StatusBar } from './components/StatusBar'
import { TopBar } from './components/TopBar'
import { useAttention } from './hooks/useAttention'
import { useBrainState } from './hooks/useBrainState'
import { useChat } from './hooks/useChat'
import { useConnection } from './hooks/useConnection'
import { useContextData } from './hooks/useContextData'
import { useEvents } from './hooks/useEvents'
import { useIdentity } from './hooks/useIdentity'
import { useModels } from './hooks/useModels'
import { usePreview } from './hooks/usePreview'
import { CameraPage } from './pages/CameraPage'
import { CognitionPage } from './pages/CognitionPage'
import { EventsPage } from './pages/EventsPage'
import { KnowledgePage } from './pages/KnowledgePage'
import { MemoryPage } from './pages/MemoryPage'
import { OverviewPage } from './pages/OverviewPage'
import { PerceptionPage } from './pages/PerceptionPage'


function initialTheme(): string {
  const stored = document.documentElement.getAttribute('data-theme')
  return stored ?? localStorage.getItem('novi-theme') ?? 'dark'
}

function shortRunId(runId?: string): string | null {
  return runId ? runId.slice(0, 8) : null
}

export default function App() {
  const [theme, setTheme] = useState(initialTheme)
  const [chatOpen, setChatOpen] = useState(true)
  const [navOpen, setNavOpen] = useState(false)

  const { connected, reportConnection } = useConnection()
  // Page-local polling (plan 02, Phase 4): each feature polls only while a
  // page that displays it is active. Shared chrome (TopBar/StatusBar) consumes
  // brain state + identity on every page, so those stay global — each still a
  // single producer. Preview (300ms base64) is the biggest win: it runs only
  // on the three pages that render the frame.
  const { pathname } = useLocation()
  const onPreviewPage = pathname === '/camera' || pathname === '/perception'
  const onEventsPage = pathname === '/events' || pathname === '/overview'
  const onAttentionPage = pathname === '/overview' || pathname === '/cognition'
  const onContextPage = pathname === '/cognition'
  const brain = useBrainState(reportConnection)
  const { models, current, setModel } = useModels(reportConnection)
  const chat = useChat(reportConnection, () => current ?? 'model', { enabled: chatOpen })
  const preview = usePreview(reportConnection, { enabled: onPreviewPage })
  const events = useEvents(reportConnection, { enabled: onEventsPage })
  const attention = useAttention(reportConnection, { enabled: onAttentionPage })
  const contextData = useContextData(reportConnection, { enabled: onContextPage })
  const identity = useIdentity(reportConnection)

  const state = brain.state

  const applyTheme = (next: string) => {
    document.documentElement.setAttribute('data-theme', next)
    try {
      localStorage.setItem('novi-theme', next)
    } catch {
      /* private mode — theme just won't persist */
    }
    setTheme(next)
  }

  const handleModelChange = async (name: string) => {
    try {
      await setModel(name)
      chat.notice('switched model → ' + name)
    } catch {
      chat.notice('model switch failed — is the server reachable?')
    }
  }

  const afterAction = () => {
    void brain.refresh()
    void attention.refresh()
    void contextData.refresh()
  }

  const cur = identity.detail?.current
  const identityLabel = !cur
    ? 'no person'
    : (cur.name || cur.person || 'someone') + (cur.tier ? ` (${cur.tier})` : '')

  return (
    <>
      <TopBar
        runId={shortRunId(state?.run_id)}
        cycle={state?.cycle ?? null}
        health={state?.health?.status ?? null}
        identity={identityLabel}
        theme={theme}
        onThemeChange={applyTheme}
        models={models}
        model={current}
        onModelChange={(m) => void handleModelChange(m)}
        chatOpen={chatOpen}
        onToggleChat={() => setChatOpen((v) => !v)}
        onToggleNav={() => setNavOpen((v) => !v)}
        navOpen={navOpen}
      />
      <ConnectionBanner show={!connected} />
      <div className="shell">
        <RailNav open={navOpen} onNavigate={() => setNavOpen(false)} />
        <main className="pages">
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route
              path="/overview"
              element={
                <OverviewPage
                  state={state}
                  confHist={brain.confHist}
                  memHist={brain.memHist}
                  evHist={events.evHist}
                  attention={attention.snapshot}
                />
              }
            />
            <Route
              path="/cognition"
              element={
                <CognitionPage
                  state={state}
                  attention={attention.snapshot}
                  context={contextData.response}
                  onAction={afterAction}
                />
              }
            />
            <Route path="/memory" element={<MemoryPage state={state} />} />
            <Route path="/knowledge" element={<KnowledgePage state={state} />} />
            <Route
              path="/perception"
              element={
                <PerceptionPage
                  reportConnection={reportConnection}
                  frame={preview.frame}
                  showImage={preview.showImage}
                  identity={identity.detail}
                />
              }
            />
            <Route path="/events" element={<EventsPage events={events.events} />} />
            <Route
              path="/camera"
              element={
                <CameraPage
                  reportConnection={reportConnection}
                  frame={preview.frame}
                  showImage={preview.showImage}
                />
              }
            />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Routes>
        </main>
        <ChatDrawer
          open={chatOpen}
          onCollapse={() => setChatOpen(false)}
          turns={chat.turns}
          streaming={chat.streaming}
          onSend={(text, confidence) => void chat.send(text, confidence)}
          onListen={() => void chat.listen()}
          onStep={() => void chat.step()}
          onClear={() => void chat.clear()}
          isStreaming={chat.isStreaming}
        />
      </div>
      <StatusBar
        connected={connected}
        lastUpdatedAt={brain.lastUpdatedAt || null}
        runId={shortRunId(state?.run_id)}
        cycle={state?.cycle ?? null}
        memCount={state?.memory?.active ?? null}
        theme={theme}
      />
    </>
  )
}
