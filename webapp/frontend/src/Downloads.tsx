import { useEffect, useState } from "react";
import { api, type CatalogEntry, type Mode, type SchemaList } from "./api";
import { bytes, fmt } from "./format";
import Sources from "./Sources";

const FILES: { file: string; label: string; hint: string }[] = [
  { file: "dataset.csv", label: "Dataset", hint: "The synthetic table, including the sensitive column" },
  { file: "queries.sql", label: "Queries", hint: "The published AVG queries, one per line" },
  { file: "released_aggregates.csv", label: "Aggregates", hint: "Each query with its answer and group size" },
  { file: "reconstruction.json", label: "Ground truth", hint: "Reconstructed vs. true values, rank check, configuration" },
];

const MODE_TEXT: Record<Mode, { title: string; body: (e: CatalogEntry) => string }> = {
  full: {
    title: "Fully reconstructable",
    body: (e) => `${fmt(e.total_records)} patients — every one of them can be reconstructed.`,
  },
  partial5: {
    title: "5% reconstructable",
    body: (e) =>
      `${fmt(e.total_records)} patients — ${fmt(e.reconstructable_records)} vulnerable ones hidden among ${fmt(e.total_records - e.reconstructable_records)} decoys.`,
  },
  partial: {
    title: "10% reconstructable",
    body: (e) =>
      `${fmt(e.total_records)} patients — ${fmt(e.reconstructable_records)} vulnerable ones hidden among ${fmt(e.total_records - e.reconstructable_records)} decoys.`,
  },
};

export default function Downloads({ list }: { list: SchemaList }) {
  const [catalog, setCatalog] = useState<Record<string, CatalogEntry[]> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.catalog().then(setCatalog, (e) => setError(String(e)));
  }, []);

  return (
    <div className="downloads">
      <section className="hero">
        <h1>Reconstructable datasets</h1>
        <p className="lead">
          Ready-made synthetic datasets for testing anonymisation tools, privacy metrics and
          disclosure-control rules. Each comes with a workload of aggregate
          queries under which the sensitive column is <strong>exactly</strong> recoverable,
          even though every query averages over half of the vulnerable patients.
        </p>
        <p className="muted">
          Each dataset follows its data standard exactly — official variable names, codes and
          derivations — and is built from a {list.demo_n}-patient core found by the optimiser,
          scaled with Hadamard doublings to as many patients as the standard's variables
          support. In the 10% variant, the vulnerable patients are the first rows; decoys never
          satisfy any published query, so deleting them would not change a single published
          average — yet they make up 90% of the table. Every dataset below is checked before
          publication: solving the published averages recovers every vulnerable value exactly.
        </p>
      </section>

      {error && <p className="error">Could not load the catalogue: {error}</p>}
      {!catalog && !error && <p className="muted">Loading catalogue…</p>}

      {catalog &&
        Object.entries(list.categories).map(([key, cat]) => (
          <section key={key} className="category">
            <div className="category-head">
              <h2>{cat.title}</h2>
              <span className="pill">{cat.standard}</span>
            </div>
            <p className="muted small">{cat.description}</p>
            {list.schemas
              .filter((s) => s.category === key)
              .map((s) => (
                <article key={s.id} className="card dataset">
                  <header>
                    <span className="eyebrow">{s.standard}</span>
                    <h3>{s.title} <span className="muted small">· {s.domain}</span></h3>
                    <p className="small">{s.summary}</p>
                    <p className="secret small">
                      Sensitive column: <code>{s.sensitive.name}</code> — {s.sensitive.description} (
                      {fmt(s.sensitive.low)}–{fmt(s.sensitive.high)} {s.sensitive.unit})
                    </p>
                    <Sources schema={s} />
                  </header>
                  <div className="variants">
                    {(catalog[s.id] ?? []).map((e) => (
                      <div key={e.mode} className="variant">
                        <div className="variant-head">
                          <strong>{MODE_TEXT[e.mode].title}</strong>
                          <span className="muted small">
                            {e.columns} columns · {e.queries} queries
                          </span>
                        </div>
                        <p className="small">{MODE_TEXT[e.mode].body(e)}</p>
                        <div className="file-buttons">
                          {FILES.map((f) => (
                            <a key={f.file} className="btn" href={api.fileUrl(s.id, e.n, e.mode, f.file)} title={f.hint} download>
                              {f.label} <small>{bytes(e.files[f.file])}</small>
                            </a>
                          ))}
                          <a className="btn primary" href={api.fileUrl(s.id, e.n, e.mode, "bundle.zip")} download>
                            All files (.zip) <small>{bytes(e.files["bundle.zip"])}</small>
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
          </section>
        ))}
    </div>
  );
}
