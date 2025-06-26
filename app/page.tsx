'use client';
import React, { useState } from 'react';
import styles from './page.module.css';
import axios from 'axios';

const API_BASE = '/api/shorten';

export default function Home() {
  const [longUrl, setLongUrl] = useState('');
  const [shortUrl, setShortUrl] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setShortUrl('');
    try {
      const res = await axios.post(API_BASE, { longUrl });
      setShortUrl(res.data.shortUrl);
    } catch (err: any) {
      if (err.response && err.response.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Network error: Could not connect to server.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 style={{ marginBottom: 32 }}>URL Shortener</h1>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 500, margin: 'auto' }}>
          <input
            type="url"
            placeholder="Enter long URL"
            value={longUrl}
            onChange={e => setLongUrl(e.target.value)}
            required
            style={{ padding: 10, fontSize: 16 }}
          />
          <button type="submit" disabled={loading} style={{ padding: 12, fontSize: 16 }}>
            {loading ? 'Shortening...' : 'Shorten URL'}
          </button>
        </form>

        {shortUrl && (
          <div style={{ marginTop: 20 }}>
            <strong>Short URL: </strong>
            <a href={shortUrl} target="_blank" rel="noopener noreferrer">{shortUrl}</a>
          </div>
        )}

        {error && <div style={{ color: 'red', marginTop: 16 }}>{error}</div>}
      </main>

      <footer className={styles.footer}>
        <p style={{ fontSize: 14, color: '#888' }}>© {new Date().getFullYear()} URL Shortener App</p>
      </footer>
    </div>
  );
}
