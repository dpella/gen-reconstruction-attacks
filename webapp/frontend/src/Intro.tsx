import { useState } from "react";
import { CENSUS, DINUR_NISSIM, LINKAGE, NEW_ATTACKS, NORDSEC, PAPER_TITLE, REPO } from "./links";

export default function Intro() {
  return (
    <div className="intro">
      <section className="hero intro-hero">
        <p className="kicker">Health data · privacy</p>
        <h1>“It's only averages.” Why that is no longer enough.</h1>
        <p className="lead">
          Statistics about large groups of patients are published every day and are widely
          considered safe. This page explains, in six short steps, why that belief breaks down
          as health data becomes more connected — and shows it on realistic examples.
        </p>
      </section>

      <Chapter
        num={1}
        title="Statistics feel safe"
        figure={<CrowdFigure />}
      >
        <p>
          When a hospital or a register publishes “the average blood pressure of 2,000
          patients”, nobody's name is in it and every patient disappears into a crowd. The
          bigger the group, the safer it feels — so publishing <strong>aggregates over many
          people</strong> is the standard way to share health data.
        </p>
      </Chapter>

      <Chapter
        num={2}
        title="That was fine when data stood still"
        figure={<ReportFigure />}
        flip
      >
        <p>
          For decades, statistics came out in a <strong>yearly report</strong>: a few tables,
          chosen in advance and checked by a statistician before publication. Few releases, few
          people asking questions — so it was hard to combine them into anything dangerous.
        </p>
      </Chapter>

      <Chapter
        num={3}
        title="Health data is being unleashed"
        figure={<NetworkFigure />}
      >
        <p>
          That world is ending. The <strong>European Health Data Space (EHDS)</strong> will let
          researchers, companies and public bodies across the EU request health statistics
          through national health-data access bodies — including answers “in anonymised
          statistical format”. Add dashboards, data networks and AI tools, and the number of
          aggregates released about the <em>same</em> patients grows from a handful to
          thousands. This is a huge opportunity for research and care.
        </p>
      </Chapter>

      <Chapter
        num={4}
        title="The scenario: attributes released, one value withheld, averages allowed"
        figure={<ScenarioFigure />}
      >
        <p className="takeaway">
          Withholding a sensitive attribute does not protect it: if quasi-identifiers are
          released and averages of the attribute are allowed, the withheld value of every
          patient can be inferred. 
        </p>
        <p>
          The attack applies whenever a data holder <strong>releases the ordinary attributes</strong>{" "}
          of each patient — age, sex, region, treatment, visit counts, with or without direct
          identifiers such as name or personnummer — but <strong>withholds one sensitive
          attribute</strong>, say HbA1c. For transparency, and so that others can learn about
          the population, it still allows <strong>averages</strong> of that attribute to be
          obtained: by region, by sex, by age band, by treatment.
        </p>
        <p>
          Those ordinary attributes are <em>quasi-identifiers</em>: none names anyone, but
          together they usually single out one person. Combined, the averages can pin down the
          withheld value of <em>every row</em>. Once the sensitive column has been inferred, the
          quasi-identifiers can be used to re-identify patients through{" "}
          <a href={LINKAGE} target="_blank" rel="noopener noreferrer">traditional linkage attacks</a>{" "}
          — even if no personnummer was ever released. 
        </p>
              </Chapter>

      <Chapter
        num={5}
        title="Enough averages reveal everyone"
        figure={<Puzzle />}
        flip
      >
        <p>
          Every average is a small clue. With enough clues, the individual values can be
          worked out exactly — like solving a sudoku. Try it on the right with three patients.
        </p>
        <p>
          This is not a trick but a known mathematical result:{" "}
          <a href={DINUR_NISSIM} target="_blank" rel="noopener noreferrer">
            Dinur and Nissim proved in 2003
          </a>{" "}
          that answering too many statistical questions lets an attacker rebuild the underlying
          data, even if the answers are slightly perturbed. The <strong>US Census Bureau</strong>{" "}
          <a href={CENSUS} target="_blank" rel="noopener noreferrer">
            later ran such an attack on its own published 2010 census tables
          </a>{" "}
          — and changed how it protects its statistics for 2020. And{" "}
          <a href={NEW_ATTACKS} target="_blank" rel="noopener noreferrer">
            new reconstruction attacks keep being developed
          </a>
          .
        </p>
        <p>
          At <strong>DPella</strong> we built a tool that systematises Dinur–Nissim attacks: from
          just the layout of a dataset, it generates data and innocent-looking statistics that
          give every individual away. It powers this website — see the{" "}
          <a href="#datasets">examples of reconstructable datasets</a> it generated — and it is{" "}
          <a href={REPO} target="_blank" rel="noopener noreferrer">open source</a>.
        </p>
      </Chapter>

      <Chapter
        num={6}
        title="Today's safeguards don't scale"
        figure={<CombineFigure />}
      >
        <p>
          Today, releases are protected in two ways, and neither keeps up:
        </p>
        <ul className="bullets">
          <li>
            <strong>Manual review.</strong> An expert checks each table for small groups before
            release. It is slow, and each release is judged <em>on its own</em> — but the risk
            lies in how it <em>combines with everything released before</em>, which no person
            can keep track of.
          </li>
          <li>
            <strong>Heavy anonymisation.</strong> Coarsen or remove so much that nothing could
            leak — which often leaves data too blurry to be useful.
          </li>
        </ul>
      </Chapter>

      <section className="closing">
        <p className="closing-text">
          The method behind this site is described in our paper <PaperLink />.
        </p>
      </section>
    </div>
  );
}

