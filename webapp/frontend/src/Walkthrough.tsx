import { useEffect, useMemo, useState } from "react";
import { api, type Result, type SchemaList } from "./api";
import SchemaPicker from "./SchemaPicker";
import Sources from "./Sources";
import { describeQuery, fmt } from "./format";

interface Props {
  list: SchemaList;
  onDatasets: () => void;
}

export default function Walkthrough({ list, onDatasets }: Props) {
  const [schemaId, setSchemaId] = useState((list.schemas.find((s) => s.featured) ?? list.schemas[0]).id);
  const [result, setResult] = useState<Result | null>(null);
  const [active, setActive] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [showSql, setShowSql] = useState(false);

  useEffect(() => {
    let live = true;
    setResult(null);
    setRevealed(false);
    setActive(0);
    api.demo(schemaId).then((r) => live && setResult(r));
    return () => { live = false; };
  }, [schemaId]);

  const schema = list.schemas.find((s) => s.id === schemaId)!;
  const n = list.demo_n;

  return (
    <div className="walkthrough">
      <section className="hero">
        <h1>See the attack</h1>
        <p className="lead">
          Pick a dataset. First, its de-identified records are released; later, aggregates — here,
          averages — of one sensitive attribute can be queried. Each release looks safe on its own
          — see how, together, they reveal that attribute for all {n} synthetic patients.
        </p>
      </section>

      <Step num={1} title="Pick a kind of health data">
        <SchemaPicker list={list} selected={schemaId} onSelect={setSchemaId} />
      </Step>

      {!result ? (
        <p className="muted">Loading the {schema.title.toLowerCase()} example…</p>
      ) : (
        <>
          <Step
            num={2}
            title="De-identified records, a sensitive attribute, and the aggregates"
            intro={
              <>
                {schema.story} The sensitive column, <strong>{result.sensitive.label}</strong>, is
                never released. Select an average to see who it covers.
              </>
            }
          >
            <Sources schema={schema} />
            <div className="split">
              <QueryList result={result} active={active} onActive={setActive} showSql={showSql} />
              <DataTable result={result} active={active} revealed={revealed} />
            </div>
            <label className="toggle">
              <input type="checkbox" checked={showSql} onChange={(e) => setShowSql(e.target.checked)} />
              Show the SQL queries
            </label>
          </Step>

          <Step
            num={3}
            title="The attack: solve the equations"
            intro={
              <>
                Because the de-identified records are released, anyone can tell which patients each
                average covers — so each average is one equation. {n} independent equations for {n}{" "}
                unknowns have exactly one solution.
              </>
            }
          >
            <Equation result={result} active={active} />
            <div className="attack-row">
              <Matrix result={result} active={active} onActive={setActive} />
              <div className="attack-side">
                <p>
                  Rows are published averages, columns are patients: every row covers exactly half
                  of them.
                </p>
                <button className="primary" onClick={() => setRevealed((v) => !v)}>
                  {revealed ? "Hide the reconstruction" : `Solve the ${n} equations`}
                </button>
                {revealed && (
                  <p className="success">
                    All {result.summary.reconstructable_records} sensitive values of{" "}
                    <strong>{result.sensitive.label}</strong> inferred exactly (largest error{" "}
                    {result.summary.max_abs_error.toExponential(0)} {result.sensitive.unit}) —
                    see the revealed column in the table above.
                  </p>
                )}
              </div>
            </div>
          </Step>

          <Step num={4} title="Scaling up">
            <Scaling result={result} onDatasets={onDatasets} />
          </Step>
        </>
      )}
    </div>
  );
}

function Step(props: { num: number; title: string; intro?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="step">
      <h2>
        <span className="step-num">{props.num}</span>
        {props.title}
      </h2>
      {props.intro && <p className="step-intro">{props.intro}</p>}
      {props.children}
    </section>
  );
}

