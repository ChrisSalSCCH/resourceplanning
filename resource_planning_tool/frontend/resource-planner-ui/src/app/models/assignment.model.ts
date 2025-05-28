export interface Assignment {
  id: number;
  project_id: number;
  project_name: string | null; // Backend sends name
  person_id: number;
  person_name: string | null; // Backend sends name
  assigned_hours: number;
  timeline_start: string; // ISO date string (YYYY-MM-DD)
  timeline_end: string;   // ISO date string (YYYY-MM-DD)
}
