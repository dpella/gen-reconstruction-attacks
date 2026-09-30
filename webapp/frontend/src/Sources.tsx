import type { Schema } from "./api";

export default function Sources({ schema }: { schema: Schema }) {
  return (
    <p className="sources small">
      Schema source:{" "}
      {schema.sources.map((src, i) => (
        <span key={src.url}>
          {i > 0 && " · "}
          <a href={src.url} target="_blank" rel="noopener noreferrer">
            {src.label}
          </a>
        </span>
      ))}
    </p>
  );
}
