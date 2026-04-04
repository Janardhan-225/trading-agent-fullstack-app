import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';

const Dashboard = () => {
  const [wallet, setWallet] = useState(0);
  const [activePositions, setActivePositions] = useState(0);
  
  useEffect(() => {
    // query backend:
    axios.get('http://localhost:8000/api/portfolio/wallet').then(res => setWallet(res.data.balance)).catch(e => setWallet(10000));
    axios.get('http://localhost:8000/api/portfolio/assets').then(res => setActivePositions(res.data.length)).catch(e => setActivePositions(0));
  }, []);

  return (
    <div>
      <h1 style={{ marginBottom: '2rem' }}>Portfolio Overview</h1>
      
      <div className="dashboard-grid">
        <div className="glass-card">
          <div className="dashboard-stat-title">Available Cash</div>
          <div className="dashboard-stat-value" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={28} className="positive" />
            {wallet.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="glass-card">
          <div className="dashboard-stat-title">Portfolio Net Worth</div>
          <div className="dashboard-stat-value" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={28} className="positive" />
            {(wallet + 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="glass-card">
          <div className="dashboard-stat-title">Active Positions</div>
          <div className="dashboard-stat-value">
            {activePositions}
          </div>
        </div>
      </div>

      <h2 style={{ marginBottom: '1.5rem', marginTop: '2rem' }}>Recent AI Decisions</h2>
      <div className="glass-card">
        <p style={{ color: 'var(--text-secondary)' }}>No recent executions. The background loop operates every 20-30 minutes.</p>
      </div>
    </div>
  );
};

export default Dashboard;