export function PaperLink() {
  return (
    <>
      <em>{PAPER_TITLE}</em>, to appear at{" "}
      <a href={NORDSEC} target="_blank" rel="noopener noreferrer">
        NordSec 2026
      </a>
    </>
  );
}

function Chapter(props: {
  num: number;
  title: string;
  figure: React.ReactNode;
  flip?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className={`chapter${props.flip ? " flip" : ""}`}>
      <div className="chapter-text">
        <h2>
          <span className="step-num">{props.num}</span>
          {props.title}
        </h2>
        {props.children}
      </div>
      <div className="chapter-figure">{props.figure}</div>
    </section>
  );
}

/* ---------- Figures ---------- */

function Person({ x, y, s = 1, className = "" }: { x: number; y: number; s?: number; className?: string }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} className={className}>
      <circle cx="0" cy="-9" r="5" />
      <path d="M-8 8 a8 8 0 0 1 16 0 v2 h-16 z" />
    </g>
  );
}

function CrowdFigure() {
  const people = [];
  for (let r = 0; r < 4; r++) for (let c = 0; c < 6; c++) people.push(<Person key={`${r}-${c}`} x={22 + c * 24} y={36 + r * 32} />);
  return (
    <svg viewBox="0 0 360 170" className="fig" role="img" aria-label="Twenty-four patients summarised as a single average">
      <g className="fig-people">{people}</g>
      <path d="M170 85 h40" className="fig-arrow" markerEnd="url(#arrow)" />
      <rect x="222" y="52" width="126" height="66" rx="12" className="fig-card" />
      <text x="285" y="78" className="fig-small" textAnchor="middle">Average</text>
      <text x="285" y="104" className="fig-big" textAnchor="middle">142 mmHg</text>
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 L10 5 L0 10 z" className="fig-arrowhead" />
        </marker>
      </defs>
    </svg>
  );
}

