import { Assignment } from './assignment.model';

export interface Project {
  id: number;
  name: string;
  project_manager_id: number;
  project_manager_name: string | null; // Backend sends name, can be null if manager not found (though API should prevent this)
  budget: string | null; // Backend sends Decimal as string
  assignments?: Assignment[]; // Optional, for views that load project with its assignments
}
