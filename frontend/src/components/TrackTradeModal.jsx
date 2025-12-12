import React, { useState, useEffect } from 'react'
import { API_BASE } from '../config'

function TrackTradeModal({ option, onClose, onTradeCreated }) {
    const [strategies, setStrategies] = useState([])
    const [selectedStrategyId, setSelectedStrategyId] = useState('')
    const [loading, setLoading] = useState(false)

    const [formData, setFormData] = useState({
        entry_price: option.lastPrice || 0,
        quantity: 1,
        stop_loss: 0,
        take_profit: 0,
        notes: '',
        notifications_enabled: true
    })

    // Calculate stats
    const risk = formData.entry_price - formData.stop_loss
    const reward = formData.take_profit - formData.entry_price
    const rrRatio = risk > 0 ? (reward / risk).toFixed(2) : 0

    useEffect(() => {
        fetchStrategies()
        // Set initial SL/TP placeholders
        setFormData(prev => ({
            ...prev,
            stop_loss: Number((prev.entry_price * 0.8).toFixed(2)),
            take_profit: Number((prev.entry_price * 1.5).toFixed(2))
        }))
    }, [])

    const fetchStrategies = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/strategies`)
            if (res.ok) {
                const data = await res.json()
                setStrategies(data.strategies || [])
                if (data.strategies?.length > 0) {
                    setSelectedStrategyId(data.strategies[0].id)
                    applyStrategyDefaults(data.strategies[0])
                }
            }
        } catch (e) {
            console.error(e)
        }
    }

    const applyStrategyDefaults = (strategy) => {
        if (!strategy) return
        const slPrice = option.lastPrice * (1 - strategy.default_stop_loss_pct)
        const tpPrice = option.lastPrice * (1 + strategy.default_take_profit_pct)

        setFormData(prev => ({
            ...prev,
            stop_loss: Number(slPrice.toFixed(2)),
            take_profit: Number(tpPrice.toFixed(2)),
            notifications_enabled: strategy.notifications_enabled
        }))
    }

    const handleStrategyChange = (e) => {
        const id = Number(e.target.value)
        setSelectedStrategyId(id)
        const strategy = strategies.find(s => s.id === id)
        applyStrategyDefaults(strategy)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)

        try {
            const payload = {
                contract_symbol: option.contractSymbol,
                ticker: option.ticker || option.symbol, // Handle both object formats
                entry_price: parseFloat(formData.entry_price),
                fill_price: parseFloat(formData.entry_price), // Simulating fill at entry
                quantity: parseInt(formData.quantity),
                stop_loss: parseFloat(formData.stop_loss),
                take_profit: parseFloat(formData.take_profit),
                strategy_id: selectedStrategyId ? parseInt(selectedStrategyId) : null,
                notifications_enabled: formData.notifications_enabled,
                notes: formData.notes
            }

            const res = await fetch(`${API_BASE}/api/trades`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                if (onTradeCreated) onTradeCreated()
                onClose()
            } else {
                const err = await res.json()
                alert(err.detail || 'Failed to create trade')
            }
        } catch (e) {
            alert('Error creating trade')
        } finally {
            setLoading(false)
        }
    }

    const applyQuickSL = (pct) => {
        const price = formData.entry_price * (1 - pct)
        setFormData(prev => ({ ...prev, stop_loss: Number(price.toFixed(2)) }))
    }

    const applyQuickTP = (pct) => {
        const price = formData.entry_price * (1 + pct)
        setFormData(prev => ({ ...prev, take_profit: Number(price.toFixed(2)) }))
    }

    return (
        <div className="track-trade-overlay" onClick={onClose}>
            <div className="track-trade-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Track Trade</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <form className="track-trade-content" onSubmit={handleSubmit}>
                    <div className="trade-summary">
                        <div>
                            <div className="trade-ticker">{option.ticker || option.symbol}</div>
                            <div className="trade-contract">{option.contractSymbol}</div>
                        </div>
                        <div className="trade-price">
                            L: ${option.lastPrice}
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Strategy</label>
                        <select
                            value={selectedStrategyId}
                            onChange={handleStrategyChange}
                            disabled={strategies.length === 0}
                        >
                            {strategies.length === 0 && <option>No strategies found</option>}
                            {strategies.map(s => (
                                <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Entry Price</label>
                            <input
                                type="number"
                                step="0.01"
                                value={formData.entry_price}
                                onChange={e => setFormData({ ...formData, entry_price: parseFloat(e.target.value) })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Quantity</label>
                            <input
                                type="number"
                                min="1"
                                value={formData.quantity}
                                onChange={e => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Stop Loss ($)</label>
                            <input
                                type="number"
                                step="0.01"
                                value={formData.stop_loss}
                                onChange={e => setFormData({ ...formData, stop_loss: parseFloat(e.target.value) })}
                                required
                            />
                            <div className="quick-actions">
                                <button type="button" className="quick-btn" onClick={() => applyQuickSL(0.10)}>-10%</button>
                                <button type="button" className="quick-btn" onClick={() => applyQuickSL(0.20)}>-20%</button>
                                <button type="button" className="quick-btn" onClick={() => applyQuickSL(0.50)}>-50%</button>
                            </div>
                        </div>
                        <div className="form-group">
                            <label>Take Profit ($)</label>
                            <input
                                type="number"
                                step="0.01"
                                value={formData.take_profit}
                                onChange={e => setFormData({ ...formData, take_profit: parseFloat(e.target.value) })}
                                required
                            />
                            <div className="quick-actions">
                                <button type="button" className="quick-btn" onClick={() => applyQuickTP(0.20)}>+20%</button>
                                <button type="button" className="quick-btn" onClick={() => applyQuickTP(0.50)}>+50%</button>
                                <button type="button" className="quick-btn" onClick={() => applyQuickTP(1.00)}>+100%</button>
                            </div>
                        </div>
                    </div>

                    <div className="risk-reward-display">
                        <div className="rr-item">
                            <span className="rr-label">Risk</span>
                            <span className="rr-value risk">${(risk * formData.quantity * 100).toFixed(0)}</span>
                        </div>
                        <div className="rr-item">
                            <span className="rr-label">Reward</span>
                            <span className="rr-value reward">${(reward * formData.quantity * 100).toFixed(0)}</span>
                        </div>
                        <div className="rr-item">
                            <span className="rr-label">R:R Ratio</span>
                            <span className="rr-value ratio">{rrRatio}</span>
                        </div>
                    </div>

                    <div className="form-group" style={{ marginTop: '15px' }}>
                        <label>Notes</label>
                        <textarea
                            value={formData.notes}
                            onChange={e => setFormData({ ...formData, notes: e.target.value })}
                            placeholder="Thesis for this trade..."
                        />
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                            {loading ? 'Tracking...' : 'Start Tracking'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default TrackTradeModal
