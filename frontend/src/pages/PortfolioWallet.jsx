import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Wallet as WalletIcon, ArrowDownCircle, ArrowUpCircle } from 'lucide-react';

const PortfolioWallet = () => {
  const [balance, setBalance] = useState(0);
  const [assets, setAssets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [amount, setAmount] = useState('');

  const fetchWallet = async () => {
    try {
      const res = await axios.get("http://localhost:8000/api/portfolio/wallet");
      setBalance(res.data.balance);
    } catch { }
  };

  const fetchAssets = async () => {
    try {
      const res = await axios.get("http://localhost:8000/api/portfolio/assets");
      setAssets(res.data);
    } catch { }
  };

  const fetchTransactions = async () => {
    try {
        const res = await axios.get("http://localhost:8000/api/portfolio/transactions");
        setTransactions(res.data);
    } catch {}
  };

  useEffect(() => {
    fetchWallet();
    fetchAssets();
    fetchTransactions();
  }, []);

  const handleTransaction = async (type) => {
    const val = parseFloat(amount);
    if (!isNaN(val) && val > 0) {
      if (type === 'deposit') {
          await axios.post(`http://localhost:8000/api/portfolio/wallet/deposit?amount=${val}`);
          fetchWallet();
      }
      if (type === 'withdraw' && val <= balance) {
          // Negative amount for withdraw
          await axios.post(`http://localhost:8000/api/portfolio/wallet/deposit?amount=-${val}`);
          fetchWallet();
      }
      setAmount('');
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: '2rem' }}>Portfolio Wallet</h1>
      
      <div className="dashboard-grid">
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1rem' }}>
          <WalletIcon size={48} color="var(--accent-blue)" style={{ marginBottom: '1rem' }} />
          <div style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Current Balance</div>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', fontFamily: 'var(--font-display)', marginTop: '0.5rem' }}>
            ${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '1.5rem' }}>Simulate Transactions</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
            Deposit or withdraw money to see how the Deepseek reasoning engine handles sudden liquidity changes. If drawing down forces liquidation, AI will decide what positions to trim.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <input 
              type="number" 
              placeholder="Amount ($)" 
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)',
                color: 'white', padding: '1rem', borderRadius: '8px', fontSize: '1.1rem'
              }}
            />
            
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.5rem', background: 'var(--accent-green)' }}
                onClick={() => handleTransaction('deposit')}
              >
                <ArrowUpCircle /> Deposit
              </button>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.5rem', background: 'var(--accent-red)' }}
                onClick={() => handleTransaction('withdraw')}
              >
                <ArrowDownCircle /> Withdraw
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <h2 style={{ marginTop: '3rem', marginBottom: '1.5rem' }}>Asset Holdings</h2>
      <div className="glass-card">
        <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-glass)' }}>
              <th style={{ padding: '1rem' }}>Symbol</th>
              <th style={{ padding: '1rem' }}>Shares</th>
              <th style={{ padding: '1rem' }}>Avg Price</th>
              <th style={{ padding: '1rem' }}>Total Value</th>
            </tr>
          </thead>
          <tbody>
            {assets.length === 0 ? (
                <tr>
                  <td style={{ padding: '1rem' }}colSpan="4" align="center" className="text-secondary">No assets currently held. Engine waiting for optimal conditions.</td>
                </tr>
            ) : (
                assets.map(asset => (
                    <tr key={asset.symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '1rem', fontWeight: 600 }}>{asset.symbol}</td>
                        <td style={{ padding: '1rem' }}>{asset.quantity.toFixed(4)}</td>
                        <td style={{ padding: '1rem' }}>${asset.average_price.toFixed(2)}</td>
                        <td style={{ padding: '1rem', color: 'var(--accent-green)' }}>${(asset.quantity * asset.average_price).toFixed(2)}</td>
                    </tr>
                ))
            )}
          </tbody>
        </table>
      </div>

    <h2 style={{ marginTop: '3rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
      Tactical AI Deployment
    </h2>
      <div className="glass-card" style={{ marginBottom: '3rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        
        {/* Strategic Auto-Invest */}
        <div style={{ background: 'rgba(0,255,100,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(0,255,100,0.1)' }}>
            <h3 style={{ marginTop: 0, color: 'var(--accent-green)' }}>Strategic Auto-Invest</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Force the Deepseek Engine to instantly allocate the requested capital exclusively to undervalued tracked stocks.
            </p>
            <div style={{ display: 'flex', gap: '1rem' }}>
                <input 
                    type="number" 
                    placeholder="E.g., 2000"
                    style={{ flex: 1, background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', color: 'white', padding: '0.8rem', borderRadius: '8px' }}
                    id="investAmt"
                />
                <button 
                    className="btn" 
                    style={{ background: 'var(--accent-green)', color: 'black', fontWeight: 'bold' }}
                    onClick={async () => {
                        const amt = document.getElementById('investAmt').value;
                        if(amt && amt > 0) {
                            try {
                                await axios.post(`http://localhost:8000/api/portfolio/strategic-invest?amount=${amt}`);
                                fetchWallet(); fetchAssets(); fetchTransactions();
                                document.getElementById('investAmt').value = '';
                                alert('Strategic Investment execution complete. Check Execution Ledger.');
                            } catch(e) { alert("Execution Failed. Check server."); }
                        }
                    }}
                >
                    Deploy Capital
                </button>
            </div>
        </div>

        {/* Strategic Auto-Withdraw */}
        <div style={{ background: 'rgba(255,80,80,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,80,80,0.1)' }}>
            <h3 style={{ marginTop: 0, color: 'var(--accent-red)' }}>Strategic Auto-Withdraw</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Force the AI to optimally liquidate specific open stock positions to explicitly free up the requested cash target.
            </p>
            <div style={{ display: 'flex', gap: '1rem' }}>
                <input 
                    type="number" 
                    placeholder="E.g., 1000"
                    style={{ flex: 1, background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', color: 'white', padding: '0.8rem', borderRadius: '8px' }}
                    id="withdrawAmt"
                />
                <button 
                    className="btn" 
                    style={{ background: 'var(--accent-red)', color: 'white', fontWeight: 'bold' }}
                    onClick={async () => {
                        const amt = document.getElementById('withdrawAmt').value;
                        if(amt && amt > 0) {
                            try {
                                await axios.post(`http://localhost:8000/api/portfolio/strategic-withdraw?amount=${amt}`);
                                fetchWallet(); fetchAssets(); fetchTransactions();
                                document.getElementById('withdrawAmt').value = '';
                                alert('Strategic Liquidation complete. Check Execution Ledger.');
                            } catch(e) { alert("Execution Failed. Check server."); }
                        }
                    }}
                >
                    Liquidate Assets
                </button>
            </div>
        </div>

      </div>
    </div>
  );
};

export default PortfolioWallet;
