import { useCallback, useEffect, useRef, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { ArrowRight, ArrowUpRight, Check, CheckCircle2, ChevronDown, FileText, History, LockKeyhole, LogOut, RefreshCw, RotateCcw, ShieldCheck, X } from 'lucide-react';
import './AdsTxtEditor.css';

const API = '/api/ads-txt-editor';
const ROW_ERRORS = {
  field_count: 'Die Zeile muss drei oder vier durch Kommas getrennte Felder enthalten.',
  invalid_domain: 'Die Domain des Werbesystems ist ungültig.',
  invalid_account: 'Die Anbieter- oder Konto-ID ist ungültig.',
  invalid_relationship: 'Als Beziehung ist DIRECT oder RESELLER erforderlich.',
  invalid_certification: 'Die Zertifizierungs-ID ist ungültig.',
  control_character: 'Die Zeile enthält ein nicht erlaubtes Steuerzeichen.',
  unknown_directive: 'Diese ads.txt-Direktive wird nicht unterstützt.',
  invalid_directive: 'Der Wert dieser ads.txt-Direktive ist ungültig. Bitte prüfe die Angabe deines Anbieters.',
  conflicting_directive: 'Diese Direktive widerspricht einer bestehenden Zuordnung. Vorhandene Zuordnungen werden beim Ergänzen nicht ersetzt.',
};
const ERROR_TEXT = {
  invalid_credentials: 'Das Passwort stimmt nicht. Bitte versuche es erneut.',
  authentication_required: 'Deine Sitzung ist abgelaufen. Bitte melde dich erneut an. Deine Eingabe bleibt erhalten.',
  csrf_failed: 'Deine Sicherheitsfreigabe wurde erneuert. Bitte führe den Schritt noch einmal aus.',
  origin_forbidden: 'Diese Anfrage wurde nicht zugelassen. Bitte öffne die Verwaltung direkt auf transfernews.de.',
  revision_conflict: 'Die Datei wurde zwischenzeitlich geändert. Lade den aktuellen Stand und prüfe deine Eingabe erneut.',
  invalid_rows: 'Einige Zeilen sind ungültig. Bitte korrigiere sie und prüfe deine Eingabe erneut.',
  rate_limited: 'Zu viele Anmeldeversuche. Bitte warte einige Minuten und versuche es erneut.',
  paste_too_large: 'Die Eingabe ist zu groß. Bitte füge weniger Zeilen auf einmal ein.',
  document_too_large: 'Die Datei würde zu groß werden. Diese Änderung wurde nicht veröffentlicht.',
  not_initialized: 'Die Verwaltung wird noch eingerichtet. Bitte versuche es später erneut.',
  configuration_unavailable: 'Die Verwaltung ist momentan nicht verfügbar. Bitte versuche es später erneut.',
  revision_not_found: 'Diese Version ist nicht mehr verfügbar. Bitte aktualisiere den Versionsverlauf.',
  no_changes: 'Es gibt keine neuen Zeilen zu veröffentlichen.',
  invalid_json: 'Die Anfrage konnte nicht gelesen werden. Bitte versuche den Schritt erneut.',
  invalid_request: 'Die Anfrage konnte nicht verarbeitet werden. Bitte lade den aktuellen Stand neu.',
};

function readableDate(value) {
  const date = new Date(value);
  return value && !Number.isNaN(date.getTime())
    ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
    : 'Noch keine Angabe';
}

function lines(text) {
  if (!text) return [];
  const result = text.split(/\r\n|\n|\r/);
  if (result[result.length - 1] === '') result.pop();
  return result;
}

function difference(current, target) {
  const remainder = new Map();
  for (const line of lines(current)) remainder.set(line, (remainder.get(line) || 0) + 1);
  let added = 0;
  for (const line of lines(target)) {
    if (remainder.get(line)) remainder.set(line, remainder.get(line) - 1);
    else added += 1;
  }
  return { added, removed: [...remainder.values()].reduce((sum, count) => sum + count, 0) };
}

// Textarea selections count CRLF as one character. Keep the clipboard text
// unchanged in state and in the API request, including leading/trailing spaces.
function rawOffset(text, index) {
  let raw = 0;
  for (let visible = 0; visible < index && raw < text.length; visible += 1) {
    raw += text[raw] === '\r' && text[raw + 1] === '\n' ? 2 : 1;
  }
  return raw;
}

function DocumentView({ content, label, className = '' }) {
  return <pre className={`ate-document ${className}`} tabIndex={0} aria-label={label}>
    <code>{content || '# Die Datei enthält noch keine Zeilen.'}</code>
  </pre>;
}

function CompareDialog({ current, target, pending, stale, error, onClose, onRestore }) {
  const dialog = useRef(null);
  const close = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    close.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = overflow;
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  const keyDown = event => {
    if (event.key === 'Escape' && !pending) { event.preventDefault(); onClose(); }
    if (event.key !== 'Tab') return;
    const focusable = [...dialog.current.querySelectorAll('button:not(:disabled), [tabindex="0"]')];
    const first = focusable[0], last = focusable[focusable.length - 1];
    const outside = !focusable.includes(document.activeElement);
    if (event.shiftKey && (document.activeElement === first || outside)) { event.preventDefault(); last?.focus(); }
    if (!event.shiftKey && (document.activeElement === last || outside)) { event.preventDefault(); first?.focus(); }
  };
  const changes = difference(current.content, target.content);
  return <div className="ate-modal-backdrop">
    <section className="ate-modal" role="dialog" aria-modal="true" aria-labelledby="restore-title"
      aria-describedby="restore-description" ref={dialog} onKeyDown={keyDown}>
      <div className="ate-modal-heading">
        <div><span className="ate-eyebrow">VERSION VERGLEICHEN</span><h2 id="restore-title">Version {target.revision} wiederherstellen?</h2></div>
        <button type="button" className="ate-icon-button" aria-label="Vergleich schließen" ref={close} onClick={onClose} disabled={pending}><X size={21} aria-hidden="true" /></button>
      </div>
      <p id="restore-description">Der ausgewählte Stand wird als neue Version veröffentlicht. Alle bisherigen Versionen bleiben im Verlauf erhalten.</p>
      <div className="ate-diff-counts"><span>+{changes.added} Zeilen</span><span>−{changes.removed} Zeilen</span><small>Vergleich nach Zeileninhalt</small></div>
      <div className="ate-compare-grid">
        <div><h3>Aktuell <span>Version {current.revision}</span></h3><DocumentView content={current.content} label="Aktuelle Datei im Vergleich" /></div>
        <div><h3>Ausgewählter Stand <span>Version {target.revision}</span></h3><DocumentView content={target.content} label="Ausgewählte historische Datei" /></div>
      </div>
      {error && <p className="ate-inline-error" role="alert">{error}</p>}
      {stale && <p className="ate-inline-error">Bitte schließe den Vergleich und lade zuerst den aktuellen Stand neu.</p>}
      <div className="ate-modal-actions">
        <button type="button" className="ate-button ate-button-secondary" onClick={onClose} disabled={pending}>Abbrechen</button>
        <button type="button" className="ate-button ate-button-primary" onClick={onRestore} disabled={pending || stale}>
          <RotateCcw size={16} aria-hidden="true" />{pending ? 'Wird wiederhergestellt …' : `Version ${target.revision} wiederherstellen`}
        </button>
      </div>
    </section>
  </div>;
}

export default function AdsTxtEditor() {
  const [session, setSession] = useState(null);
  const [documentState, setDocument] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyCursor, setHistoryCursor] = useState(null);
  const [historyError, setHistoryError] = useState(false);
  const [password, setPassword] = useState('');
  const [text, setText] = useState('');
  const [preview, setPreview] = useState(null);
  const [invalidRows, setInvalidRows] = useState([]);
  const [invalidCount, setInvalidCount] = useState(0);
  const [target, setTarget] = useState(null);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('session');
  const csrf = useRef('');
  const locked = useRef(false);
  const active = useRef(false);
  const controllers = useRef(new Set());
  const pasteField = useRef(null);
  const previewHeading = useRef(null);
  const auth = session?.authenticated === true;

  const request = useCallback(async (path, body) => {
    const controller = new AbortController();
    controllers.current.add(controller);
    try {
      const response = await fetch(API + path, {
        method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: { Accept: 'application/json', ...(body === undefined ? {} : { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf.current }) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: controller.signal,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw Object.assign(new Error('editor_request_failed'), { status: response.status, data });
      return data;
    } finally { controllers.current.delete(controller); }
  }, []);

  const fetchSession = useCallback(async () => {
    const value = await request('/session');
    if (!active.current) return value;
    csrf.current = value.csrf_token || '';
    setSession(value);
    if (value.authenticated !== true) { setDocument(null); setHistory([]); setHistoryCursor(null); setTarget(null); setPreview(null); }
    return value;
  }, [request]);

  const receiveHistory = useCallback(value => {
    setHistory(value.revisions || []);
    setHistoryCursor(Number.isInteger(value.next_before) ? value.next_before : null);
    setHistoryError(false);
  }, []);

  const loadWorkspace = useCallback(async () => {
    const [current, versions] = await Promise.allSettled([request('/document'), request('/history')]);
    if (!active.current) return;
    if (current.status === 'rejected') throw current.reason;
    if (typeof current.value.content !== 'string' || !Number.isInteger(current.value.revision)) throw new Error('invalid_document');
    setDocument(current.value);
    setStale(false);
    setPreview(null);
    if (versions.status === 'fulfilled') {
      receiveHistory(versions.value);
    } else {
      if ([401, 403].includes(versions.reason.status)) throw versions.reason;
      setHistoryError(true);
    }
  }, [request, receiveHistory]);

  const handleError = useCallback(async problem => {
    if (!active.current || problem.name === 'AbortError') return;
    const code = problem.data?.error;
    const message = ERROR_TEXT[code] || (problem.status === 401 ? ERROR_TEXT.authentication_required
      : problem.status === 409 ? ERROR_TEXT.revision_conflict
        : 'Die Verbindung konnte nicht abgeschlossen werden. Bitte versuche es erneut.');
    setError(message);
    if (problem.status === 409) { setStale(true); setPreview(null); }
    if (problem.status === 422 && code === 'invalid_rows') {
      setInvalidRows(problem.data.errors || []);
      setInvalidCount(Number.isInteger(problem.data.invalid_count) ? problem.data.invalid_count : (problem.data.errors || []).length);
      setPreview(null);
    }
    if (problem.status === 401) {
      csrf.current = '';
      setSession({ authenticated: false });
      setDocument(null); setHistory([]); setHistoryCursor(null); setPreview(null); setTarget(null);
      try { await fetchSession(); } catch { /* The login form offers a manual retry. */ }
    } else if (problem.status === 403 && code === 'csrf_failed') {
      setPreview(null);
      try { await fetchSession(); } catch { csrf.current = ''; }
    }
  }, [fetchSession]);

  const perform = async (name, operation) => {
    if (locked.current) return;
    locked.current = true;
    setBusy(name); setError(''); setNotice('');
    try { await operation(); } catch (problem) { await handleError(problem); }
    finally { locked.current = false; if (active.current) setBusy(''); }
  };

  useEffect(() => {
    active.current = true;
    const pendingRequests = controllers.current;
    (async () => {
      try {
        const value = await fetchSession();
        if (value.authenticated && active.current) await loadWorkspace();
      } catch (problem) { await handleError(problem); }
      finally { if (active.current) setBusy(''); }
    })();
    return () => { active.current = false; pendingRequests.forEach(controller => controller.abort()); };
  }, [fetchSession, handleError, loadWorkspace]);

  useEffect(() => { if (preview) previewHeading.current?.focus(); }, [preview]);

  const changeText = value => { setText(value); setPreview(null); setInvalidRows([]); setInvalidCount(0); setError(''); setNotice(''); };
  const paste = event => {
    const incoming = event.clipboardData?.getData('text/plain');
    if (incoming === undefined) return;
    event.preventDefault();
    const start = rawOffset(text, event.currentTarget.selectionStart);
    const end = rawOffset(text, event.currentTarget.selectionEnd);
    const prefix = text.slice(0, start);
    changeText(prefix + incoming + text.slice(end));
    const cursor = (prefix + incoming).replace(/\r\n|\r/g, '\n').length;
    requestAnimationFrame(() => pasteField.current?.setSelectionRange(cursor, cursor));
  };
  const login = event => {
    event.preventDefault();
    perform('login', async () => {
      try {
        if (!csrf.current) await fetchSession();
        const value = await request('/login', { password });
        csrf.current = value.csrf_token || '';
        setSession(value);
        await loadWorkspace();
      } finally { setPassword(''); }
    });
  };
  const refresh = () => perform('refresh', async () => { setTarget(null); await loadWorkspace(); setNotice('Der aktuelle Stand wurde geladen. Deine Eingabe bleibt erhalten.'); });
  const check = () => perform('preview', async () => {
    setInvalidRows([]); setInvalidCount(0);
    const value = await request('/preview', { text, expected_revision: documentState.revision });
    setPreview({ ...value, input: text });
  });
  const append = () => perform('append', async () => {
    const updated = await request('/append', { text: preview.input, expected_revision: preview.base_revision });
    setDocument(updated); setText(''); setPreview(null); setInvalidRows([]); setInvalidCount(0); setStale(false);
    setNotice(`Veröffentlicht. Die ads.txt ist jetzt auf Version ${updated.revision}.`);
    try { receiveHistory(await request('/history')); }
    catch { setHistoryError(true); }
  });
  const restore = () => perform('rollback', async () => {
    const updated = await request('/rollback', { target_revision: target.revision, expected_revision: documentState.revision });
    const restored = target.revision;
    setDocument(updated); setTarget(null); setPreview(null); setInvalidRows([]); setInvalidCount(0); setStale(false);
    setNotice(`Version ${restored} wurde als neue Version ${updated.revision} veröffentlicht. Deine Eingabe bleibt erhalten.`);
    try { receiveHistory(await request('/history')); }
    catch { setHistoryError(true); }
  });
  const logout = () => perform('logout', async () => {
    await request('/logout', {});
    csrf.current = ''; setSession({ authenticated: false }); setDocument(null); setHistory([]); setHistoryCursor(null);
    setText(''); setPreview(null); setTarget(null); setInvalidRows([]); setInvalidCount(0); setStale(false);
    setNotice('Du bist abgemeldet.');
    await fetchSession();
  });
  const loadOlder = () => perform('history', async () => {
    const value = await request(`/history?before=${historyCursor}`);
    setHistory(previous => {
      const present = new Set(previous.map(version => version.revision));
      return [...previous, ...(value.revisions || []).filter(version => !present.has(version.revision))];
    });
    setHistoryCursor(Number.isInteger(value.next_before) ? value.next_before : null);
  });
  const rows = lines(documentState?.content || '');

  return <div className="ads-manager" lang="de">
    <Helmet><title>ads.txt verwalten | TransferNews</title><meta name="robots" content="noindex, nofollow" /><meta name="referrer" content="same-origin" /></Helmet>
    <a className="ate-skip" href="#ads-main">Zum Inhalt</a>
    <header className="ate-header"><div className="ate-header-inner">
      <div className="ate-brand"><span className="ate-brand-word">transfer<span>news</span><span className="ate-brand-dot">.</span></span><span className="ate-brand-divider" /><span className="ate-product">ads.txt manager</span></div>
      <div className="ate-header-actions"><span className="ate-site"><span />transfernews.de</span>
        {auth && <button type="button" className="ate-logout" onClick={logout} disabled={Boolean(busy)}><LogOut size={16} aria-hidden="true" /><span>{busy === 'logout' ? 'Abmelden …' : 'Abmelden'}</span></button>}
      </div>
    </div></header>
    <main id="ads-main" className={`ate-main ${auth ? '' : 'ate-main-login'}`}>
      {!auth ? <section className="ate-login" aria-labelledby="login-title">
        <div className="ate-lock"><LockKeyhole size={27} strokeWidth={1.6} aria-hidden="true" /></div>
        <span className="ate-eyebrow">TRANSFERNEWS · WERBEPARTNER</span><h1 id="login-title">Deine ads.txt.<br />Alles an einem Ort.</h1>
        <p>Einträge ergänzen, Änderungen prüfen und frühere Versionen wiederherstellen.</p>
        {busy === 'session' ? <p className="ate-loading" role="status"><RefreshCw size={17} className="ate-spin" aria-hidden="true" />Sitzung wird geprüft …</p> : <form onSubmit={login}>
          <label htmlFor="editor-password">Passwort</label>
          <input id="editor-password" name="password" type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} disabled={Boolean(busy)} aria-describedby={error ? 'editor-login-error' : undefined} />
          {error && <p className="ate-inline-error" id="editor-login-error" role="alert">{error}</p>}
          {notice && <p className="ate-login-notice" role="status">{notice}</p>}
          <button type="submit" className="ate-button ate-button-primary" disabled={Boolean(busy)}>{busy === 'login' ? 'Wird angemeldet …' : 'Anmelden'}<ArrowRight size={17} aria-hidden="true" /></button>
        </form>}
        <div className="ate-login-foot"><ShieldCheck size={16} aria-hidden="true" />Geschützter Zugang zur ads.txt-Verwaltung</div>
      </section> : <>
        <div className="ate-page-heading"><div><span className="ate-eyebrow">WERBEPARTNER VERWALTEN</span><h1>ads.txt verwalten</h1><p>Neue Einträge prüfen und zur veröffentlichten Datei hinzufügen.</p></div>
          <div className="ate-page-actions"><button type="button" className="ate-button ate-button-secondary" onClick={refresh} disabled={Boolean(busy)}><RefreshCw size={16} className={busy === 'refresh' ? 'ate-spin' : ''} aria-hidden="true" /><span>Aktualisieren</span></button><a className="ate-button ate-button-secondary" href="/ads.txt" target="_blank" rel="noopener noreferrer">Datei öffnen<ArrowUpRight size={16} aria-hidden="true" /></a></div>
        </div>
        <div className="ate-feedback" aria-live="polite" aria-atomic="true">
          {error && <div className="ate-alert ate-alert-error" role="alert"><span>{error}</span>{stale && <button type="button" onClick={refresh} disabled={Boolean(busy)}>Aktuellen Stand laden</button>}</div>}
          {notice && <div className="ate-alert ate-alert-success"><CheckCircle2 size={19} aria-hidden="true" /><span>{notice}</span></div>}
        </div>
        {!documentState ? <section className="ate-card ate-empty" aria-busy={Boolean(busy)}><FileText size={30} aria-hidden="true" /><h2>{busy ? 'Datei wird geladen …' : 'Datei konnte nicht geladen werden'}</h2><p>{busy ? 'Der aktuelle Stand und die Versionen werden abgerufen.' : 'Bitte lade den aktuellen Stand erneut.'}</p>{!busy && <button type="button" className="ate-button ate-button-secondary" onClick={refresh}>Erneut versuchen</button>}</section> : <>
          <section className="ate-overview" aria-label="Übersicht der aktuellen Datei">
            <div><span className="ate-stat-label">Aktueller Stand</span><strong>Version {documentState.revision}<span className="ate-live">Veröffentlicht</span></strong></div>
            <div><span className="ate-stat-label">Dateiumfang</span><strong>{rows.length.toLocaleString('de-DE')} <small>Zeilen</small></strong></div>
            <div><span className="ate-stat-label">Letzte Änderung</span><strong className="ate-stat-date">{readableDate(documentState.created_at)}</strong></div>
          </section>
          <div className="ate-workspace">
            <section className="ate-card ate-edit-card" aria-labelledby="paste-title">
              <div className="ate-card-heading"><span className="ate-step">01</span><div><h2 id="paste-title">Neue Zeilen hinzufügen</h2><p>Einfügen. Prüfen. Veröffentlichen.</p></div></div>
              <div className="ate-card-body"><label className="ate-label" htmlFor="ads-paste">Zusätzliche ads.txt-Zeilen</label>
                <p id="paste-help" className="ate-help">Füge die Einträge deines Anbieters unverändert ein. Bereits vorhandene Datensätze werden in der Vorschau erkannt.</p>
                <textarea id="ads-paste" ref={pasteField} value={text} onChange={event => changeText(event.target.value)} onPaste={paste} spellCheck={false} autoCapitalize="off" autoCorrect="off" wrap="off" disabled={Boolean(busy)} rows={11} aria-describedby="paste-help paste-errors" aria-invalid={invalidCount > 0} placeholder={'# Zusätzliche Einträge hier einfügen\nanbieter.example, konto-id, DIRECT'} />
                <div className="ate-input-foot"><span>{lines(text).length} eingefügte Zeilen</span><button type="button" onClick={() => changeText('')} disabled={!text || Boolean(busy)}>Eingabe leeren</button></div>
                <div id="paste-errors">{invalidCount > 0 && <div className="ate-validation" role="alert"><h3>{invalidCount} ungültige {invalidCount === 1 ? 'Zeile' : 'Zeilen'}</h3>{invalidCount > invalidRows.length && <p>Angezeigt: {invalidRows.length} von {invalidCount} Fehlern.</p>}<ul>{invalidRows.map((row, index) => <li key={`${row.line}-${index}`}><strong>Zeile {row.line}</strong><span>{ROW_ERRORS[row.code] || 'Bitte prüfe das Format dieser Zeile.'}</span><code>{lines(text)[row.line - 1] || ''}</code></li>)}</ul></div>}</div>
                <button type="button" className="ate-button ate-button-primary ate-check-button" onClick={check} disabled={!text || Boolean(busy) || stale}>{busy === 'preview' ? <RefreshCw size={16} className="ate-spin" aria-hidden="true" /> : <Check size={17} aria-hidden="true" />}{busy === 'preview' ? 'Wird geprüft …' : 'Änderungen prüfen'}</button>
              </div>
            </section>
            <section className="ate-card ate-current-card" aria-labelledby="current-title">
              <div className="ate-card-heading"><FileText size={22} aria-hidden="true" /><div><h2 id="current-title">Veröffentlichte Datei</h2><p>ads.txt · Version {documentState.revision}</p></div><span className="ate-readonly">Nur lesen</span></div>
              <DocumentView content={documentState.content} label="Aktueller Inhalt der ads.txt" />
              <div className="ate-file-footer"><span>transfernews.de/ads.txt</span><span>{Number(documentState.bytes || 0).toLocaleString('de-DE')} Bytes</span></div>
            </section>
          </div>
          {preview && <section className="ate-card ate-preview" aria-labelledby="preview-title">
            <div className="ate-card-heading"><span className="ate-step">02</span><div><h2 id="preview-title" ref={previewHeading} tabIndex={-1}>Änderungen im Überblick</h2><p>Geprüft gegen Version {preview.base_revision}. Noch nicht veröffentlicht.</p></div></div>
            <div className="ate-preview-body"><div className="ate-preview-counts"><span className="ate-count-new"><strong>{preview.added_rows}</strong> neue Datensätze</span><span><strong>{preview.duplicate_rows}</strong> doppelte Datensätze</span><span><strong>0</strong> ungültige Zeilen</span></div>
              {preview.comment_lines > 0 && <p className="ate-help">Zusätzlich enthalten: {preview.comment_lines} Kommentarzeilen.</p>}
              {preview.duplicate_rows > 0 && <p className="ate-help">Doppelte Datensätze werden ausgelassen. Die bestehende Datei bleibt unverändert erhalten.</p>}
              {preview.can_apply ? <details className="ate-preview-details" open><summary>Diese Zeilen werden angehängt<ChevronDown size={16} aria-hidden="true" /></summary><DocumentView content={preview.appended_text} label="Vorschau der anzuhängenden Zeilen" /></details> : <p className="ate-nothing-new">Alles auf dem aktuellen Stand. Es gibt keine neuen Zeilen zu veröffentlichen.</p>}
              <div className="ate-publish-bar"><p><ShieldCheck size={17} aria-hidden="true" />Veröffentlichung als neue Version</p><button type="button" className="ate-button ate-button-primary" onClick={append} disabled={!preview.can_apply || Boolean(busy) || stale}>{busy === 'append' ? 'Wird veröffentlicht …' : 'Änderungen veröffentlichen'}<ArrowRight size={17} aria-hidden="true" /></button></div>
            </div>
          </section>}
          <section className="ate-card ate-history" aria-labelledby="history-title"><div className="ate-card-heading"><History size={22} aria-hidden="true" /><div><h2 id="history-title">Versionsverlauf</h2><p>Jede Veröffentlichung bleibt nachvollziehbar.</p></div><span className="ate-history-count">{history.length} {historyCursor ? 'angezeigt' : 'Versionen'}</span></div>
            {historyError ? <div className="ate-history-error"><p>Der Versionsverlauf konnte nicht geladen werden.</p><button type="button" className="ate-button ate-button-secondary" onClick={refresh} disabled={Boolean(busy)}>Erneut laden</button></div> : history.length === 0 ? <p className="ate-empty-history">Noch keine Versionen vorhanden.</p> : <div className="ate-table-wrap"><table><caption className="ate-sr-only">Gespeicherte Versionen der ads.txt</caption><thead><tr><th scope="col">Version</th><th scope="col">Änderung</th><th scope="col">Veröffentlicht am</th><th scope="col"><span className="ate-sr-only">Aktion</span></th></tr></thead><tbody>{history.map(version => <tr key={version.revision}>
              <td><span className="ate-version">v{version.revision}</span>{version.revision === documentState.revision && <span className="ate-current-tag">Aktuell</span>}</td>
              <td>{version.action === 'append' ? `${version.added_rows || 0} Datensätze ergänzt` : version.action === 'rollback' ? `Version ${version.restored_from} wiederhergestellt` : 'Ausgangsversion'}</td><td>{readableDate(version.created_at)}</td>
              <td><button type="button" className="ate-history-button" disabled={Boolean(busy) || version.revision === documentState.revision} onClick={() => perform('version', async () => { const value = await request(`/revisions/${version.revision}`); setTarget(value); })}>Vergleichen<ArrowRight size={14} aria-hidden="true" /></button></td>
            </tr>)}</tbody></table></div>}
            {!historyError && historyCursor !== null && <div className="ate-history-more"><button type="button" className="ate-button ate-button-secondary" onClick={loadOlder} disabled={Boolean(busy)}>{busy === 'history' ? 'Versionen werden geladen …' : 'Ältere Versionen laden'}<ChevronDown size={16} aria-hidden="true" /></button></div>}
          </section>
          <footer className="ate-footer"><ShieldCheck size={15} aria-hidden="true" /><span>Änderungen werden erst nach deiner Bestätigung veröffentlicht.</span><span>TransferNews · ads.txt manager</span></footer>
        </>}
      </>}
    </main>
    {target && documentState && <CompareDialog current={documentState} target={target} pending={busy === 'rollback'} stale={stale} error={error} onClose={() => setTarget(null)} onRestore={restore} />}
  </div>;
}
