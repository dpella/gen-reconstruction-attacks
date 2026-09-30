import { useEffect, useState } from "react";
import { api, type SchemaList } from "./api";
import Walkthrough from "./Walkthrough";
import Downloads from "./Downloads";
import Intro, { PaperLink } from "./Intro";
import { REPO } from "./links";
import logo from "./assets/dpella-logo.png";

type Tab = "intro" | "how" | "datasets";
const TABS: { id: Tab; label: string }[] = [
  { id: "intro", label: "Why it matters" },
  { id: "how", label: "How it works" },
  { id: "datasets", label: "Examples of reconstructable datasets" },
];

function tabFromHash(): Tab {
  const h = window.location.hash.slice(1);
  return h === "how" || h === "datasets" ? h : "intro";
}

export default function App() {
  const [tab, setTab] = useState<Tab>(tabFromHash);
  const [schemas, setSchemas] = useState<SchemaList | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.schemas().then(setSchemas, (e) => setError(String(e)));
    const onHash = () => setTab(tabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = (t: Tab) => {
    window.location.hash = t === "intro" ? "" : t;
    setTab(t);
    window.scrollTo({ top: 0 });
  };

  return (
    <>
      <header className="topbar">
        <div className="wrap topbar-inner">
          <a className="brand" href="#" onClick={(e) => { e.preventDefault(); go("intro"); }}>
            <img src={logo} alt="DPella" className="brand-logo" />
            <span className="brand-name">Reconstruction attacks on health statistics</span>
          </a>
          <nav className="tabs" role="tablist">
            {TABS.map((t) => (
              <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => go(t.id)}>
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="wrap">
        {error && <p className="error">Could not reach the server: {error}</p>}
        {!schemas && !error && tab !== "intro" && <p className="muted">Loading…</p>}
        {tab === "intro" && <Intro />}
        {schemas && tab === "how" && <Walkthrough list={schemas} onDatasets={() => go("datasets")} />}
        {schemas && tab === "datasets" && <Downloads list={schemas} />}
      </main>

      <footer className="footer">
        <div className="wrap">
          <img src={logo} alt="DPella" className="footer-logo" />
          <span>
            Built on the paper <PaperLink /> ·{" "}
            <a href={REPO} target="_blank" rel="noopener noreferrer">source code</a> · All data on
            this site is synthetic — no real patient is described.
          </span>
        </div>
      </footer>
    </>
  );
}
