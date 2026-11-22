import React, { useEffect, useState } from 'react';
import {
  ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, ChevronRight,
  CircleAlert, CircleHelp, ClipboardCheck, Database, ExternalLink, FileSearch,
  FileText, GraduationCap, Info, Layers3, Link2, ListChecks, LockKeyhole,
  Menu, Play, Search, ShieldCheck, Sparkles, Video, X
} from 'lucide-react';

const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const LEGACY = 'https://veriloop-research.streamlit.app';
const validUrl = (value) => {
  try {
    const host = new URL(value).hostname.toLowerCase();
    return ['youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtu.be','www.youtu.be','www.youtube-nocookie.com','youtube-nocookie.com'].includes(host);
  } catch { return false; }
};

async function readJson(url, opts) {
  const response = await fetch(API + url, opts);
  let value = {};
  try { value = await response.json(); } catch { /* empty server response */ }
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'The service is temporarily unavailable.');
  return value;
}

const features = [
  { icon: Video, title: 'YouTube focused', description: 'Explore published video titles and descriptions.' },
  { icon: Search, title: 'Evidence-based', description: 'Find related original references and published fact-checks.' },
  { icon: Layers3, title: 'Transparent results', description: 'Understand what was found, what is missing and why.' },
  { icon: GraduationCap, title: 'Research-driven', description: 'A carefully scoped academic research MVP.' }
];

function Logo({ onClick }) {
  return <button type="button" className="logo" onClick={onClick} aria-label="Go to VeriLoop homepage">
    <span className="logo-mark"><ShieldCheck size={31} strokeWidth={2.5}/></span>
    <span><strong>VeriLoop</strong><small>News Evidence Explorer</small></span>
  </button>;
}

function VideoForm({ onVerify, busy, compact=false }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  return <form className={compact ? 'search-form compact-search' : 'search-form'} onSubmit={(e) => {
    e.preventDefault();
    if (!validUrl(url.trim())) {setError('Enter a public YouTube video URL.');return;}
    setError('');
    onVerify(url.trim());
  }}>
    <label htmlFor={compact ? 'verify-top' : 'verify-home'}><Video size={19}/> YouTube video link</label>
    <div className="search-line">
      <input id={compact ? 'verify-top' : 'verify-home'} type="url" value={url} onChange={(e) => setUrl(e.target.value)}
        placeholder="https://www.youtube.com/watch?v=..." maxLength={2048} autoComplete="off" />
      <button className="btn btn-dark" type="submit" disabled={busy}><Search size={18}/>{busy ? 'Checking…' : 'Check this video'}<ArrowRight size={18}/></button>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
  </form>;
}

function SiteHeader({ page, go, mobile, setMobile }) {
  return <header className="site-header">
    <div className="nav-inner">
      <Logo onClick={() => go('home')}/>
      <nav className={mobile ? 'nav open' : 'nav'} aria-label="Main menu">
        {[['home','Home'],['verify','Verify video'],['how','How it works'],['sources','Evidence sources'],['about','About']].map(([id,label]) =>
          <button key={id} className={page === id ? 'nav-link active' : 'nav-link'} onClick={() => {go(id);setMobile(false);}}>{label}</button>)}
      </nav>
      <button className="btn btn-dark header-cta" onClick={() => go('verify')}>Try VeriLoop <ArrowRight size={18}/></button>
      <button className="mobile-menu" onClick={() => setMobile(!mobile)} aria-label={mobile ? 'Close menu' : 'Open menu'}>{mobile ? <X/> : <Menu/>}</button>
    </div>
  </header>;
}

