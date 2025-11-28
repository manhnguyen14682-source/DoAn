import React, { useEffect, useState, useRef } from 'react'
import axios from 'axios'

export default function App() {
  const [data, setData] = useState({})
  const [history, setHistory] = useState([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    const protocolHttp = location.protocol === 'https:' ? 'https:' : 'http:'
    const API_BASE = import.meta.env.VITE_API_URL ?? `${protocolHttp}//${location.hostname}:8000`

    axios.get(`${API_BASE}/api/status`).then(res => setData(res.data)).catch(err => {
      console.error('Failed to fetch /api/status', err)
      setError('Failed to fetch initial status')
    })
    axios.get(`${API_BASE}/api/history`).then(res => setHistory(res.data)).catch(err => {
      console.error('Failed to fetch /api/history', err)
    })

    try {
      const apiUrl = new URL(API_BASE)
      const wsProtocol = apiUrl.protocol === 'https:' ? 'wss' : 'ws'
      const wsUrl = `${wsProtocol}://${apiUrl.host}/ws`
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('WS open')
      }
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          setData(prev => ({ ...prev, [msg.topic]: { value: msg.value, ts: msg.ts } }))
          setHistory(prev => [...prev.slice(-199), msg])
        } catch (e) {
          console.error('Invalid WS message', e)
        }
      }
      ws.onclose = () => setConnected(false)
      ws.onerror = (e) => {
        console.error('WS error', e)
        setConnected(false)
      }
    } catch (e) {
      console.error('Failed to open websocket', e)
      setError('WebSocket connection failed')
    }

    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const getValue = (topic, label) => {
    const entry = data[topic]
    if (!entry) return '--'
    return entry.value
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-4xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">Smart Irrigation Dashboard</h1>
          <div className={`px-3 py-1 rounded ${connected ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>{connected ? 'Connected' : 'Disconnected'}</div>
        </header>

        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 text-red-700">{error}</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card title="Temperature (°C)" value={getValue('V1')} />
          <Card title="Humidity (%)" value={getValue('V2')} />
          <Card title="Soil Moisture (analog)" value={getValue('V3')} />
          <Card title="Status" value={getValue('V4')} />
        </div>

        <section className="mt-6">
          <h2 className="text-lg font-medium mb-2">Recent messages</h2>
          <div className="bg-white shadow rounded">
            <table className="w-full table-auto text-sm">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="p-2 text-left">Time</th>
                  <th className="p-2 text-left">Topic</th>
                  <th className="p-2 text-left">Value</th>
                </tr>
              </thead>
              <tbody>
                {history.slice().reverse().map((m, i) => (
                  <tr key={i} className="border-t">
                    <td className="p-2 align-top">{m.ts ? new Date(m.ts * 1000).toLocaleString() : '-'}</td>
                    <td className="p-2 align-top">{m.topic}</td>
                    <td className="p-2 align-top">{m.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}

function Card({ title, value }) {
  return (
    <div className="bg-white p-4 rounded shadow">
      <div className="text-sm text-slate-500 mb-1">{title}</div>
      <div className="text-3xl font-semibold">{value}</div>
    </div>
  )
}
