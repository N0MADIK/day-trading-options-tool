import React, { useState, useEffect } from 'react'
import { API_BASE } from '../config'
import StrategyManager from './StrategyManager'

function TradeTracker({ onClose }) {
    const [stats, setStats] = useState(null)
    const [trades, setTrades] = useState([])
    const [notifications, setNotifications] = useState([])
    const [filter, setFilter] = useState('OPEN') // OPEN, CLOSED
    const [showStrategies, setShowStrategies] = useState(false)

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 30000) // Refresh every 30s
        return () => clearInterval(interval)
    }, [filter])

    const fetchData = async () => {
        try {
            // 1. Fetch Stats
            const statsRes = await fetch(`${API_BASE}/api/trades/stats`)
            if (statsRes.ok) setStats(await statsRes.json())

            // 2. Fetch Trades
            const statusParam = filter === 'ALL' ? '' : `?status=${filter}`
            const tradesRes = await fetch(`${API_BASE}/api/trades${statusParam}`)
            if (tradesRes.ok) {
                const data = await tradesRes.json()
                setTrades(data.trades || [])
            }

            // 3. Fetch Notifications
            const notifRes = await fetch(`${API_BASE}/api/notifications`)
            if (notifRes.ok) {
                const data = await notifRes.json()
                setNotifications(data.notifications || [])
            }
        } catch (e) {
            console.error('Error fetching tracker data:', e)
        }
    }

    const handleCloseTrade = async (tradeId, currentPrice) => {
        // Prompt for exit price if not provided (though usually we'd pass it)
        const exitPrice = prompt('Enter exit price:', currentPrice)
        if (!exitPrice) return

        try {
            const res = await fetch(`${API_BASE}/api/trades/${tradeId}/close`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exit_price: parseFloat(exitPrice) })
            })

            if (res.ok) {
                fetchData()
            } else {
                alert('Failed to close trade')
            }
        } catch (e) {
            alert('Error closing trade')
        }
    }

    const handleDeleteTrade = async (tradeId) => {
        if (!confirm('Delete this trade record?')) return
        try {
            await fetch(`${API_BASE}/api/trades/${tradeId}`, { method: 'DELETE' })
            fetchData()
        } catch (e) { console.error(e) }
    }

    const handleClearNotifications = async () => {
        try {
            await fetch(`${API_BASE}/api/notifications`, { method: 'DELETE' })
            setNotifications([])
        } catch (e) { console.error(e) }
    }

    return (
        <div className="trade-tracker">
            <div className="tracker-header">
                <h1>Trade Tracker</h1>
                <div className="tracker-actions">
                    <button className="btn btn-secondary" onClick={() => setShowStrategies(true)}>
                        Strategies
                    </button>
                    <button className="close-btn" onClick={onClose}>
                        &times;
                    </button>
                </div>
            </div>

            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="stat-title">Win Rate</span>
                        <span className="stat-value">{stats.win_rate}%</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-title">Total P&L</span>
                        <span className={`stat-value ${stats.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                            {stats.total_pnl >= 0 ? '+' : '-'}${Math.abs(stats.total_pnl).toFixed(2)}
                        </span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-title">Active Trades</span>
                        <span className="stat-value">{stats.open_trades}</span>
                    </div>
                    <div className="stat-card">
                        <span className="stat-title">Wins / Losses</span>
                        <span className="stat-value">{stats.wins}W / {stats.losses}L</span>
                    </div>
                </div>
            )}

            <div className="tracker-content">
                <div className="trades-section">
                    <div className="section-header">
                        <h2>Trades</h2>
                        <div className="filter-tabs">
                            <button className={`btn ${filter === 'OPEN' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('OPEN')} style={{ marginRight: '5px' }}>Open</button>
                            <button className={`btn ${filter === 'CLOSED_WIN' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('CLOSED_WIN')} style={{ marginRight: '5px' }}>Wins</button>
                            <button className={`btn ${filter === 'CLOSED_LOSS' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('CLOSED_LOSS')}>Losses</button>
                        </div>
                    </div>

                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Strategy</th>
                                <th>Entry</th>
                                <th>Current / Exit</th>
                                <th>Stop / Target</th>
                                <th>P&L</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.length === 0 && (
                                <tr><td colSpan="7" style={{ textAlign: 'center' }}>No trades found</td></tr>
                            )}
                            {trades.map(trade => (
                                <tr key={trade.id}>
                                    <td>
                                        <div className="ticker-symbol">{trade.ticker}</div>
                                        <div className="trade-contract-symbol">{trade.contract_symbol}</div>
                                    </td>
                                    <td>{trade.strategy_name || '-'}</td>
                                    <td>
                                        ${trade.fill_price?.toFixed(2)}
                                        <div style={{ fontSize: '0.8rem', color: '#888' }}>{new Date(trade.entry_date).toLocaleDateString()}</div>
                                    </td>
                                    <td>
                                        {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : (
                                            <span style={{ color: '#aaa' }}>Live...</span>
                                        )}
                                    </td>
                                    <td>
                                        <div style={{ color: '#f44336' }}>SL: ${trade.stop_loss}</div>
                                        <div style={{ color: '#4caf50' }}>TP: ${trade.take_profit}</div>
                                    </td>
                                    <td>
                                        {trade.pnl !== null ? (
                                            <span className={trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                                {trade.pnl >= 0 ? '+' : '-'}${Math.abs(trade.pnl).toFixed(2)}
                                            </span>
                                        ) : '-'}
                                    </td>
                                    <td>
                                        {trade.status === 'OPEN' && (
                                            <button className="btn btn-primary" style={{ padding: '4px 8px', fontSize: '0.8rem', marginRight: '5px' }} onClick={() => handleCloseTrade(trade.id, trade.fill_price)}>Close</button>
                                        )}
                                        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem' }} onClick={() => handleDeleteTrade(trade.id)}>Del</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="notifications-section">
                    <div className="section-header">
                        <h2>Notifications</h2>
                        <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '4px 8px' }} onClick={handleClearNotifications}>Clear</button>
                    </div>
                    <div className="notifications-list">
                        {notifications.length === 0 && <div style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>No notifications</div>}
                        {notifications.map(n => (
                            <div key={n.id} className={`notification-item ${!n.read ? 'unread' : ''}`}>
                                <div className="notif-header">
                                    <span className="notif-ticker">{n.ticker}</span>
                                    <span className="notif-time">{new Date(n.timestamp).toLocaleTimeString()}</span>
                                </div>
                                <div className="notif-msg">
                                    {n.status === 'CLOSED_WIN' ? 'Take Profit Hit' : 'Stop Loss Hit'}
                                    <div style={{ fontWeight: 'bold', color: n.pnl >= 0 ? '#4caf50' : '#f44336' }}>
                                        {n.pnl >= 0 ? '+' : '-'}${Math.abs(n.pnl).toFixed(2)}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {showStrategies && (
                <StrategyManager onClose={() => setShowStrategies(false)} />
            )}
        </div>
    )
}

export default TradeTracker
