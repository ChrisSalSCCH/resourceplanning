import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Assignment } from '../models/assignment.model';

@Injectable({
  providedIn: 'root'
})
export class AssignmentService {
  private apiUrlBase = 'http://localhost:5000/api'; // Base API URL

  constructor(private http: HttpClient) { }

  getAssignmentsForProject(projectId: number): Observable<Assignment[]> {
    return this.http.get<Assignment[]>(`${this.apiUrlBase}/projects/${projectId}/assignments`);
  }

  getAssignmentsForPerson(personId: number): Observable<Assignment[]> {
    return this.http.get<Assignment[]>(`${this.apiUrlBase}/persons/${personId}/assignments`);
  }

  // For addAssignment, backend expects: project_id, person_id, assigned_hours, timeline_start, timeline_end
  addAssignment(assignment: Omit<Assignment, 'id' | 'project_name' | 'person_name'>): Observable<Assignment> {
    return this.http.post<Assignment>(`${this.apiUrlBase}/assignments`, assignment);
  }

  // For updateAssignment, backend expects partial data of: project_id, person_id, assigned_hours, timeline_start, timeline_end
  updateAssignment(id: number, assignment: Partial<Omit<Assignment, 'id' | 'project_name' | 'person_name'>>): Observable<Assignment> {
    return this.http.put<Assignment>(`${this.apiUrlBase}/assignments/${id}`, assignment);
  }

  deleteAssignment(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrlBase}/assignments/${id}`);
  }
}