function ReportFigure() {
  return (
    <svg viewBox="0 0 360 170" className="fig" role="img" aria-label="A yearly report with a few tables, checked by hand">
      <rect x="40" y="18" width="120" height="140" rx="8" className="fig-card" />
      <text x="100" y="42" className="fig-small" textAnchor="middle">Annual report</text>
      {[0, 1, 2].map((i) => (
        <g key={i}>
          <rect x="56" y={56 + i * 30} width="88" height="20" rx="3" className="fig-soft" />
          <rect x="60" y={60 + i * 30} width={30 + i * 18} height="4" rx="2" className="fig-ink" />
          <rect x="60" y={68 + i * 30} width={50 - i * 10} height="4" rx="2" className="fig-ink" />
        </g>
      ))}
      <g transform="translate(262 60)">
        <rect x="-68" y="-30" width="136" height="92" rx="10" className="fig-card" />
        <text x="0" y="-8" className="fig-small" textAnchor="middle">Released</text>
        <text x="0" y="22" className="fig-big" textAnchor="middle">1× / year</text>
        <text x="0" y="46" className="fig-small fig-ok" textAnchor="middle">✓ checked by hand</text>
      </g>
    </svg>
  );
}

function NetworkFigure() {
  const nodes = [
    { x: 60, y: 40, label: "Hospitals" },
    { x: 300, y: 40, label: "Registers" },
    { x: 48, y: 132, label: "Researchers" },
    { x: 312, y: 132, label: "Companies" },
    { x: 180, y: 158, label: "AI & apps" },
  ];
  return (
    <svg viewBox="0 0 360 180" className="fig" role="img" aria-label="Many parties connected through the European Health Data Space, exchanging statistics">
      {nodes.map((n) => (
        <line key={n.label} x1="180" y1="84" x2={n.x} y2={n.y} className="fig-flow" />
      ))}
      <circle cx="180" cy="84" r="38" className="fig-hub" />
      <text x="180" y="81" textAnchor="middle" className="fig-hub-text">EHDS</text>
      <text x="180" y="97" textAnchor="middle" className="fig-hub-sub">on request</text>
      {nodes.map((n) => (
        <g key={n.label}>
          <rect x={n.x - 42} y={n.y - 13} width="84" height="26" rx="13" className="fig-card" />
          <text x={n.x} y={n.y + 4} textAnchor="middle" className="fig-small">{n.label}</text>
        </g>
      ))}
    </svg>
  );
}

function ScenarioFigure() {
  // The revealed record is the last row, level with the arrow pointing to it.
  const rows = [["61", "M", "Uppsala", "48"], ["47", "F", "Skåne", "88"], ["54", "F", "Skåne", "71"]];
  return (
    <svg viewBox="0 0 360 200" className="fig" role="img"
      aria-label="Released attributes and allowed averages together reveal each patient's withheld value">
      <text x="10" y="16" className="fig-small">Released attributes</text>
      <text x="200" y="16" className="fig-small fig-danger">Withheld</text>
      {["age", "sex", "region"].map((h, j) => (
        <text key={h} x={14 + j * 58} y="36" className="fig-small">{h}</text>
      ))}
      <text x="200" y="36" className="fig-small">HbA1c</text>
      {rows.map((r, i) => (
        <g key={i}>
          <rect x="8" y={44 + i * 26} width="176" height="22" rx="4" className={i === rows.length - 1 ? "fig-highlight" : "fig-soft"} />
          {r.slice(0, 3).map((v, j) => (
            <text key={j} x={14 + j * 58} y={59 + i * 26} className="fig-cell">{v}</text>
          ))}
          <rect x="194" y={44 + i * 26} width="52" height="22" rx="4" className="fig-hidden" />
          <text x="220" y={59 + i * 26} textAnchor="middle" className="fig-cell fig-danger">?</text>
        </g>
      ))}
      <rect x="8" y="132" width="246" height="40" rx="8" className="fig-card" />
      <text x="16" y="148" className="fig-small">Allowed: mean HbA1c by sex, by region,</text>
      <text x="16" y="164" className="fig-small">by age band, … (each = half the patients)</text>
      <path d="M252 104 h26" className="fig-arrow" markerEnd="url(#arrow2)" />
      <rect x="282" y="72" width="72" height="64" rx="10" className="fig-card fig-danger-card" />
      <text x="318" y="92" textAnchor="middle" className="fig-small">54, F, Skåne</text>
      <text x="318" y="114" textAnchor="middle" className="fig-big fig-danger">71</text>
      <text x="318" y="129" textAnchor="middle" className="fig-small">revealed</text>
      <text x="8" y="192" className="fig-small">Exact value recovery.</text>
      <defs>
        <marker id="arrow2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0 L10 5 L0 10 z" className="fig-arrowhead" />
        </marker>
      </defs>
    </svg>
  );
}