function DemoLaptop() {
  return <div className="laptop-wrap" aria-label="Illustration of the VeriLoop evidence review interface">
    <div className="laptop-screen">
      <div className="mock-browser"><span/><span/><span/><small>veriloop / verification</small></div>
      <div className="mock-top"><span className="tiny-logo"><ShieldCheck size={16}/> VeriLoop</span><span className="tiny-pill">Evidence explorer</span></div>
      <div className="mock-content">
        <div className="mock-video"><div className="mock-sun"><Play size={30} fill="white"/></div><small>VIDEO ANALYSIS</small></div>
        <div className="mock-results"><b>Evidence overview</b><div className="mock-meter"><i/></div>
          <p><span>5</span> candidate statements</p><p><span>?</span> context unresolved</p>
          <div className="mock-note">No verdict without evidence</div>
        </div>
      </div>
    </div>
    <div className="laptop-base"/><div className="floating-chip chip-top"><FileSearch size={20}/> Extract claims</div>
    <div className="floating-chip chip-right"><Link2 size={20}/> Find original sources</div>
    <div className="floating-chip chip-bottom"><ShieldCheck size={20}/> Explain evidence</div>
  </div>;
}

function Home({ go, onVerify, busy, sources }) {
  return <>
    <section className="hero">
      <div className="hero-content">
        <span className="hero-tag"><GraduationCap size={18}/> Research prototype · MVP</span>
        <h1>Check YouTube News Videos.<br/>Find Evidence. <em>Stay Informed.</em></h1>
        <p>Explore claims from a YouTube video's published information, see related original sources, and understand what is still uncertain.</p>
        <div className="hero-actions">
          <button className="btn btn-mint" onClick={() => go('verify')}><Play size={19} fill="currentColor"/> Verify a video now <ArrowRight size={19}/></button>
          <button className="btn btn-outline-white" onClick={() => go('how')}><Info size={19}/> See how it works</button>
        </div>
      </div>
      <DemoLaptop/>
    </section>
    <section className="feature-band">{features.map(({icon:Icon,title,description}) =>
      <article className="feature" key={title}><span className="feature-icon"><Icon size={27}/></span>
        <div><h3>{title}</h3><p>{description}</p></div></article>)}</section>
    <section className="home-main" id="workflow">
      <div className="work-steps">
        <span className="eyebrow">SIMPLE · TRANSPARENT · EVIDENCE FIRST</span>
        <h2>How VeriLoop works</h2>
        <div className="steps-list">
          {[
            {icon:Link2,title:'Paste a video link',text:'Start with one public YouTube URL.'},
            {icon:FileText,title:'Find candidate claims',text:'Extract up to five statements from the published title and description.'},
            {icon:Search,title:'Explore related evidence',text:'Compare the original sources and see what remains unresolved.'}
          ].map(({icon:Icon,title,text},i)=><div className="step" key={title}>
            <span className="step-circle"><Icon size={26}/><b>{i+1}</b></span><h3>{title}</h3><p>{text}</p>
          </div>)}
        </div>
      </div>
      <div className="try-card"><div className="try-ornament"><Play size={86} fill="currentColor"/></div>
        <span className="eyebrow">GET STARTED</span><h2>Try it yourself</h2><p>Paste a public YouTube video link to begin your evidence check.</p>
        <VideoForm onVerify={onVerify} busy={busy}/>
        <small>Free research demonstration. No account needed for preliminary results.</small>
      </div>
    </section>
    <section className="source-band" id="evidence">
      <div><span className="eyebrow">EXTERNAL REFERENCES</span><h2>Our evidence sources</h2><p>Selected original publications for claim retrieval, not partnerships, endorsements or automatic verdicts.</p></div>
      <div className="source-logos">{(sources?.publishers?.length ? sources.publishers : ['NASA','WHO','USGS','NOAA','AFP Fact Check']).slice(0,8).map(name => <span key={name}>{name}</span>)}</div>
    </section>
    <section className="about-strip" id="about"><div><span className="eyebrow">ABOUT THE PROJECT</span>
      <h2>Evidence before verdicts.</h2><p>VeriLoop is a university research prototype. The public checker compares metadata claims with a small evidence library and available published fact-checks. It does not inspect full video or audio and never treats a topical match as proof.</p></div>
      <button className="btn btn-outline-dark" onClick={() => go('about')}>Learn more <ArrowRight size={18}/></button>
    </section>
  </>;
}

function NoEvidence({ claim }) {
  return <div className="reason-box"><CircleHelp size={21}/><div><b>No sufficient related evidence</b><p>We could not identify a close, context-compatible source for this statement. This does not mean the statement is false.</p>
    <small>Local reference library: no sufficient match. Online fact-check lookup: {claim.online_status?.toLowerCase().replaceAll('_',' ') || 'not run'}.</small></div></div>;
}

