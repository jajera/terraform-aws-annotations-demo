import { useState } from 'react';
import FilterBar from './components/FilterBar';
import DemoDescription from './components/DemoDescription';
import ImageGrid from './components/ImageGrid';
import LoadingSkeleton from './components/LoadingSkeleton';
import ResultsBar from './components/ResultsBar';
import ThemeToggle from './components/ThemeToggle';
import { useTheme } from './hooks/useTheme';

const PAGE_SIZE = 24;

async function fetchImages(filters, { offset = 0, limit = PAGE_SIZE } = {}) {
  const params = new URLSearchParams();
  if (filters.day_phase) params.set('day_phase', filters.day_phase);
  if (filters.utc_day) params.set('utc_day', filters.utc_day);
  if (filters.visibility) params.set('visibility', filters.visibility);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  const resp = await fetch(`${import.meta.env.VITE_API_URL}/images?${params}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

function App() {
  const { toggleTheme } = useTheme();
  const [filters, setFilters] = useState({
    day_phase: '',
    utc_day: '',
    visibility: '',
  });
  const [images, setImages] = useState([]);
  const [totalAvailable, setTotalAvailable] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasQueried, setHasQueried] = useState(false);

  async function loadImages(pageOffset = 0) {
    setLoading(true);
    setError(null);
    setImages([]);
    try {
      const data = await fetchImages(filters, { offset: pageOffset, limit: PAGE_SIZE });
      setImages(data.items);
      setTotalAvailable(data.total_available);
      setOffset(data.offset ?? pageOffset);
      setHasQueried(true);
    } catch (err) {
      setError(err.message || 'Failed to fetch images');
    } finally {
      setLoading(false);
    }
  }

  function handleApplyFilters() {
    setOffset(0);
    loadImages(0);
  }

  function handlePageChange(pageIndex) {
    const nextOffset = pageIndex * PAGE_SIZE;
    setOffset(nextOffset);
    loadImages(nextOffset);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderContent() {
    if (loading) {
      return (
        <>
          <p className="loading" aria-live="polite">Fetching image metadata…</p>
          <LoadingSkeleton />
        </>
      );
    }

    if (error) {
      return (
        <div className="error-banner" role="alert">
          <p>Error: {error}</p>
        </div>
      );
    }

    if (!hasQueried) {
      return (
        <p className="empty-state hint">
          Select filters (optional), then click <strong>Apply Filters</strong> to load images.
        </p>
      );
    }

    if (images.length === 0 && totalAvailable === 0) {
      return <p className="empty-state">No images have been ingested yet.</p>;
    }

    if (images.length === 0 && totalAvailable > 0) {
      return <p className="empty-state">No images match the current filters.</p>;
    }

    return (
      <>
        <ResultsBar
          total={totalAvailable}
          offset={offset}
          pageSize={PAGE_SIZE}
          showingCount={images.length}
          onPageChange={handlePageChange}
          disabled={loading}
        />
        <ImageGrid images={images} />
        <ResultsBar
          total={totalAvailable}
          offset={offset}
          pageSize={PAGE_SIZE}
          showingCount={images.length}
          onPageChange={handlePageChange}
          disabled={loading}
        />
      </>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>S3 Annotation Demo</h1>
        <ThemeToggle onToggle={toggleTheme} />
      </header>
      <main>
        <DemoDescription />
        <FilterBar
          filters={filters}
          onChange={setFilters}
          onApply={handleApplyFilters}
          disabled={loading}
        />
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
export { fetchImages, PAGE_SIZE };
