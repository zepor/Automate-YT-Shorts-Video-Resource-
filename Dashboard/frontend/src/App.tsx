import { useState, useEffect } from 'react';
import './App.css';

interface VideoCardData {
  video: string;
  status?: string;
  highlights?: { start: string; end: string; type: string }[];
  rating?: number;
  approved?: boolean;
  edited?: boolean;
  edited_path?: string;
  published?: boolean;
  output_location?: string;
}

interface PipelineStatus {
  Ingested: VideoCardData[];
  Detection: VideoCardData[];
  Editing: VideoCardData[];
  Publishing: VideoCardData[];
}

// Utility: get video preview URL (relative to /temp/)
const getVideoUrl = (video: string, edited_path?: string) => {
  if (edited_path) {
    // If edited video exists, use it
    return `/temp/${edited_path.split('/').pop()}`;
  }
  return `/temp/${video}`;
};

// KanbanCard: Renders a single video card with preview and details
function KanbanCard({ data, step }: { data: VideoCardData; step: string }) {
  const videoUrl = getVideoUrl(data.video, data.edited_path);
  return (
    <div className="kanban-card">
      <div className="video-preview">
        {/* Only show preview if not a mock row */}
        {data.video && !data.video.startsWith('No videos') && (
          <video width={180} height={100} controls preload="metadata">
            <source src={videoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        )}
      </div>
      <div className="video-details">
        <strong>{data.video}</strong>
        {data.status && <div>Status: {data.status}</div>}
        {step === 'Detection' && data.highlights && (
          <div>
            <div>Highlights:</div>
            <ul>
              {data.highlights.length ? data.highlights.map((h, i) => (
                <li key={i}>{h.start ? `${h.start} - ${h.end} (${h.type})` : JSON.stringify(h)}</li>
              )) : <li>No highlights</li>}
            </ul>
            <div>Rating: {data.rating ?? 'N/A'} {data.approved ? '✅' : '❌'}</div>
          </div>
        )}
        {step === 'Editing' && (
          <div>
            <div>Edited: {data.edited ? 'Yes' : 'No'}</div>
            {data.edited_path && <div>Edited Path: {data.edited_path}</div>}
          </div>
        )}
        {step === 'Publishing' && (
          <div>
            <div>Published: {data.published ? 'Yes' : 'No'}</div>
            {data.output_location && (
              <div>
                Output: <a href={data.output_location} target="_blank" rel="noopener noreferrer">View</a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// KanbanColumn: Renders a column for a pipeline step
function KanbanColumn({ title, cards, step }: { title: string; cards: VideoCardData[]; step: string }) {
  return (
    <div className="kanban-col">
      <h3>{title}</h3>
      {cards.length ? (
        cards.map((data, i) => <KanbanCard key={i} data={data} step={step} />)
      ) : (
        <div className="kanban-card empty">No videos in {title.toLowerCase()}</div>
      )}
    </div>
  );
}

function App() {
  const [status, setStatus] = useState<string>('');
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string>('');

  // Helper to call backend API endpoints
  const runStep = async (step: string) => {
    setStatus(`Running ${step}...`);
    setError('');
    try {
      let url = '';
      switch (step) {
        case 'ingest':
          url = '/api/ingest/';
          break;
        case 'detection':
          url = '/api/run_step/detection';
          break;
        case 'editing':
          url = '/api/run_step/editing';
          break;
        case 'publishing':
          url = '/api/run_step/publishing';
          break;
        case 'evaluation':
          url = '/api/evaluation/';
          break;
        default:
          setError('Unknown step');
          return;
      }
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setStatus(`${step} completed successfully.`);
        fetchPipelineStatus();
      } else {
        setStatus('');
        setError(data.message || `${step} failed.`);
      }
    } catch (err) {
      setStatus('');
      setError(`Error running ${step}: ${String(err)}`);
    }
  };

  // Fetch pipeline status for Kanban/flow chart
  const fetchPipelineStatus = async () => {
    try {
      const res = await fetch('/api/pipeline_status');
      const data = await res.json();
      setPipeline(data);
    } catch (err) {
      console.error('Error fetching pipeline status:', err);
      setError('Failed to fetch pipeline status');
    }
  };

  // Fetch status on mount
  useEffect(() => {
    fetchPipelineStatus();
  }, []);

  return (
    <div className="container">
      <h1>Twitch Shorts Pipeline Dashboard</h1>
      <div className="button-row">
        <button onClick={() => runStep('ingest')}>Ingest VOD</button>
        <button onClick={() => runStep('detection')}>Highlight Detection</button>
        <button onClick={() => runStep('editing')}>Editing</button>
        <button onClick={() => runStep('publishing')}>Publishing</button>
        <button onClick={() => runStep('evaluation')}>Evaluation</button>
      </div>
      {status && <div className="status">{status}</div>}
      {error && <div className="error">{error}</div>}
      <h2>Pipeline Flow</h2>
      <div className="kanban">
        <KanbanColumn title="Ingested" cards={pipeline?.Ingested || []} step="Ingested" />
        <KanbanColumn title="Detection" cards={pipeline?.Detection || []} step="Detection" />
        <KanbanColumn title="Editing" cards={pipeline?.Editing || []} step="Editing" />
        <KanbanColumn title="Publishing" cards={pipeline?.Publishing || []} step="Publishing" />
      </div>
    </div>
  );
}

export default App;