function SourceCard({ source, online }) {
  const sourceUrl = online ? source.article_url : source.source_url;
  const label = online ? source.publisher : source.source_name;
  return <article className="source-card"><div className="source-label"><BookOpen size={19}/><strong>{label}</strong><span>{online ? 'Published fact-check' : 'Curated reference'}</span></div>
    <p><b>What this source checked:</b> {online ? source.checked_claim : source.reference_claim}</p>
    <p><b>Source's own classification:</b> {online ? (source.publisher_rating || 'Not supplied') : source.external_reference_classification?.replaceAll('_', ' ')}</p>
    <p><b>Context:</b> {source.context_status?.toLowerCase().replaceAll('_',' ') || 'not established'}</p>
    <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="source-link">Read original publication <ArrowUpRight size={15}/></a>
    <small>Source classification is not a verdict on the submitted video.</small>
  </article>;
}

function Results({ data, onVerify, busy }) {
  const [selected, setSelected] = useState(0);
  useEffect(() => {setSelected(0);}, [data]);
  const summary = data.summary, video = data.video, claims = data.claims || [];
  const claim = claims[selected];
  return <div className="results-page">
    <div className="breadcrumb"><span>Home</span><ChevronRight size={15}/><span>Verify video</span><ChevronRight size={15}/><strong>Results</strong></div>
    <div className="results-heading"><div><span className="eyebrow">VERIFICATION RESULTS</span><h1>Check a video. Understand the evidence.</h1><p>Claim-by-claim findings from this video's published metadata.</p></div></div>
    <VideoForm onVerify={onVerify} busy={busy} compact/>
    <div className="results-overview">
      <div className="video-card">{video.thumbnail_url && <img src={video.thumbnail_url} alt="Video thumbnail supplied by YouTube"/>}
        <div><h2>{video.title || 'Untitled video'}</h2><p>{video.channel_name || 'Channel unavailable'}</p>
          <small>Published: {video.published_at ? new Date(video.published_at).toLocaleDateString() : 'Unknown'}</small>
          <a href={video.watch_url} rel="noopener noreferrer" target="_blank">Open on YouTube <ExternalLink size={15}/></a></div></div>
      <div className="summary-card"><h2><ClipboardCheck size={22}/> Result at a glance</h2><div className="stats">
        <div><FileText size={22}/><strong>{summary.statements}</strong><span>Statements found</span></div>
        <div><Link2 size={22}/><strong>{summary.with_related_sources}</strong><span>With related sources</span></div>
        <div><CircleHelp size={22}/><strong>{summary.without_related_sources}</strong><span>Without source match</span></div>
      </div><div className="overall-note"><Info size={20}/><p><b>Overall assessment: Not determined.</b> Related sources are research leads, not proof of truth or misleadingness; full narration and footage were not checked.</p></div></div>
    </div>
    <div className="results-tabs"><span className="active"><ListChecks size={19}/> Claim analysis ({claims.length})</span><span><Link2 size={18}/> Source comparisons</span><span><Info size={18}/> Clear explanations</span></div>
    {claims.length ? <div className="claim-workspace">
      <div className="claim-list" role="group" aria-label="Choose a statement">
        {claims.map((c,i) => <button key={c.id} className={selected === i ? 'claim-choice selected' : 'claim-choice'} onClick={() => setSelected(i)}>
          <span className="claim-index">{i+1}</span><span className="claim-copy">{c.text}</span>
          <span className={c.has_related_sources ? 'claim-label related' : 'claim-label'}>{c.has_related_sources ? 'Related sources' : 'Insufficient evidence'}</span><ChevronRight size={18}/></button>)}
      </div>
      <section className="claim-details"><span className="eyebrow">CLAIM {selected+1} OF {claims.length} · FROM THE {claim.source_field?.toUpperCase()}</span>
        <h2>{claim.text}</h2><div className="status-info"><CircleHelp size={22}/><div><b>{claim.has_related_sources ? 'Related sources found — not verified' : 'Insufficient evidence'}</b>
          <p>{claim.has_related_sources ? 'A similar published claim was found; its meaning and the video context must still be compared.' : 'There is not enough matching evidence to decide whether this claim is supported or misleading.'}</p></div></div>
        <h3>Why this result?</h3><p className="explanation">{claim.explanation}</p>
        {claim.has_related_sources ? <div className="evidence-list"><h3>Original source comparison</h3>
          {claim.references.map(ref => <SourceCard key={'ref'+ref.evidence_id} source={ref}/>)}
          {claim.factchecks.map((ref,i) => <SourceCard key={'online'+i} source={ref} online/>)}
        </div> : <NoEvidence claim={claim}/>}
        <details className="technical"><summary>Technical details for researchers <ChevronDown size={16}/></summary>
          <p>Preliminary state: {claim.preliminary_state}</p><p>Metadata stance cue: {claim.stance_cue}</p>
          <p>Fact-check index status: {claim.online_status}</p><p>Text matching is a retrieval technique, not a probability of truth.</p>
        </details>
        <a className="review-link" href={LEGACY} target="_blank" rel="noopener noreferrer"><LockKeyhole size={17}/> Human review available in the current research workspace <ArrowUpRight size={16}/></a>
      </section>
    </div> : <div className="empty-result">No checkable statements were found in the published metadata; this does not establish whether the video is accurate.</div>}
    <div className="limitations"><GraduationCap size={26}/><div><strong>Notes & limitations</strong><p>Only public YouTube title and description are inspected. No full video, audio, or image verification; no whole-video misleading verdict; third-party ratings are not transferred to the video.</p></div></div>
  </div>;
}

