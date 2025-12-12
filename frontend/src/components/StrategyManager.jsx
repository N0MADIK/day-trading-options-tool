import React, { useState, useEffect } from 'react'
import { API_BASE } from '../config'

function StrategyManager({ onClose, onSelectStrategy }) {
    const [strategies, setStrategies] = useState([])
    const [loading, setLoading] = useState(false)
    const [selectedId, setSelectedId] = useState(null)
    const [isEditing, setIsEditing] = useState(false)

    // Form State
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        default_stop_loss_pct: 0.20,
        default_take_profit_pct: 0.50,
        notifications_enabled: true
    })

    useEffect(() => {
        fetchStrategies()
    }, [])

    const fetchStrategies = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE}/api/strategies`)
            if (res.ok) {
                const data = await res.json()
                setStrategies(data.strategies || [])
            }
        } catch (e) {
            console.error('Failed to fetch strategies', e)
        } finally {
            setLoading(false)
        }
    }

    const handleSelect = (strategy) => {
        setSelectedId(strategy.id)
        setFormData({
            name: strategy.name,
            description: strategy.description || '',
            default_stop_loss_pct: strategy.default_stop_loss_pct,
            default_take_profit_pct: strategy.default_take_profit_pct,
            notifications_enabled: strategy.notifications_enabled
        })
        setIsEditing(false)
    }

    const handleNew = () => {
        setSelectedId(null)
        setFormData({
            name: 'New Strategy',
            description: '',
            default_stop_loss_pct: 0.20,
            default_take_profit_pct: 0.50,
            notifications_enabled: true
        })
        setIsEditing(true)
    }

    const handleSave = async (e) => {
        e.preventDefault()
        setLoading(true)

        try {
            const url = selectedId
                ? `${API_BASE}/api/strategies/${selectedId}`
                : `${API_BASE}/api/strategies`

            const method = selectedId ? 'PUT' : 'POST'

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })

            if (res.ok) {
                await fetchStrategies()
                setIsEditing(false)
                if (!selectedId) {
                    // Select the newly created one (simplified)
                    const data = await res.json()
                    if (data.id) setSelectedId(data.id)
                }
            } else {
                const err = await res.json()
                alert(err.detail || 'Failed to save context')
            }
        } catch (e) {
            alert('Error saving strategy')
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        if (!selectedId || !confirm('Are you sure you want to delete this strategy?')) return

        setLoading(true)
        try {
            const res = await fetch(`${API_BASE}/api/strategies/${selectedId}`, {
                method: 'DELETE'
            })

            if (res.ok) {
                await fetchStrategies()
                handleNew()
            }
        } catch (e) {
            alert('Error deleting strategy')
        } finally {
            setLoading(false)
        }
    }

    const handleUseStrategy = () => {
        if (selectedId && onSelectStrategy) {
            const strategy = strategies.find(s => s.id === selectedId)
            onSelectStrategy(strategy)
            onClose()
        }
    }

    return (
        <div className="strategy-manager-overlay" onClick={onClose}>
            <div className="strategy-manager-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Strategy Manager</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="modal-content">
                    <div className="strategies-list-sidebar">
                        <button className="new-strategy-btn" onClick={handleNew}>
                            + New Strategy
                        </button>
                        <div className="strategy-list">
                            {strategies.map(s => (
                                <div
                                    key={s.id}
                                    className={`strategy-item ${s.id === selectedId ? 'active' : ''}`}
                                    onClick={() => handleSelect(s)}
                                >
                                    <div className="strategy-item-name">{s.name}</div>
                                    <div className="strategy-item-desc">{s.description}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="strategy-editor">
                        {selectedId || isEditing ? (
                            <form onSubmit={handleSave}>
                                <div className="form-group">
                                    <label>Strategy Name</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={e => setFormData({ ...formData, description: e.target.value })}
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Default Stop Loss (%)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={formData.default_stop_loss_pct}
                                            onChange={e => setFormData({ ...formData, default_stop_loss_pct: parseFloat(e.target.value) })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Default Take Profit (%)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={formData.default_take_profit_pct}
                                            onChange={e => setFormData({ ...formData, default_take_profit_pct: parseFloat(e.target.value) })}
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="checkbox-group">
                                        <input
                                            type="checkbox"
                                            checked={formData.notifications_enabled}
                                            onChange={e => setFormData({ ...formData, notifications_enabled: e.target.checked })}
                                        />
                                        Enable Notifications
                                    </label>
                                </div>

                                <div className="form-actions">
                                    {selectedId && (
                                        <button type="button" className="btn btn-danger" onClick={handleDelete} style={{ marginRight: 'auto' }}>
                                            Delete
                                        </button>
                                    )}
                                    {onSelectStrategy && selectedId && (
                                        <button type="button" className="btn btn-secondary" onClick={handleUseStrategy}>
                                            Select Strategy
                                        </button>
                                    )}
                                    <button type="submit" className="btn btn-primary" disabled={loading}>
                                        {loading ? 'Saving...' : 'Save Strategy'}
                                    </button>
                                </div>
                            </form>
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
                                Select a strategy or create a new one
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default StrategyManager
