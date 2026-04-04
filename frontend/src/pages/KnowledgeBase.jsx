import React, { useState } from 'react';
import { BookOpen, UploadCloud } from 'lucide-react';

const KnowledgeBase = () => {
  const [file, setFile] = useState(null);

  const handleUpload = () => {
    if (file) {
      alert(`Simulating upload for ${file.name}. This would be sent to /api/knowledge/upload and ingested via RAG.`);
      setFile(null);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <BookOpen size={32} color="var(--accent-purple)" /> Knowledge Base
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '3rem', maxWidth: '800px', lineHeight: '1.6' }}>
        Upload trading books, strategy PDFs, or customized logic texts. These documents dictate standard principles that the system will adhere strictly to. 
        Once uploaded, our Vector Engine parses the context ensuring Deepseek references these rules before trading decisions.
      </p>

      <div className="glass-card" style={{ padding: '4rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', borderStyle: 'dashed' }}>
        <UploadCloud size={64} color="var(--text-secondary)" style={{ marginBottom: '2rem' }} />
        
        <input 
          type="file" 
          id="file-upload" 
          accept=".pdf,.txt"
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files[0])}
        />
        
        <label htmlFor="file-upload" className="btn btn-primary" style={{ marginBottom: '1rem', display: 'inline-block', cursor: 'pointer' }}>
          Select File (.pdf, .txt)
        </label>
        
        {file && (
          <div style={{ marginTop: '1rem', color: 'var(--accent-green)', fontWeight: 'bold' }}>
            Selected: {file.name}
          </div>
        )}

        <button 
          className="btn" 
          onClick={handleUpload} 
          disabled={!file}
          style={{ marginTop: '2rem', opacity: file ? 1 : 0.5 }}
        >
          Inject to RAG Vector DB
        </button>
      </div>
    </div>
  );
};

export default KnowledgeBase;
