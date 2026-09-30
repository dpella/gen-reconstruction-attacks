import type { SchemaList } from "./api";

interface Props {
  list: SchemaList;
  selected: string;
  onSelect: (id: string) => void;
}

export default function SchemaPicker({ list, selected, onSelect }: Props) {
  return (
    <div className="categories">
      {Object.entries(list.categories).map(([key, cat]) => (
        <section key={key} className="category">
          <div className="category-head">
            <h3>{cat.title}</h3>
            <span className="pill">{cat.standard}</span>
          </div>
          <p className="muted small">{cat.description}</p>
          <div className="cards">
            {list.schemas
              .filter((s) => s.category === key && s.featured)
              .map((s) => (
                <button
                  key={s.id}
                  className={`card schema-card${s.id === selected ? " selected" : ""}`}
                  aria-pressed={s.id === selected}
                  onClick={() => onSelect(s.id)}
                >
                  <span className="eyebrow">{s.standard}</span>
                  <strong>{s.title}</strong>
                  <span className="muted small">{s.domain}</span>
                  <span className="secret small">
                    Withheld: <code>{s.sensitive.name}</code> — {s.sensitive.description}
                  </span>
                </button>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
