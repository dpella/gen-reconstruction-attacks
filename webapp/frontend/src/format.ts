/** Turn a generated `SELECT AVG(s) FROM table WHERE …;` into plain language. */
export function describeQuery(sql: string, labels: Map<string, string> = new Map()): string {
  const name = (c: string) => labels.get(c) ?? c;
  const where = sql.match(/WHERE (.*);$/)?.[1];
  if (!where) return "all records";

  const eq = where.match(/^([\p{L}\p{N}_]+) = '([^']*)'$/u);
  if (eq) return `${name(eq[1])} is ${eq[2]}`;

  const ranges = [...where.matchAll(/\(([\p{L}\p{N}_]+) >= ([\d.]+) AND [\p{L}\p{N}_]+ < ([\d.]+)\)/gu)];
  if (ranges.length) {
    const col = ranges[0][1];
    const parts = ranges.map((r) => `${r[2]}–${r[3]}`);
    const list = parts.length > 1 ? `${parts.slice(0, -1).join(", ")} or ${parts.at(-1)}` : parts[0];
    return `${name(col)} is in ${list}`;
  }
  return where;
}

export function fmt(x: number, digits = 2): string {
  return x.toLocaleString("en-US", { maximumFractionDigits: digits });
}

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 ** 2).toFixed(1)} MB`;
}
