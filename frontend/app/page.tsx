// Auto-generated - Edits to this file will be merged with a `cruft update`

"use client"; // This is a client component

import { useEffect, useState } from 'react';
import { fetchAPIInfo } from '../utils/api';

export default function Home() {
  const [backend, setBackend] = useState(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const fetchedBackend = await fetchAPIInfo();
        setBackend(fetchedBackend);
      } catch (error) {
        // Convert error to string for React rendering
        const errorMessage = error instanceof Error ? error.message : String(error);
        setError(errorMessage);
      }
    }
    loadData();
  }, []);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!backend) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>This is a NextJS frontend with a {backend} backend</h1>
    </div>
  );
}