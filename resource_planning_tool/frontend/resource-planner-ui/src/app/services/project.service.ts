import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Project } from '../models/project.model';

@Injectable({
  providedIn: 'root'
})
export class ProjectService {
  private apiUrl = 'http://localhost:5000/api'; // Base API URL

  constructor(private http: HttpClient) { }

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.apiUrl}/projects`);
  }

  getProject(id: number): Observable<Project> {
    return this.http.get<Project>(`${this.apiUrl}/projects/${id}`);
  }

  // For addProject, backend expects: name, project_manager_id, budget (optional)
  addProject(project: Omit<Project, 'id' | 'project_manager_name' | 'assignments'>): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/projects`, project);
  }

  // For updateProject, backend expects partial data of: name, project_manager_id, budget
  updateProject(id: number, project: Partial<Omit<Project, 'id' | 'project_manager_name' | 'assignments'>>): Observable<Project> {
    return this.http.put<Project>(`${this.apiUrl}/projects/${id}`, project);
  }

  deleteProject(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/projects/${id}`);
  }

  getProjectsByManager(managerId: number): Observable<Project[]> {
    // This endpoint returns projects with their assignments populated
    return this.http.get<Project[]>(`${this.apiUrl}/project_manager/${managerId}/projects`);
  }
}
