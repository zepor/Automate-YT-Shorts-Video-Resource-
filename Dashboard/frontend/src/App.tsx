import { useState, useEffect, useRef } from 'react';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Modal, Button, Accordion, Spinner } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';

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

// Utility to fetch all markdown files in the repo (frontend fetches from backend-provided list)
const fetchMarkdownFiles = async (): Promise<string[]> => {
  try {
    const res = await fetch('/api/markdown_files');
    if (!res.ok) throw new Error('Markdown file list not found');
    return await res.json();
  } catch (err) {
    // Show a toast or alert, or set an error state
    alert('Could not load markdown files.');
    return [];
  }
};

// Utility to fetch markdown file content
const fetchMarkdownContent = async (filename: string): Promise<string> => {
  const res = await fetch(`/api/markdown_file/${filename}`);
  return res.text();
};

function VideoDetailsTable({ highlights }: { highlights?: { start: string; end: string; type: string; rating?: number; approved?: boolean; edited?: boolean; planogram?: string; edited_video?: string }[] }) {
  if (!highlights || !highlights.length) return <div className="text-muted">No highlights</div>;
  return (
    <div className="table-responsive">
      <table className="table table-sm table-bordered align-middle mb-0">
        <thead className="table-light">
          <tr>
            <th>Start</th>
            <th>End</th>
            <th>Type</th>
            <th>Rating</th>
            <th>Approved</th>
            <th>Edited</th>
            <th>Planogram</th>
            <th>Edited Video</th>
          </tr>
        </thead>
        <tbody>
          {highlights.map((h, i) => (
            <tr key={i}>
              <td>{h.start}</td>
              <td>{h.end}</td>
              <td>{h.type}</td>
              <td>{h.rating ?? ''}</td>
              <td>{h.approved ? '✅' : '❌'}</td>
              <td>{h.edited !== undefined ? (h.edited ? '✅' : '❌') : ''}</td>
              <td>{h.planogram ?? ''}</td>
              <td>{h.edited_video ?? ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// VideoCard with error handling for video playback
function VideoCard({ data, step }: { data: VideoCardData; step: string }) {
  const [expanded, setExpanded] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const handleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      }
    }
  };
  const videoUrl = getVideoUrl(data.video, data.edited_path);
  return (
    <div className={`card shadow-sm mb-3 ${expanded ? 'border-primary' : ''}`}>
      <div className="card-body">
        <div className="d-flex align-items-center mb-2">
          <h6 className="card-title text-truncate flex-grow-1 mb-0">{data.video}</h6>
          <Button size="sm" variant="outline-primary" className="ms-2" onClick={() => setExpanded(e => !e)}>
            {expanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
        <div className="position-relative mb-2 video-center-align">
          {videoError ? (
            <div className="alert alert-warning p-2">Video not available or cannot be played.</div>
          ) : (
            <video
              ref={videoRef}
              className={`rounded video-max-width`}
              width={expanded ? 480 : '100%'}
              height={expanded ? 320 : 180}
              controls
              preload="metadata"
              onError={() => setVideoError(true)}
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          )}
          {!videoError && (
            <Button
              size="sm"
              variant="secondary"
              className="position-absolute top-0 end-0 m-2"
              style={{ zIndex: 2 }}
              onClick={handleFullscreen}
            >
              Fullscreen
            </Button>
          )}
        </div>
        {expanded && (
          <div className="video-details-table mt-2">
            {step === 'Detection' && <VideoDetailsTable highlights={data.highlights} />}
            {step === 'Editing' && (
              <table className="table table-bordered table-sm">
                <tbody>
                  <tr><th>Edited</th><td>{data.edited ? 'Yes' : 'No'}</td></tr>
                  {data.edited_path && <tr><th>Edited Path</th><td>{data.edited_path}</td></tr>}
                </tbody>
              </table>
            )}
            {step === 'Publishing' && (
              <table className="table table-bordered table-sm">
                <tbody>
                  <tr><th>Published</th><td>{data.published ? 'Yes' : 'No'}</td></tr>
                  {data.output_location && <tr><th>Output</th><td><a href={data.output_location} target="_blank" rel="noopener noreferrer">View</a></td></tr>}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function PipelineSection({
  title,
  step,
  videos,
  onRun,
  running,
  disabled,
  children,
}: {
  title: string;
  step: string;
  videos: VideoCardData[];
  onRun: () => void;
  running: boolean;
  disabled: boolean;
  children?: React.ReactNode;
}) {
  // Move the action button below the header to avoid nested <button>
  return (
    <Accordion.Item eventKey={step}>
      <Accordion.Header>
        <div className="d-flex align-items-center w-100 justify-content-between">
          <span>{title}</span>
        </div>
      </Accordion.Header>
      <Accordion.Body>
        <div className="mb-3">
          <Button
            variant={running ? 'primary' : 'outline-secondary'}
            size="sm"
            disabled={disabled || running}
            onClick={onRun}
          >
            {running ? <Spinner animation="border" size="sm" /> : `Run ${title}`}
          </Button>
        </div>
        {children}
        <div className="row g-3">
          {videos.length ? videos.map((data, i) => (
            <div className="col-12 col-md-6 col-lg-4" key={i}>
              <VideoCard data={data} step={step} />
            </div>
          )) : <div className="text-muted">No videos in this stage.</div>}
        </div>
      </Accordion.Body>
    </Accordion.Item>
  );
}

function App() {
  const [status, setStatus] = useState<string>('');
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string>('');
  const [runningStep, setRunningStep] = useState<string>('');
  const [showReadme, setShowReadme] = useState(false);
  const [readmeContent, setReadmeContent] = useState('');
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [promptContent, setPromptContent] = useState('');
  const [showReadmeBox, setShowReadmeBox] = useState(false);
  const [showPromptBox, setShowPromptBox] = useState(false);
  const [markdownFiles, setMarkdownFiles] = useState<string[]>([]);
  const [selectedMd, setSelectedMd] = useState<string>('');
  const [loadingPrompt, setLoadingPrompt] = useState(false);

  // Helper to call backend API endpoints
  const runStep = async (step: string) => {
    setStatus(`Running ${step}...`);
    setError('');
    setRunningStep(step);
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
          setRunningStep('');
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
    setRunningStep('');
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

  // (Removed unused fetchReadme function)
  // Fetch selected markdown file content
  // (handled by handleSelectMd and fetchMarkdownContent)
  const handleSelectMd = async (filename: string) => {
    setSelectedMd(filename);
    setReadmeContent('');
    const content = await fetchMarkdownContent(filename);
    setReadmeContent(content);
  };

  // Fetch prompt recommendations from backend evaluation API
  const fetchPrompt = async () => {
    setShowPromptBox(true);
    setLoadingPrompt(true);
    setPromptContent('');
    try {
      const res = await fetch('/api/evaluation/', { method: 'POST' });
      if (!res.ok) throw new Error('Evaluation API error');
      const data = await res.json();
      if (data.prompt_recommendation) {
        setPromptContent(data.prompt_recommendation);
      } else {
        setPromptContent('No recommendations yet.');
      }
    } catch (err) {
      setPromptContent('Error: Could not fetch prompt recommendations.');
    }
    setLoadingPrompt(false);
  };

  // Fetch markdown file list on mount
  useEffect(() => {
    fetchMarkdownFiles().then(setMarkdownFiles);
  }, []);

  // Fetch status on mount
  useEffect(() => {
    fetchPipelineStatus();
  }, []);

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="fw-bold">Twitch Shorts Pipeline Dashboard</h1>
        <div>
          <Button
            variant={showReadmeBox ? 'dark' : 'outline-dark'}
            className="me-2"
            onClick={() => setShowReadmeBox((v) => !v)}
          >
            {showReadmeBox ? 'Hide Project Guide' : 'Show Project Guide'}
          </Button>
          <Button
            variant={showPromptBox ? 'primary' : 'outline-primary'}
            onClick={fetchPrompt}
          >
            {showPromptBox ? 'Hide Prompt Recommendations' : 'Show Prompt Recommendations'}
          </Button>
        </div>
      </div>
      <div className="row">
        {showReadmeBox && (
          <div className="col-12 col-md-6 mb-3">
            <div className="card h-100">
              <div className="card-header d-flex justify-content-between align-items-center">
                <span className="fw-bold">Project Guide</span>
                <Button size="sm" variant="outline-secondary" onClick={() => setShowReadmeBox(false)}>
                  Close
                </Button>
              </div>
              <div className="card-body overflow-auto max-height-400">
                <div className="mb-2">
                  <strong>Markdown Files:</strong>
                  <ul className="list-unstyled mb-2">
                    {markdownFiles.map(f => (
                      <li key={f}>
                        <Button
                          size="sm"
                          variant={selectedMd === f ? 'primary' : 'outline-primary'}
                          className="me-2 mb-1"
                          onClick={() => handleSelectMd(f)}
                        >
                          {f}
                        </Button>
                      </li>
                    ))}
                  </ul>
                </div>
                {selectedMd && (
                  <div className="markdown-scrollbox">
                    <ReactMarkdown>{readmeContent}</ReactMarkdown>
                  </div>
                )}
                {!selectedMd && <div className="text-muted">Select a markdown file to view its content.</div>}
              </div>
            </div>
          </div>
        )}
        {showPromptBox && (
          <div className="col-12 col-md-6 mb-3">
            <div className="card h-100">
              <div className="card-header d-flex justify-content-between align-items-center">
                <span className="fw-bold">Prompt Recommendations</span>
                <Button size="sm" variant="outline-secondary" onClick={() => setShowPromptBox(false)}>
                  Close
                </Button>
              </div>
              <div className="card-body overflow-auto max-height-400">
                {loadingPrompt ? (
                  <div className="d-flex justify-content-center align-items-center loading-spinner-container">
                    <Spinner animation="border" role="status" />
                    <span className="ms-2">Loading...</span>
                  </div>
                ) : (
                  <ReactMarkdown>{promptContent || 'No recommendations yet.'}</ReactMarkdown>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      {status && <div className="alert alert-info">{status}</div>}
      {error && <div className="alert alert-danger">{error}</div>}
      <Accordion defaultActiveKey="Ingested" alwaysOpen className="mb-4">
        <PipelineSection
          title="Ingestion"
          step="Ingested"
          videos={pipeline?.Ingested || []}
          onRun={() => runStep('ingest')}
          running={runningStep === 'ingest'}
          disabled={false}
        />
        <PipelineSection
          title="Detection"
          step="Detection"
          videos={pipeline?.Detection || []}
          onRun={() => runStep('detection')}
          running={runningStep === 'detection'}
          disabled={!pipeline?.Detection?.length}
        />
        <PipelineSection
          title="Editing"
          step="Editing"
          videos={pipeline?.Editing || []}
          onRun={() => runStep('editing')}
          running={runningStep === 'editing'}
          disabled={!pipeline?.Editing?.length}
        />
        <PipelineSection
          title="Publishing"
          step="Publishing"
          videos={pipeline?.Publishing || []}
          onRun={() => runStep('publishing')}
          running={runningStep === 'publishing'}
          disabled={!pipeline?.Publishing?.length}
        />
        <PipelineSection
          title="Evaluation"
          step="Evaluation"
          videos={[]} // No videos, just a button
          onRun={() => runStep('evaluation')}
          running={runningStep === 'evaluation'}
          disabled={false}
        >
          <div className="mb-2">Run evaluation to get prompt recommendations and pipeline feedback.</div>
        </PipelineSection>
      </Accordion>
      {/* README Modal */}
      <Modal show={showReadme && !showReadmeBox} onHide={() => setShowReadme(false)} size="lg" className="markdown-modal">
        <Modal.Header closeButton>
          <Modal.Title>Project Guide (READMEBUILD.md)</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ReactMarkdown>{readmeContent}</ReactMarkdown>
        </Modal.Body>
      </Modal>
      {/* Prompt Recommendations Modal */}
      <Modal show={showPromptModal && !showPromptBox} onHide={() => setShowPromptModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Prompt Recommendations</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ReactMarkdown>{promptContent || 'No recommendations yet.'}</ReactMarkdown>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default App;