export default function App() {
  const [page, setPage] = useState('home');
  const [mobile, setMobile] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [sources, setSources] = useState(null);
  useEffect(() => {readJson('/api/sources').then(setSources).catch(() => {});}, []);

  const go = (p) => {
    setPage(p); setError('');
    if (['how','sources','about'].includes(p)) {
      setPage('home');
      requestAnimationFrame(() => document.getElementById(p === 'how' ? 'workflow' : p === 'sources' ? 'evidence' : 'about')?.scrollIntoView({behavior:'smooth'}));
    } else window.scrollTo({top:0,behavior:'smooth'});
  };
  const verify = async (url) => {
    setError('');setBusy(true);
    try {
      const result = await readJson('/api/verify', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
      setData(result);setPage('results');window.scrollTo({top:0});
    } catch (err) {setError(err.message);setPage('verify');window.scrollTo({top:0});}
    finally {setBusy(false);}
  };
  return <>
    <SiteHeader page={page} go={go} mobile={mobile} setMobile={setMobile}/>
    <main>
      {error && <div role="alert" className="global-error"><CircleAlert size={21}/>{error}</div>}
      {page === 'home' ? <Home go={go} onVerify={verify} busy={busy} sources={sources}/> :
        page === 'results' && data ? <Results data={data} onVerify={verify} busy={busy}/> :
        <div className="verify-landing"><span className="eyebrow">VERIFICATION WORKSPACE</span><h1>Check a YouTube video</h1>
          <p>Paste a public link to examine up to five candidate factual claims and available related evidence.</p>
          <VideoForm onVerify={verify} busy={busy}/>
          <div className="verify-assurance"><ShieldCheck/><p>We never label a video false simply because a fact-check source shares similar words. Missing evidence remains unresolved.</p></div>
        </div>}
    </main>
    <footer className="site-footer"><div className="footer-top"><Logo onClick={() => go('home')}/>
      <div><strong>Explore</strong><button onClick={() => go('verify')}>Verify a video</button><button onClick={() => go('how')}>How it works</button></div>
      <div><strong>Research</strong><a href={LEGACY} target="_blank" rel="noopener noreferrer">Existing reviewer workspace <ArrowUpRight size={13}/></a><button onClick={() => go('sources')}>Evidence sources</button></div>
    </div><div className="footer-bottom">© VeriLoop · Academic research MVP · No automatic accusations or misinformation scores · No direct association with referenced publishers</div></footer>
  </>;
}
