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
          Pick a dataset and look at what is released about {n} synthetic patients — their
          attributes, and averages of one withheld value — then solve for it.
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
            title="Released attributes, a withheld value, and the averages"
            intro={
              <>
                {schema.story} The <strong>{result.sensitive.label}</strong> column itself is never
                released. Select an average to see who it covers.
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
                Because the attributes are released, anyone can tell which patients each average
                covers — so each average is one equation. {n} independent equations for {n}{" "}
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
                    All {result.summary.reconstructable_records} withheld values of{" "}
                    <strong>{result.sensitive.label}</strong> recovered exactly (largest error{" "}
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
          <li key={i}>
            <button
              className={i === active ? "active" : ""}
              onClick={() => onActive(i)}
              onMouseEnter={() => onActive(i)}
            >
              <span className="q-text">
                {showSql ? <code>{q.sql}</code> : <>Average {s.label} where {describeQuery(q.sql, labels)}</>}
              </span>
              <span className="q-answer">
                {fmt(q.answer)} <small>{s.unit}</small>
                <small className="muted"> · {q.matched} patients</small>
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
        The table ({result.preview_rows.length} synthetic patients): released attributes, and the withheld
        column
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
  const doubled = useMemo(() => {
    const flip = (r: string) => [...r].map((c) => (c === "1" ? "0" : "1")).join("");
    return [...M.map((r) => r + r), ...M.map((r) => r + flip(r))];
  }, [M]);
  return (
    <div className="scaling">
      <p>
        The same attack principles apply at scale: with more aggregates, bigger datasets can be
        reconstructed. See the{" "}
        <a href="#datasets" onClick={(e) => { e.preventDefault(); onDatasets(); }}>
          examples of reconstructable datasets
        </a>
        .
      </p>
      <figure className="doubling">
        <div className="matrix small" style={{ gridTemplateColumns: `repeat(${doubled.length}, 1fr)` }} aria-hidden>
          {doubled.map((row, i) =>
            [...row].map((c, j) => {
              const flipped = i >= M.length && j >= M.length;
              return <div key={`${i}-${j}`} className={`cell${c === "1" ? " on" : ""}${flipped ? " flipped" : ""}`} />;
            }),
          )}
        </div>
        <figcaption className="muted small">
          The {M.length}-patient grid grown to {2 * M.length} patients — still exactly solvable.
        </figcaption>
      </figure>
    </div>
  );
}
