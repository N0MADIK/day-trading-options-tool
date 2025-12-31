import React, { useState, useEffect } from 'react'
import { API_BASE } from '../config'

/**
 * Personal Finance Overview Page
 * 
 * Displays:
 * - Net worth total
 * - Custodian cards with accounts and values
 * - Connection status and last sync time
 * - Actions: Sync, Manage connection
 */
const ConnectionModal = ({ isOpen, onClose, onRefresh, initialTab = 'robinhood' }) => {
    const [activeTab, setActiveTab] = useState(initialTab)
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        apiKey: '',
        privateKey: '',
        plaidClientId: '',
        plaidSecret: ''
    })

    // Reset tab when modal opens with a specific initialTab
    useEffect(() => {
        if (isOpen && initialTab) {
            setActiveTab(initialTab)
        }
    }, [isOpen, initialTab])

    if (!isOpen) return null

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)

        try {
            if (activeTab === 'snaptrade') {
                // Special flow for SnapTrade
                const res = await fetch(`${API_BASE}/api/finance/snaptrade/link`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                const data = await res.json()

                if (res.ok && data.link_url) {
                    window.open(data.link_url, '_blank')
                    alert('A new tab has been opened to connect your brokerage accounts via SnapTrade.\n\nAfter you complete the connection process, click "Refresh" here to update your data.')
                    // We don't close the modal immediately, or we do and trigger a refresh?
                    // Better to let user trigger refresh.
                    onRefresh()
                    onClose()
                } else {
                    alert('Failed to generate connection link: ' + (data.detail || 'Unknown error'))
                }
                return
            }

            let institutionKey = ''
            let authData = {}

            if (activeTab === 'robinhood') {
                institutionKey = 'robinhood_crypto'
                authData = {
                    api_key: formData.apiKey,
                    private_key: formData.privateKey
                }
            } else if (activeTab === 'fidelity') {
                institutionKey = 'fidelity'
            } else if (activeTab === 'vanguard') {
                institutionKey = 'vanguard'
            }

            const res = await fetch(`${API_BASE}/api/finance/connections`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    institution_brand_key: institutionKey,
                    auth_data: authData
                })
            })

            const data = await res.json()

            if (res.ok) {
                alert('Connection established successfully!')
                onRefresh()
                onClose()
            } else {
                alert(`Connection failed: ${data.detail || 'Unknown error'}`)
            }
        } catch (err) {
            console.error(err)
            alert('Error connecting: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="modal-overlay" style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 1000
        }}>
            <div className="modal-content" style={{
                backgroundColor: '#1e1e1e', padding: '24px', borderRadius: '8px',
                width: '500px', maxWidth: '90%', color: 'white', border: '1px solid #333'
            }}>
                <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                    <h2>Connect Institution</h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '20px' }}>×</button>
                </div>

                <div className="tabs" style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid #333' }}>
                    {['robinhood', 'snaptrade', 'fidelity', 'vanguard'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            style={{
                                background: 'none', border: 'none',
                                borderBottom: activeTab === tab ? '2px solid #2196F3' : 'none',
                                color: activeTab === tab ? '#2196F3' : '#888',
                                padding: '8px 16px', cursor: 'pointer', textTransform: 'capitalize'
                            }}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                <form onSubmit={handleSubmit}>
                    {activeTab === 'robinhood' && (
                        <div className="form-group">
                            <p style={{ fontSize: '0.9em', color: '#ccc', marginBottom: '15px' }}>
                                Enter your Robinhood Crypto API credentials.
                                The Private Key is the Ed25519 secret key you generated.
                            </p>
                            <label style={{ display: 'block', marginBottom: '8px' }}>API Key</label>
                            <input
                                type="text"
                                value={formData.apiKey}
                                onChange={e => setFormData({ ...formData, apiKey: e.target.value })}
                                style={{ width: '100%', padding: '8px', marginBottom: '16px', background: '#333', border: '1px solid #444', color: 'white' }}
                                required
                            />
                            <label style={{ display: 'block', marginBottom: '8px' }}>Private Key (Secret)</label>
                            <input
                                type="password"
                                value={formData.privateKey}
                                onChange={e => setFormData({ ...formData, privateKey: e.target.value })}
                                style={{ width: '100%', padding: '8px', marginBottom: '16px', background: '#333', border: '1px solid #444', color: 'white' }}
                                required
                            />
                        </div>
                    )}

                    {activeTab === 'snaptrade' && (
                        <div className="form-group">
                            <p style={{ fontSize: '0.9em', color: '#ccc', marginBottom: '15px' }}>
                                Connect your brokerage accounts securely via SnapTrade.
                                Supports Robinhood, Schwab, Fidelity, TD Ameritrade, and more.
                            </p>
                            <div className="info-box" style={{ padding: '15px', background: '#2a2a2a', borderRadius: '4px', marginBottom: '15px' }}>
                                <strong>How it works:</strong>
                                <ol style={{ marginLeft: '20px', marginTop: '10px', color: '#aaa', fontSize: '0.9em' }}>
                                    <li>Click "Connect" below to open the secure connection portal.</li>
                                    <li>Select your brokerage and log in.</li>
                                    <li>Return here and your accounts will be synced automatically.</li>
                                </ol>
                            </div>
                        </div>
                    )}

                    {(activeTab === 'fidelity' || activeTab === 'vanguard') && (
                        <div className="form-group">
                            <p style={{ fontSize: '0.9em', color: '#ccc', marginBottom: '15px' }}>
                                Create a connection for {activeTab === 'fidelity' ? 'Fidelity' : 'Vanguard'} to enable file imports.
                                After creating the connection, you can upload OFX/CSV files directly from the dashboard.
                            </p>
                        </div>
                    )}

                    <div className="form-actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                        <button type="button" onClick={onClose} style={{ padding: '10px 20px', background: 'transparent', border: '1px solid #444', color: 'white', cursor: 'pointer', borderRadius: '4px' }}>
                            Cancel
                        </button>
                        <button type="submit" disabled={loading} style={{ padding: '10px 20px', background: '#2196F3', border: 'none', color: 'white', cursor: loading ? 'default' : 'pointer', borderRadius: '4px', opacity: loading ? 0.7 : 1 }}>
                            {loading ? 'Connecting...' : 'Connect'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

function PersonalFinanceOverview({ onClose, onNavigateToConnections }) {
    const [overview, setOverview] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [syncing, setSyncing] = useState({}) // Track syncing state per connection
    const [showConnectionModal, setShowConnectionModal] = useState(false)
    const [modalInitialTab, setModalInitialTab] = useState('robinhood')

    // Fetch overview data on mount
    useEffect(() => {
        fetchOverview()
    }, [])

    const fetchOverview = async () => {
        setLoading(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE}/api/overview`)
            if (!res.ok) {
                throw new Error('Failed to fetch overview')
            }
            const data = await res.json()
            setOverview(data)
        } catch (err) {
            setError(err.message || 'Error loading personal finance data')
        } finally {
            setLoading(false)
        }
    }

    const handleSync = async (connectionId) => {
        setSyncing(prev => ({ ...prev, [connectionId]: true }))
        try {
            const res = await fetch(`${API_BASE}/api/connections/${connectionId}/sync`, {
                method: 'POST'
            })
            if (res.ok) {
                // Refresh the overview after sync
                await fetchOverview()
            }
        } catch (err) {
            console.error('Sync failed:', err)
        } finally {
            setSyncing(prev => ({ ...prev, [connectionId]: false }))
        }
    }

    const formatCurrency = (value, currency = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(value)
    }

    const formatRelativeTime = (isoString) => {
        if (!isoString) return 'Never'
        const date = new Date(isoString)
        const now = new Date()
        const diffMs = now - date
        const diffMins = Math.floor(diffMs / 60000)
        const diffHours = Math.floor(diffMins / 60)
        const diffDays = Math.floor(diffHours / 24)

        if (diffMins < 1) return 'Just now'
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
        return date.toLocaleDateString()
    }

    const getStatusClass = (status) => {
        switch (status) {
            case 'ACTIVE': return 'status-active'
            case 'NEEDS_REAUTH': return 'status-warning'
            case 'ERROR': return 'status-error'
            case 'DISABLED': return 'status-disabled'
            default: return ''
        }
    }

    const getStatusLabel = (status) => {
        switch (status) {
            case 'ACTIVE': return 'Active'
            case 'NEEDS_REAUTH': return 'Needs Re-auth'
            case 'ERROR': return 'Error'
            case 'DISABLED': return 'Disabled'
            default: return status
        }
    }

    const getSourceTypeLabel = (sourceType) => {
        switch (sourceType) {
            case 'AGGREGATOR': return 'Linked'
            case 'ROBINHOOD_CRYPTO': return 'Crypto'
            case 'FILE_IMPORT': return 'File Import'
            default: return sourceType
        }
    }

    // Loading state
    if (loading) {
        return (
            <div className="finance-overview">
                <div className="finance-header">
                    <button className="back-btn" onClick={onClose}>← Back</button>
                    <h1>Personal Finance Overview</h1>
                </div>
                <div className="loading">
                    <div className="spinner"></div>
                    Loading your finances...
                </div>
            </div>
        )
    }

    const handleReauth = (custodian) => {
        setShowConnectionModal(true)
    }

    const handleFileUpload = async (connectionId, event) => {
        const file = event.target.files[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)

        setSyncing(prev => ({ ...prev, [connectionId]: true }))
        try {
            const res = await fetch(`${API_BASE}/api/finance/connections/${connectionId}/upload`, {
                method: 'POST',
                body: formData
            })

            if (res.ok) {
                // Refresh overview
                await fetchOverview()
            } else {
                const err = await res.json()
                alert(`Upload failed: ${err.detail || 'Unknown error'}`)
            }
        } catch (err) {
            console.error('Upload failed:', err)
            alert('Upload failed: ' + err.message)
        } finally {
            setSyncing(prev => ({ ...prev, [connectionId]: false }))
            // Reset file input
            event.target.value = ''
        }
    }

    // Error state
    if (error) {
        return (
            <div className="finance-overview">
                <div className="finance-header">
                    <button className="back-btn" onClick={onClose}>← Back</button>
                    <h1>Personal Finance Overview</h1>
                </div>
                <div className="error-state">
                    <div className="error-icon">⚠️</div>
                    <h3>Unable to load data</h3>
                    <p>{error}</p>
                    <button className="retry-btn" onClick={fetchOverview}>Try Again</button>
                </div>
            </div>
        )
    }

    // Empty state (no custodians)
    if (!overview?.custodians?.length) {
        return (
            <div className="finance-overview">
                <div className="finance-header">
                    <button className="back-btn" onClick={onClose}>← Back</button>
                    <h1>Personal Finance Overview</h1>
                </div>
                <div className="empty-state finance-empty">
                    <div className="empty-icon">💰</div>
                    <h2>No accounts connected</h2>
                    <p>Connect your financial accounts to see your complete picture</p>
                    <button
                        className="primary-btn"
                        onClick={() => {
                            setModalInitialTab('snaptrade')
                            setShowConnectionModal(true)
                        }}
                    >
                        Connect SnapTrade (Vanguard, Robinhood, etc.)
                    </button>
                </div>
            </div>
        )
    }

    // Populated state
    return (
        <div className="finance-overview">
            <ConnectionModal
                isOpen={showConnectionModal}
                onClose={() => setShowConnectionModal(false)}
                onRefresh={fetchOverview}
                initialTab={modalInitialTab}
            />

            <div className="finance-header">
                <button className="back-btn" onClick={onClose}>← Back</button>
                <h1>Personal Finance Overview</h1>
                <div className="header-actions">
                    <button
                        className="manage-btn"
                        style={{ backgroundColor: '#2196F3', color: 'white', marginRight: '10px' }}
                        onClick={() => {
                            setModalInitialTab('snaptrade')
                            setShowConnectionModal(true)
                        }}
                    >
                        Connect to SnapTrade
                    </button>
                    <button className="manage-btn" onClick={() => {
                        setModalInitialTab('robinhood')
                        setShowConnectionModal(true)
                    }}>
                        Manage Connections
                    </button>
                    <button className="refresh-btn" onClick={fetchOverview} disabled={loading}>
                        ↻ Refresh
                    </button>
                </div>
            </div>

            {/* Net Worth Card */}
            <div className="net-worth-card">
                <div className="net-worth-label">Net Worth</div>
                <div className="net-worth-value">
                    {formatCurrency(overview.netWorthTotal?.value || 0, overview.netWorthTotal?.currency)}
                </div>
                <div className="net-worth-asof">
                    As of {new Date(overview.asOf).toLocaleString()}
                </div>
            </div>

            {/* Custodian Cards */}
            <div className="custodians-grid">
                {overview.custodians.map(custodian => (
                    <div
                        key={custodian.institutionId}
                        className={`custodian-card ${custodian.connection?.status === 'NEEDS_REAUTH' || custodian.connection?.status === 'ERROR' ? 'has-warning' : ''}`}
                    >
                        <div className="custodian-header">
                            <div className="custodian-info">
                                <h3 className="custodian-name">{custodian.institutionName}</h3>
                                <div className="custodian-badges">
                                    <span className="source-type-badge">{getSourceTypeLabel(custodian.sourceType)}</span>
                                    <div className={`status-badge ${getStatusClass(custodian.connection?.status)}`}>
                                        {getStatusLabel(custodian.connection?.status)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Error message if exists */}
                        {custodian.connection?.lastErrorMessage && (
                            <div className="connection-error">
                                {custodian.connection.lastErrorMessage}
                            </div>
                        )}

                        <div className="custodian-sync-info">
                            Last Sync: {formatRelativeTime(custodian.connection?.lastSyncedAt)}
                        </div>

                        <div className="custodian-total">
                            <span className="total-label">Total</span>
                            <span className="total-value">
                                {formatCurrency(custodian.totalValue?.value || 0, custodian.totalValue?.currency)}
                            </span>
                        </div>

                        {/* Accounts List */}
                        <div className="accounts-list">
                            {custodian.accounts.map(account => (
                                <div key={account.accountId} className="account-item">
                                    <div className="account-info">
                                        <span className="account-name">{account.accountName}</span>
                                        <span className="account-type-badge">{account.accountSubtype || account.accountType}</span>
                                    </div>
                                    <span className="account-value">
                                        {formatCurrency(account.value?.value || 0, account.value?.currency)}
                                    </span>
                                </div>
                            ))}
                        </div>

                        {/* Actions */}
                        <div className="custodian-actions">
                            {custodian.connection?.status === 'NEEDS_REAUTH' ? (
                                <button
                                    className="action-btn reauth-btn"
                                    onClick={() => handleReauth(custodian)}
                                >
                                    Re-authenticate
                                </button>
                            ) : (
                                <>
                                    {custodian.sourceType === 'FILE_IMPORT' ? (
                                        <div className="file-upload-wrapper">
                                            <input
                                                type="file"
                                                id={`file-upload-${custodian.connection?.connectionId}`}
                                                className="file-input"
                                                accept=".ofx,.qfx,.csv"
                                                onChange={(e) => handleFileUpload(custodian.connection?.connectionId, e)}
                                                disabled={syncing[custodian.connection?.connectionId]}
                                                style={{ display: 'none' }}
                                            />
                                            <label
                                                htmlFor={`file-upload-${custodian.connection?.connectionId}`}
                                                className="action-btn upload-btn"
                                                style={{ cursor: syncing[custodian.connection?.connectionId] ? 'default' : 'pointer' }}
                                            >
                                                {syncing[custodian.connection?.connectionId] ? 'Importing...' : 'Upload File'}
                                            </label>
                                        </div>
                                    ) : (
                                        <button
                                            className="action-btn sync-btn"
                                            onClick={() => handleSync(custodian.connection?.connectionId)}
                                            disabled={syncing[custodian.connection?.connectionId]}
                                        >
                                            {syncing[custodian.connection?.connectionId] ? 'Syncing...' : 'Sync Now'}
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default PersonalFinanceOverview
