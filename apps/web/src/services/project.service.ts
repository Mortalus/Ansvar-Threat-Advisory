import { apiClient } from './api.client';
import { z } from 'zod';

// Validation schemas
const projectSchema = z.object({
  id: z.string(),
  name: z.string().min(1, 'Project name is required'),
  description: z.string().optional(),
  client_id: z.string().optional(),
  created_by: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  metadata: z.record(z.any()).optional(),
  status: z.enum(['active', 'archived', 'draft']).default('active'),
});

const sessionSchema = z.object({
  id: z.string(),
  project_id: z.string(),
  name: z.string(),
  pipeline_id: z.string().optional(),
  status: z.enum(['pending', 'running', 'completed', 'failed']).default('pending'),
  results: z.any().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type Project = z.infer<typeof projectSchema>;
export type Session = z.infer<typeof sessionSchema>;

interface CreateProjectData {
  name: string;
  description?: string;
  metadata?: Record<string, any>;
}

interface CreateSessionData {
  name: string;
  project_id: string;
}

class ProjectService {
  /**
   * Get all projects with defensive error handling
   */
  async getProjects(): Promise<Project[]> {
    try {
      const response = await apiClient.get<Project[]>('/api/projects');
      
      // Validate each project
      return response.map(project => projectSchema.parse(project));
    } catch (error: any) {
      console.error('Failed to fetch projects:', error);
      
      // Return empty array on error to prevent UI crash
      if (error.code === 'OFFLINE') {
        // Try to load from local storage if offline
        const cached = localStorage.getItem('cached_projects');
        if (cached) {
          try {
            return JSON.parse(cached);
          } catch {
            return [];
          }
        }
      }
      
      throw error;
    }
  }

  /**
   * Get project by ID
   */
  async getProject(id: string): Promise<Project> {
    try {
      const response = await apiClient.get<Project>(`/api/projects/${id}`);
      return projectSchema.parse(response);
    } catch (error: any) {
      console.error(`Failed to fetch project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create new project
   */
  async createProject(data: CreateProjectData): Promise<Project> {
    try {
      // Validate input
      const validated = z.object({
        name: z.string().min(1).max(255),
        description: z.string().max(1000).optional(),
        metadata: z.record(z.any()).optional(),
      }).parse(data);

      const response = await apiClient.post<Project>('/api/projects', validated);
      const project = projectSchema.parse(response);

      // Update cache
      this.updateProjectCache(project);

      return project;
    } catch (error: any) {
      console.error('Failed to create project:', error);
      
      if (error instanceof z.ZodError) {
        throw new Error(error.errors[0].message);
      }
      
      throw error;
    }
  }

  /**
   * Update project
   */
  async updateProject(id: string, data: Partial<CreateProjectData>): Promise<Project> {
    try {
      const response = await apiClient.put<Project>(`/api/projects/${id}`, data);
      const project = projectSchema.parse(response);

      // Update cache
      this.updateProjectCache(project);

      return project;
    } catch (error: any) {
      console.error(`Failed to update project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete project
   */
  async deleteProject(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/projects/${id}`);
      
      // Remove from cache
      this.removeFromProjectCache(id);
    } catch (error: any) {
      console.error(`Failed to delete project ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get project sessions
   */
  async getProjectSessions(projectId: string): Promise<Session[]> {
    try {
      const response = await apiClient.get<Session[]>(`/api/projects/${projectId}/sessions`);
      return response.map(session => sessionSchema.parse(session));
    } catch (error: any) {
      console.error(`Failed to fetch sessions for project ${projectId}:`, error);
      throw error;
    }
  }

  /**
   * Create project session
   */
  async createSession(data: CreateSessionData): Promise<Session> {
    try {
      // Validate input
      const validated = z.object({
        name: z.string().min(1).max(255),
        project_id: z.string().uuid(),
      }).parse(data);

      const response = await apiClient.post<Session>(
        `/api/projects/${data.project_id}/sessions`,
        validated
      );
      
      return sessionSchema.parse(response);
    } catch (error: any) {
      console.error('Failed to create session:', error);
      
      if (error instanceof z.ZodError) {
        throw new Error(error.errors[0].message);
      }
      
      throw error;
    }
  }

  /**
   * Delete session
   */
  async deleteSession(projectId: string, sessionId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/projects/${projectId}/sessions/${sessionId}`);
    } catch (error: any) {
      console.error(`Failed to delete session ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Export project data
   */
  async exportProject(id: string, format: 'json' | 'pdf' | 'docx' = 'json'): Promise<Blob> {
    try {
      const response = await apiClient.get<Blob>(
        `/api/projects/${id}/export`,
        {
          params: { format },
          responseType: 'blob',
        }
      );
      
      return response;
    } catch (error: any) {
      console.error(`Failed to export project ${id}:`, error);
      throw error;
    }
  }

  // Cache management

  private updateProjectCache(project: Project): void {
    try {
      const cached = localStorage.getItem('cached_projects');
      let projects: Project[] = cached ? JSON.parse(cached) : [];
      
      // Update or add project
      const index = projects.findIndex(p => p.id === project.id);
      if (index >= 0) {
        projects[index] = project;
      } else {
        projects.push(project);
      }
      
      localStorage.setItem('cached_projects', JSON.stringify(projects));
    } catch (error) {
      console.error('Failed to update project cache:', error);
    }
  }

  private removeFromProjectCache(id: string): void {
    try {
      const cached = localStorage.getItem('cached_projects');
      if (cached) {
        let projects: Project[] = JSON.parse(cached);
        projects = projects.filter(p => p.id !== id);
        localStorage.setItem('cached_projects', JSON.stringify(projects));
      }
    } catch (error) {
      console.error('Failed to remove from project cache:', error);
    }
  }
}

export const projectService = new ProjectService();