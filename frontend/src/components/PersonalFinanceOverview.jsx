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
function PersonalFinanceOverview({ onClose, onNavigateToConnections }) {
    const [overview, setOverview] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [syncing, setSyncing] = useState({}) // Track syncing state per connection

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

    // Mock Data for Preview
    const MOCK_OVERVIEW_DATA = {
        netWorthTotal: { value: 125430.50, currency: 'USD' },
        asOf: new Date().toISOString(),
        custodians: [
            {
                institutionId: 'inst_fidelity_01',
                institutionName: 'Fidelity (Preview)',
                sourceType: 'FILE_IMPORT',
                totalValue: { value: 85200.00, currency: 'USD' },
                connection: {
                    connectionId: 'conn_fidelity_01',
                    status: 'ACTIVE',
                    lastSyncedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
                    lastErrorMessage: null
                },
                accounts: [
                    {
                        accountId: 'acc_fid_01',
                        accountName: 'Individual Brokerage',
                        accountType: 'BROKERAGE',
                        accountSubtype: 'TAXABLE',
                        value: { value: 45200.00, currency: 'USD' }
                    },
                    {
                        accountId: 'acc_fid_02',
                        accountName: 'Roth IRA',
                        accountType: 'RETIREMENT',
                        accountSubtype: 'ROTH_IRA',
                        value: { value: 40000.00, currency: 'USD' }
                    }
                ]
            },
            {
                institutionId: 'inst_robinhood_01',
                institutionName: 'Robinhood Crypto (Preview)',
                sourceType: 'ROBINHOOD_CRYPTO',
                totalValue: { value: 15230.50, currency: 'USD' },
                connection: {
                    connectionId: 'conn_rh_01',
                    status: 'ACTIVE',
                    lastSyncedAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 mins ago
                    lastErrorMessage: null
                },
                accounts: [
                    {
                        accountId: 'acc_rh_crypto',
                        accountName: 'Crypto Holdings',
                        accountType: 'CRYPTO',
                        accountSubtype: 'CRYPTO',
                        value: { value: 15230.50, currency: 'USD' }
                    }
                ]
            },
            {
                institutionId: 'inst_vanguard_01',
                institutionName: 'Vanguard (Preview)',
                sourceType: 'FILE_IMPORT',
                totalValue: { value: 25000.00, currency: 'USD' },
                connection: {
                    connectionId: 'conn_van_01',
                    status: 'NEEDS_REAUTH',
                    lastSyncedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(), // 7 days ago
                    lastErrorMessage: 'Session expired'
                },
                accounts: [
                    {
                        accountId: 'acc_van_01',
                        accountName: 'Traditional IRA',
                        accountType: 'RETIREMENT',
                        accountSubtype: 'TRAD_IRA',
                        value: { value: 25000.00, currency: 'USD' }
                    }
                ]
            }
        ]
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
                    <div className="error-actions" style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                        <button className="retry-btn" onClick={fetchOverview}>Try Again</button>
                        <button
                            className="mock-btn"
                            style={{
                                padding: '8px 16px',
                                background: '#2196F3',
                                border: 'none',
                                borderRadius: '4px',
                                color: 'white',
                                cursor: 'pointer'
                            }}
                            onClick={() => {
                                setOverview(MOCK_OVERVIEW_DATA)
                                setError(null)
                            }}
                        >
                            Mock Preview
                        </button>
                    </div>
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
                        onClick={onNavigateToConnections}
                    >
                        Add Connection
                    </button>
                </div>
            </div>
        )
    }

    // Populated state
    return (
        <div className="finance-overview">
            <div className="finance-header">
                <button className="back-btn" onClick={onClose}>← Back</button>
                <h1>Personal Finance Overview</h1>
                <button className="refresh-btn" onClick={fetchOverview} disabled={loading}>
                    ↻ Refresh
                </button>
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
                                <span className="source-type-badge">{getSourceTypeLabel(custodian.sourceType)}</span>
                            </div>
                            <div className={`status-badge ${getStatusClass(custodian.connection?.status)}`}>
                                {getStatusLabel(custodian.connection?.status)}
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
                                    onClick={onNavigateToConnections}
                                >
                                    Re-authenticate
                                </button>
                            ) : (
                                <button
                                    className="action-btn sync-btn"
                                    onClick={() => handleSync(custodian.connection?.connectionId)}
                                    disabled={syncing[custodian.connection?.connectionId]}
                                >
                                    {syncing[custodian.connection?.connectionId] ? 'Syncing...' : 'Sync Now'}
                                </button>
                            )}
                            <button
                                className="action-btn manage-btn"
                                onClick={onNavigateToConnections}
                            >
                                Manage
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default PersonalFinanceOverview
