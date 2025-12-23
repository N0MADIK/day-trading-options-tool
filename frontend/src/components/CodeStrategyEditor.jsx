import React, { useState, useEffect } from 'react'
import { API_BASE } from '../config'

function CodeStrategyEditor({ onClose }) {
    const [strategies, setStrategies] = useState([])
    const [selectedId, setSelectedId] = useState(null)
    const [logs, setLogs] = useState([])

    // Editor State
    const [name, setName] = useState('')
    const [code, setCode] = useState('')
    const [scheduleType, setScheduleType] = useState('INTERVAL')
    const [scheduleValue, setScheduleValue] = useState('60')
    const [executionType, setExecutionType] = useState('HOST')
    const [isActive, setIsActive] = useState(false)

    const [loading, setLoading] = useState(false)
    const [executing, setExecuting] = useState(false)
    const [message, setMessage] = useState('')

    useEffect(() => {
        fetchStrategies()
    }, [])

    useEffect(() => {
        if (selectedId) {
            fetchStrategyDetails(selectedId)
            fetchLogs(selectedId)
        } else {
            resetForm()
        }
    }, [selectedId])

    const fetchStrategies = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/custom-strategies`)
            if (res.ok) {
                const data = await res.json()
                setStrategies(data.strategies || [])
            }
        } catch (e) {
            console.error(e)
        }
    }

    const fetchStrategyDetails = async (id) => {
        try {
            const res = await fetch(`${API_BASE}/api/custom-strategies/${id}`)
            if (res.ok) {
                const data = await res.json()
                setName(data.name)
                setCode(data.code || '')
                setScheduleType(data.schedule_type)
                setScheduleValue(data.schedule_value)
                setExecutionType(data.execution_type)
                setIsActive(data.is_active)
            }
        } catch (e) {
            console.error(e)
        }
    }

    const fetchLogs = async (id) => {
        try {
            const res = await fetch(`${API_BASE}/api/custom-strategies/${id}/logs`)
            if (res.ok) {
                const data = await res.json()
                setLogs(data.logs || [])
            }
        } catch (e) {
            console.error(e)
        }
    }

    const resetForm = () => {
        setName('')
        setCode('def run(context):\n    # Entry point for your strategy\n    # context.log("Checking signals...")\n    # price = context.market.get_price("SPY")\n    \n    return []')
        setScheduleType('INTERVAL')
        setScheduleValue('60')
        setExecutionType('HOST')
        setIsActive(false)
        setLogs([])
        setMessage('')
    }

    const handleSave = async () => {
        if (!name) return setMessage('Name required')
        setLoading(true)
        setMessage('')

        try {
            const payload = {
                name,
                code,
                schedule_type: scheduleType,
                schedule_value: scheduleValue,
                execution_type: executionType
            }

            let url = `${API_BASE}/api/custom-strategies`
            let method = 'POST'

            if (selectedId) {
                url = `${API_BASE}/api/custom-strategies/${selectedId}`
                method = 'PUT'
            }

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                const data = await res.json()
                setMessage(selectedId ? 'Updated successfully' : 'Created successfully')
                if (!selectedId && data.id) setSelectedId(data.id)
                fetchStrategies()
            } else {
                const err = await res.json()
                setMessage(`Error: ${err.detail}`)
            }
        } catch (e) {
            setMessage('Network error')
        } finally {
            setLoading(false)
        }
    }

    const handleToggle = async () => {
        if (!selectedId) return
        try {
            const res = await fetch(`${API_BASE}/api/custom-strategies/${selectedId}/toggle`, { method: 'POST' })
            if (res.ok) {
                const data = await res.json()
                setIsActive(data.active)
            }
        } catch (e) {
            console.error(e)
        }
    }

    const handleExecute = async () => {
        if (!selectedId) return
        setExecuting(true)
        try {
            // First save
            await handleSave()

            const res = await fetch(`${API_BASE}/api/custom-strategies/${selectedId}/execute`, { method: 'POST' })
            if (res.ok) {
                const result = await res.json()
                // Refresh logs
                fetchLogs(selectedId)
                alert(`Execution ${result.status}\nTrades: ${result.trades}`)
            }
        } catch (e) {
            alert('Execution failed')
        } finally {
            setExecuting(false)
        }
    }

    return (
        <div className="strategy-manager-overlay" style={{ zIndex: 1100 }}>
            <div className="strategy-manager-modal" style={{ maxWidth: '1200px', height: '90vh' }}>
                <div className="modal-header">
                    <h2>Python Strategy Editor</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="modal-content">
                    {/* Sidebar */}
                    <div className="strategies-list-sidebar">
                        <button className="new-strategy-btn" onClick={() => setSelectedId(null)}>
                            + New Script
                        </button>
                        <div className="strategy-list">
                            {strategies.map(s => (
                                <div
                                    key={s.id}
                                    className={`strategy-item ${selectedId === s.id ? 'active' : ''}`}
                                    onClick={() => setSelectedId(s.id)}
                                >
                                    <div className="strategy-item-name">{s.name}</div>
                                    <div className="strategy-item-desc" style={{ color: s.is_active ? '#4caf50' : '#888' }}>
                                        {s.is_active ? '● Active' : '○ Paused'} | {s.schedule_type}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Editor */}
                    <div className="strategy-editor" style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', gap: '0' }}>
                        {/* Config Bar */}
                        <div style={{ padding: '10px', background: '#1a1a1a', borderBottom: '1px solid #333', display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <input
                                placeholder="Strategy Name"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                style={{ background: '#333', border: '1px solid #444', color: 'white', padding: '6px', borderRadius: '4px', width: '200px' }}
                            />

                            <select
                                value={scheduleType}
                                onChange={e => setScheduleType(e.target.value)}
                                style={{ background: '#333', border: '1px solid #444', color: 'white', padding: '6px', borderRadius: '4px' }}
                            >
                                <option value="INTERVAL">Interval (min)</option>
                                <option value="CRON">Cron Expression</option>
                            </select>

                            <input
                                placeholder="Value (e.g. 60)"
                                value={scheduleValue}
                                onChange={e => setScheduleValue(e.target.value)}
                                style={{ background: '#333', border: '1px solid #444', color: 'white', padding: '6px', borderRadius: '4px', width: '100px' }}
                            />

                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <label style={{ color: '#aaa', fontSize: '12px' }}>Mode:</label>
                                <select
                                    value={executionType}
                                    onChange={e => setExecutionType(e.target.value)}
                                    style={{ background: '#333', border: '1px solid #444', color: 'white', padding: '6px', borderRadius: '4px' }}
                                >
                                    <option value="HOST">Host (Direct)</option>
                                    <option value="DOCKER">Docker (Isolate)</option>
                                </select>
                            </div>

                            <div style={{ marginLeft: 'auto', display: 'flex', gap: '10px' }}>
                                {selectedId && (
                                    <button
                                        onClick={handleToggle}
                                        style={{
                                            background: isActive ? '#4caf50' : '#333',
                                            color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'
                                        }}
                                    >
                                        {isActive ? 'ACTIVE' : 'PAUSED'}
                                    </button>
                                )}
                                <button
                                    onClick={handleSave}
                                    disabled={loading}
                                    className="btn btn-primary"
                                    style={{ fontSize: '12px' }}
                                >
                                    {loading ? 'Saving...' : 'Save'}
                                </button>
                                {selectedId && (
                                    <button
                                        onClick={handleExecute}
                                        disabled={executing}
                                        className="btn"
                                        style={{ background: '#ff9800', color: 'white', fontSize: '12px' }}
                                    >
                                        {executing ? 'Running...' : 'Run Now'}
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Code Area */}
                        <div style={{ flex: 1, position: 'relative' }}>
                            <textarea
                                value={code}
                                onChange={e => setCode(e.target.value)}
                                style={{
                                    width: '100%', height: '100%', resize: 'none',
                                    background: '#1e1e1e', color: '#d4d4d4', border: 'none', padding: '15px',
                                    fontFamily: '"Consolas", "Monaco", monospace', fontSize: '14px', lineHeight: '1.5'
                                }}
                                spellCheck="false"
                            />
                        </div>

                        {/* Logs Panel */}
                        <div style={{ height: '200px', background: '#000', borderTop: '1px solid #333', overflow: 'auto', padding: '10px' }}>
                            <div style={{ color: '#888', marginBottom: '5px', fontSize: '11px', textTransform: 'uppercase' }}>Console / Logs</div>
                            {logs.map((log, i) => (
                                <div key={i} style={{ fontFamily: 'monospace', fontSize: '12px', marginBottom: '4px', borderBottom: '1px solid #222', paddingBottom: '2px' }}>
                                    <span style={{ color: log.status === 'ERROR' ? '#f44336' : '#4caf50', marginRight: '8px' }}>[{log.status}]</span>
                                    <span style={{ color: '#666', marginRight: '8px' }}>{new Date(log.timestamp).toLocaleTimeString()}</span>
                                    <span style={{ color: '#ccc' }}>Traded: {log.trades_generated}</span>
                                    <pre style={{ margin: '4px 0 0 0', color: '#aaa', whiteSpace: 'pre-wrap' }}>{log.output}</pre>
                                </div>
                            ))}
                            {logs.length === 0 && <div style={{ color: '#444', fontStyle: 'italic' }}>No execution logs yet...</div>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default CodeStrategyEditor