function QueryList(props: { result: Result; active: number; onActive: (i: number) => void; showSql: boolean }) {
  const { result, active, onActive, showSql } = props;
  const s = result.sensitive;
  const labels = useMemo(() => new Map(result.columns.map((c) => [c.name, c.label || c.name])), [result]);
  return (
    <div className="panel">
      <div className="panel-title">Published averages</div>
      <ol className="queries">
        {result.queries.map((q, i) => (
          <li key={i} id={`avg-${i + 1}`}>
            <button
              className={i === active ? "active" : ""}
              onClick={() => onActive(i)}
              onMouseEnter={() => onActive(i)}
            >
              <span className="q-num">{i + 1}</span>
              <span className="q-body">
                <span className="q-text">
                  {showSql ? <code>{q.sql}</code> : <>Average {s.label} where {describeQuery(q.sql, labels)}</>}
                </span>
                <span className="q-answer">
                  {fmt(q.answer)} <small>{s.unit}</small>
                  <small className="muted"> · {q.matched} patients</small>
                </span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

function DataTable({ result, active, revealed }: { result: Result; active: number; revealed: boolean }) {
  // Show the released (queried) columns and the hidden one; the downloads
  // also carry the standard's derived columns (IDs, dates, groupings, ...).
  // The hidden column goes last; CSS pins it to the right edge so it stays
  // in view even when a wide table scrolls.
  const sensIdx = result.header.indexOf(result.sensitive.name);
  const shown = useMemo(
    () => [...result.query_columns.map((h) => result.header.indexOf(h)).filter((j) => j >= 0 && j !== sensIdx), sensIdx],
    [result, sensIdx],
  );
  const row = result.matrix[active] ?? "";
  const cols = useMemo(() => new Map(result.columns.map((c) => [c.name, c])), [result]);
  return (
    <div className="panel">
      <div className="panel-title">
        The table ({result.preview_rows.length} synthetic patients): de-identified records, and the
        sensitive column
      </div>
      <div className="table-scroll">
        <table className="data">
          <thead>
            <tr>
              <th>#</th>
              {shown.map((j) => {
                const h = result.header[j];
                const c = cols.get(h);
                return (
                  <th
                    key={h}
                    className={j === sensIdx ? "sensitive" : ""}
                    title={j === sensIdx ? `${h}: ${result.sensitive.description}` : `${h}: ${c?.description ?? ""} — ${c?.detail ?? ""}`}
                  >
                    {j === sensIdx ? result.sensitive.label : c?.label || h}
                    {j === sensIdx && " 🔒"}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {result.preview_rows.map((r, i) => (
              <tr key={i} className={row[i] === "1" ? "in-group" : ""}>
                <td className="muted">{i + 1}</td>
                {shown.map((j) =>
                  j === sensIdx ? (
                    <td key={j} className={`sensitive ${revealed ? "revealed" : ""}`} style={{ transitionDelay: `${i * 40}ms` }}>
                      {revealed ? (
                        <span title={`true value ${result.ground_truth[i]}`}>
                          {result.reconstructed[i].toFixed(result.sensitive.decimals ?? 0)}{" "}
                          {result.reconstructed[i] === result.ground_truth[i] && "✓"}
                        </span>
                      ) : (
                        <span className="masked">•••</span>
                      )}
                    </td>
                  ) : (
                    <td key={j}>{r[j]}</td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">
        Highlighted rows are the patients included in the selected average. Hover a column
        name for its official variable name and definition.
      </p>
    </div>
  );
}

function Equation({ result, active }: { result: Result; active: number }) {
  const q = result.queries[active];
  const members = [...(result.matrix[active] ?? "")].flatMap((c, i) => (c === "1" ? [i + 1] : []));
  return (
    <div className="equation" aria-live="polite">
      <span className="muted small">Selected average #{active + 1} as an equation:</span>
      <div className="eq">
        ( {members.map((m, k) => (
          <span key={m}>
            {k > 0 && " + "}
            <var>x<sub>{m}</sub></var>
          </span>
        ))} ) ÷ {members.length} = <strong>{fmt(q.answer, 4)}</strong>
      </div>
    </div>
  );
}

function Matrix({ result, active, onActive }: { result: Result; active: number; onActive: (i: number) => void }) {
  const n = result.matrix[0]?.length ?? 0;
  return (
    <div className="matrix" style={{ gridTemplateColumns: `repeat(${n}, 1fr)` }} role="grid" aria-label="Which patients each average covers">
      {result.matrix.map((row, i) =>
        [...row].map((c, j) => (
          <div
            key={`${i}-${j}`}
            className={`cell${c === "1" ? " on" : ""}${i === active ? " active" : ""}`}
            onMouseEnter={() => onActive(i)}
            onClick={() => onActive(i)}
          />
        )),
      )}
    </div>
  );
}

function Scaling({ result, onDatasets }: { result: Result; onDatasets: () => void }) {
  const M = result.matrix;
  const n = M.length;
  const flip = (r: string) => [...r].map((c) => (c === "1" ? "0" : "1")).join("");
  // Sylvester doubling only stays solvable when the base contains the all-ones
  // row (the average over everyone). As in the CLI (Hadamard.generate_new_table),
  // it replaces the negation query (`col = '0'`): that query plus its `col = '1'`
  // partner already sum to the all-ones row, so nothing is lost.
  const base = useMemo(() => {
    const negation = M.map((r) => M.includes(flip(r))).lastIndexOf(true);
    const drop = negation === -1 ? M.length - 1 : negation;
    return ["1".repeat(n), ...M.filter((_, i) => i !== drop)];
  }, [M, n]);
  const doubled = useMemo(
    () => [...base.map((r) => r + r), ...base.map((r) => r + flip(r))],
    [base],
  );
  const [hover, setHover] = useState<number | null>(null);
  return (
    <div className="scaling">
      <div>
        <p>
          The same attack principles apply at scale: with more aggregates, bigger datasets can be
          reconstructed. Our tool first finds averages that pin down {n} patients. To reach more
          patients, it doesn't start over: it <strong>doubles</strong> both the patients and the
          averages, to {2 * n}, {4 * n}, {8 * n} patients and beyond, and every doubled set can
          still be solved exactly.
        </p>
        <div className="info" role="note">
          <svg className="info-icon" viewBox="0 0 20 20" aria-hidden>
            <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" strokeWidth="1.8" />
            <rect x="9.1" y="8.5" width="1.8" height="6" rx="0.9" fill="currentColor" />
            <circle cx="10" cy="5.8" r="1.1" fill="currentColor" />
          </svg>
          <span>
            The highlighted row is the overall average of all patients, often seen as the safest
            statistic to publish. Here, it is what makes the doubling work.
          </span>
        </div>
        <p>
          The{" "}
          <a href="#datasets" onClick={(e) => { e.preventDefault(); onDatasets(); }}>
            examples of reconstructable datasets
          </a>{" "}
          are built exactly this way.
        </p>
      </div>
      <figure className="doubling">
        <div className="doubling-grid" onMouseLeave={() => setHover(null)}>
          <div className="matrix small" style={{ gridTemplateColumns: `repeat(${doubled.length}, 1fr)` }} aria-hidden>
            {doubled.map((row, i) =>
              [...row].map((c, j) => {
                const ones = i === 0;
                // The top-left block is the matrix our tool found for the first n patients.
                const original = !ones && i < n && j < n;
                return (
                  <div
                    key={`${i}-${j}`}
                    className={`cell${c === "1" ? " on" : ""}${ones ? " ones" : ""}${original ? " original" : ""}${ones && hover === i ? " hovered" : ""}`}
                    onMouseEnter={() => setHover(i)}
                  />
                );
              }),
            )}
          </div>
          {hover === 0 && (
            <div className="grid-tip" style={{ top: `${(1 / doubled.length) * 100}%` }}>
              The overall average of all {2 * n} patients
            </div>
          )}
        </div>
        <figcaption className="muted small">
          <span className="swatch original" aria-hidden /> the averages our tool found for {n}{" "}
          patients · <span className="swatch ones" aria-hidden /> the overall average. Doubled to{" "}
          {2 * n} patients — still exactly solvable.
        </figcaption>
      </figure>
    </div>
  );
}
