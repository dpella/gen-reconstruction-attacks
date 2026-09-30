export type Mode = "full" | "partial" | "partial5";

export interface Column {
  name: string;
  kind: "numeric" | "categorical";
  description: string;
  detail: string;
  label: string;
}

export interface Category {
  title: string;
  standard: string;
  description: string;
}

export interface Schema {
  id: string;
  category: string;
  title: string;
  standard: string;
  domain: string;
  summary: string;
  story: string;
  sensitive: { name: string; low: number; high: number; unit: string; description: string };
  sources: { label: string; url: string }[];
  download_n: number;
  featured: boolean;
  demo_columns: Column[];
}

export interface SchemaList {
  demo_n: number;
  modes: Record<Mode, number>;
  categories: Record<string, Category>;
  schemas: Schema[];
}

export interface Result {
  schema: string;
  n: number;
  mode: Mode;
  summary: {
    total_records: number;
    reconstructable_records: number;
    decoy_records: number;
    queries: number;
    matrix_rank: number;
    full_rank: boolean;
    max_abs_error: number;
    records_per_query: number;
  };
  sensitive: { name: string; unit: string; description: string; decimals: number; label: string };
  columns: Column[];
  query_columns: string[];
  header: string[];
  preview_rows: string[][];
  queries: { sql: string; matched: number; answer: number }[];
  matrix: string[];
  ground_truth: number[];
  reconstructed: number[];
}

export interface CatalogEntry {
  n: number;
  mode: Mode;
  total_records: number;
  reconstructable_records: number;
  queries: number;
  columns: number;
  files: Record<string, number>;
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  schemas: () => get<SchemaList>("/api/schemas"),
  demo: (id: string) => get<Result>(`/api/demo/${id}`),
  catalog: () => get<Record<string, CatalogEntry[]>>("/api/catalog"),
  fileUrl: (id: string, n: number, mode: Mode, file: string) =>
    `/api/results/${id}/${n}/${mode}/${file}`,
};
