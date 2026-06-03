import { useState, useEffect, useCallback, useRef } from 'react'
import VoyageMap from './components/VoyageMap'
import Dashboard from './components/Dashboard'

const API_BASE = '/api'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeRoute, setActiveRoute] = useState('b')
  const [showRouteA, setShowRouteA] = useState(true)
  const [showRouteB, setShowRouteB] = useState(true)
  const mapAnchorRef = useRef(null)
  const [params, setParams] = useState({
    commanded_speed: 12,
    laycan_start: '2026-09-19',
    laycan_end: '2026-09-20',
    bunker_price: 600,
    departure_time: '2026-08-22',
  })

  const runAnalysis = useCallback(async () => {
    setLoading(true)
    setError(null)
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 45000)
    try {
      const res = await fetch(`${API_BASE}/voyage/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
        signal: controller.signal,
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const result = await res.json()
      setData(result)
      setActiveRoute(result.recommendation.route_id.includes('alt') ? 'b' : 'a')
    } catch (e) {
      if (e.name === 'AbortError') {
        setError('Analysis timed out — check that the backend is running on port 8000')
      } else {
        setError(e.message)
      }
    } finally {
      clearTimeout(timeoutId)
      setLoading(false)
    }
  }, [params])

  useEffect(() => {
    runAnalysis()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-ocean-900">
      <VoyageMap
        routeA={data?.route_a}
        routeB={data?.route_b}
        activeRoute={activeRoute}
        anchorRef={mapAnchorRef}
        showRouteA={showRouteA}
        showRouteB={showRouteB}
      />
      <header className="border-b border-slate-800 bg-ocean-800/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">⚓ Voyage Optimizer</h1>
            <p className="text-xs text-slate-400">Weather-Aware Routing & Laycan Risk Management</p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> Low</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" /> Medium</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> High</span>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-4">
        <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4 mb-4">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Route</label>
              <select className="bg-ocean-900 border border-slate-600 rounded px-3 py-2 text-sm text-white" disabled>
                <option>Rotterdam → Singapore</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Commanded Speed (kn)</label>
              <input
                type="number"
                value={params.commanded_speed}
                onChange={(e) => setParams({ ...params, commanded_speed: +e.target.value })}
                className="bg-ocean-900 border border-slate-600 rounded px-3 py-2 text-sm text-white w-24"
                min={1}
                max={25}
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Laycan Start</label>
              <input
                type="date"
                value={params.laycan_start}
                onChange={(e) => setParams({ ...params, laycan_start: e.target.value })}
                className="bg-ocean-900 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Laycan End</label>
              <input
                type="date"
                value={params.laycan_end}
                onChange={(e) => setParams({ ...params, laycan_end: e.target.value })}
                className="bg-ocean-900 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Bunker Price ($/MT)</label>
              <input
                type="number"
                value={params.bunker_price}
                onChange={(e) => setParams({ ...params, bunker_price: +e.target.value })}
                className="bg-ocean-900 border border-slate-600 rounded px-3 py-2 text-sm text-white w-28"
              />
            </div>
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium transition"
            >
              {loading ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-3 mb-4 text-red-400 text-sm">
            {error} — Make sure the backend is running on port 8000.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-700 overflow-hidden h-[500px] lg:h-[700px] relative">
            <div className="relative z-20 bg-ocean-800 px-3 py-2 flex flex-wrap items-center gap-2 border-b border-slate-700">
              <button
                onClick={() => setActiveRoute('a')}
                className={`text-xs px-3 py-1 rounded ${activeRoute === 'a' ? 'bg-blue-600 text-white' : 'bg-ocean-900 text-slate-400'}`}
              >
                Route A — Shortest
              </button>
              <button
                onClick={() => setActiveRoute('b')}
                className={`text-xs px-3 py-1 rounded ${activeRoute === 'b' ? 'bg-green-600 text-white' : 'bg-ocean-900 text-slate-400'}`}
              >
                Route B — Avoidance
              </button>
              <div className="flex items-center gap-3 ml-auto text-xs text-slate-400">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showRouteA}
                    onChange={(e) => setShowRouteA(e.target.checked)}
                    className="rounded border-slate-600"
                  />
                  <span className="text-blue-400">Route A</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showRouteB}
                    onChange={(e) => setShowRouteB(e.target.checked)}
                    className="rounded border-slate-600"
                  />
                  <span className="text-green-400">Route B</span>
                </label>
              </div>
            </div>
            <div ref={mapAnchorRef} className="h-[calc(100%-36px)]" />
          </div>

          <div className="lg:max-h-[700px] lg:overflow-y-auto">
            <Dashboard data={data} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  )
}