function CombineFigure() {
  return (
    <svg viewBox="0 0 360 170" className="fig" role="img" aria-label="Three releases each pass review on their own, but together they reveal individuals">
      {["Release A", "Release B", "Release C"].map((r, i) => (
        <g key={r} transform={`translate(${12 + i * 82} 40)`}>
          <rect width="66" height="80" rx="8" className="fig-card" />
          <text x="33" y="22" textAnchor="middle" className="fig-small">{r}</text>
          <rect x="12" y="32" width="42" height="4" rx="2" className="fig-ink" />
          <rect x="12" y="42" width="30" height="4" rx="2" className="fig-ink" />
          <text x="33" y="68" textAnchor="middle" className="fig-ok fig-mid">✓ safe</text>
          {i < 2 && <text x="74" y="46" textAnchor="middle" className="fig-mid">+</text>}
        </g>
      ))}
      <text x="258" y="86" textAnchor="middle" className="fig-mid">=</text>
      <g transform="translate(272 40)">
        <rect width="80" height="80" rx="8" className="fig-card fig-danger-card" />
        <Person x={40} y={40} s={1.3} className="fig-danger" />
        <text x="40" y="70" textAnchor="middle" className="fig-danger fig-small">revealed</text>
      </g>
    </svg>
  );
}

const PATIENTS = [
  { name: "Anna", value: 120 },
  { name: "Björn", value: 140 },
  { name: "Cecilia", value: 160 },
];
const GROUPS: [number, number][] = [[0, 1], [1, 2], [0, 2]];

function Puzzle() {
  const [solved, setSolved] = useState(false);
  const avg = ([a, b]: [number, number]) => (PATIENTS[a].value + PATIENTS[b].value) / 2;
  return (
    <div className="puzzle">
      <div className="puzzle-people">
        {PATIENTS.map((p) => (
          <div key={p.name} className={`puzzle-person${solved ? " solved" : ""}`}>
            <svg viewBox="-12 -16 24 28" width="34" height="40" aria-hidden className="fig-people">
              <Person x={0} y={0} />
            </svg>
            <span>{p.name}</span>
            <strong>{solved ? p.value : "?"}</strong>
          </div>
        ))}
      </div>
      <div className="puzzle-clues">
        <span className="muted small">Published averages (blood pressure, mmHg):</span>
        {GROUPS.map((g) => (
          <div key={g.join()} className="clue">
            {PATIENTS[g[0]].name} & {PATIENTS[g[1]].name}: <strong>{avg(g)}</strong>
          </div>
        ))}
      </div>
      {solved ? (
        <p className="small puzzle-explain">
          Add Anna & Björn and Anna & Cecilia, subtract Björn & Cecilia:{" "}
          <br />
          Anna = {avg(GROUPS[0])} + {avg(GROUPS[2])} − {avg(GROUPS[1])} = <strong>{PATIENTS[0].value}</strong>. The
          others follow the same way. Each average covered two of the three patients — yet
          together they give away all three.
        </p>
      ) : (
        <p className="small muted puzzle-explain">Each average covers most of the group. Can you work out each person's value?</p>
      )}
      <button className="primary" onClick={() => setSolved((s) => !s)}>
        {solved ? "Hide the answer" : "Reveal the answer"}
      </button>
    </div>
  );
}
