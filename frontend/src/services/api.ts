import axios from 'axios';
import { 
  Project, 
  ProjectSummary, 
  Model, 
  ModelSummary, 
  Column, 
  ColumnWithRelations, 
  UserCorrection,
  ModelWithLineage,
  ColumnWithLineage,
  ColumnLineage,
  RelatedModel,
  ColumnLineageLink
} from '../types';

// Clean any quotation marks from the API URL
const rawApiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_URL = rawApiUrl.replace(/"/g, '');

console.log('Using API URL:', API_URL);

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Projects
export const getProjects = async (): Promise<Project[]> => {
  const response = await api.get<Project[]>('/api/projects');
  return response.data;
};

export const getProjectSummaries = async (): Promise<ProjectSummary[]> => {
  const response = await api.get<ProjectSummary[]>('/projects/summary');
  return response.data;
};

export const getProject = async (id: string): Promise<Project> => {
  const response = await api.get<Project>(`/projects/${id}`);
  return response.data;
};

export const createProject = async (project: Partial<Project>): Promise<Project> => {
  const response = await api.post<Project>('/projects', project);
  return response.data;
};

export const refreshProject = async (id: string): Promise<Project> => {
  const response = await api.post<Project>(`/projects/${id}/refresh`);
  return response.data;
};

// Models
export const getModels = async (
  projectId?: string,
  search?: string,
  tag?: string,
  materialized?: string
): Promise<Model[]> => {
  let url = '/api/models';
  const params: Record<string, string> = {};
  
  if (projectId) {
    params.project_id = projectId;
  }
  
  if (search) {
    // Ensure search is trimmed and non-empty
    const trimmedSearch = search.trim();
    if (trimmedSearch) {
      params.search = trimmedSearch;
      console.log('API search param:', trimmedSearch);
    }
  }
  
  if (tag) {
    params.tag = tag;
  }
  
  if (materialized) {
    params.materialized = materialized;
  }
  
  console.log('Calling API with params:', params);
  const response = await api.get(url, { params });
  console.log(`API returned ${response.data.length} models`);
  return response.data;
};

export const getModelSummaries = async (): Promise<ModelSummary[]> => {
  const response = await api.get<ModelSummary[]>('/models/summary');
  return response.data;
};

export const getModel = async (id: string): Promise<Model> => {
  const response = await api.get<Model>(`/api/models/${id}`);
  return response.data;
};

export const getModelWithLineage = async (id: string): Promise<ModelWithLineage> => {
  const response = await api.get<ModelWithLineage>(`/api/models/${id}/lineage`);
  return response.data;
};

interface ModelDetailResponse {
  model: Model;
  upstream: RelatedModel[];
  downstream: RelatedModel[];
  column_lineage?: {
    columns: Array<{
      id: number;
      name: string;
      data_type: string;
      description?: string;
    }>;
    upstream_columns: { [key: string]: ColumnLineageLink[] };
    downstream_columns: { [key: string]: ColumnLineageLink[] };
  };
}

export const fetchModelDetail = async (modelId: string): Promise<ModelDetailResponse> => {
  const [modelResponse, columnLineageResponse] = await Promise.all([
    api.get<ModelDetailResponse>(`/models/${modelId}/lineage`),
    api.get<any>(`/models/${modelId}/column-lineage`)
  ]);

  // Convert column lineage data to the format expected by the frontend
  const processColumnLinks = (columns: any[], relationships: any) => {
    const links: ColumnLineageLink[] = [];
    columns.forEach(column => {
      const columnId = column.id;
      if (relationships[columnId]) {
        relationships[columnId].forEach((rel: any) => {
          links.push({
            sourceColumn: rel.name,
            targetColumn: column.name,
            confidence: rel.confidence
          });
        });
      }
    });
    return links;
  };

  // Add column lineage to each related model
  const modelDetail: ModelDetailResponse = modelResponse.data;
  if (columnLineageResponse?.data) {
    modelDetail.column_lineage = columnLineageResponse.data;
    
    // Add column lineage to upstream models
    modelDetail.upstream = modelDetail.upstream.map(model => ({
      ...model,
      column_lineage: processColumnLinks(
        columnLineageResponse.data.columns,
        columnLineageResponse.data.upstream_columns
      ) || []  // Ensure column_lineage is always an array
    }));

    // Add column lineage to downstream models
    modelDetail.downstream = modelDetail.downstream.map(model => ({
      ...model,
      column_lineage: processColumnLinks(
        columnLineageResponse.data.columns,
        columnLineageResponse.data.downstream_columns
      ) || []  // Ensure column_lineage is always an array
    }));
  }

  return modelDetail;
};

export const getLineage = async () => {
  const response = await api.get('/api/lineage');
  return response.data;
};

// Description Updates
export const updateModelDescription = async (
  modelId: string,
  description: string
): Promise<any> => {
  const response = await api.post(`/api/models/${modelId}/description`, {
    description
  });
  return response.data;
};

export const updateColumnDescription = async (
  modelId: string,
  columnName: string,
  description: string
): Promise<any> => {
  const response = await api.post(`/api/columns/${modelId}/${columnName}/description`, {
    description
  });
  return response.data;
};

// Columns
export const getColumns = async (
  modelId?: string,
  projectId?: string,
  search?: string
): Promise<ColumnWithRelations[]> => {
  const params = { model_id: modelId, project_id: projectId, search };
  const response = await api.get<ColumnWithRelations[]>('/columns', { params });
  return response.data;
};

export const getColumn = async (id: string): Promise<ColumnWithRelations> => {
  const response = await api.get<ColumnWithRelations>(`/columns/${id}`);
  return response.data;
};

export const getRelatedColumns = async (columnName: string): Promise<ColumnWithRelations[]> => {
  const response = await api.get<ColumnWithRelations[]>('/columns/search/related', {
    params: { column_name: columnName }
  });
  return response.data;
};

// User Corrections
export const createUserCorrection = async (
  entityType: 'model' | 'column',
  entityId: string,
  correctedDescription: string
): Promise<UserCorrection> => {
  if (entityType === 'model') {
    return updateModelDescription(entityId, correctedDescription);
  } else if (entityType === 'column') {
    // For column corrections, entityId is expected to be "modelId:columnName"
    const [modelId, columnName] = entityId.split(':');
    if (!modelId || !columnName) {
      throw new Error(`Invalid column entity ID format: ${entityId}. Expected "modelId:columnName"`);
    }
    return updateColumnDescription(modelId, columnName, correctedDescription);
  }
  
  // Fallback to old API for backward compatibility
  const response = await api.post<UserCorrection>('/corrections', {
    entity_type: entityType,
    entity_id: entityId,
    corrected_description: correctedDescription
  });
  return response.data;
};

// Export
export const exportMetadata = async (format: string = 'json'): Promise<any> => {
  const response = await api.get(`/export/${format}`);
  return response.data;
};

export const exportMetadataToJson = async (): Promise<void> => {
  window.open(`${API_URL}/api/export/json`, '_blank');
};

export const exportMetadataToYaml = async (): Promise<void> => {
  window.open(`${API_URL}/api/export/yaml`, '_blank');
};

// Initialize Database
export const initializeDatabase = async (): Promise<any> => {
  const response = await api.post('/initialize');
  return response.data;
};

export const refreshMetadata = async () => {
  const response = await api.post('/api/refresh');
  return response.data;
};

export const refreshModelMetadata = async (modelId: string) => {
  const response = await api.post(`/api/models/${modelId}/refresh`);
  return response.data;
};

// Watcher service
export const getWatcherStatus = async (): Promise<any> => {
  const response = await api.get('/api/watcher/status');
  return response.data;
};

export const toggleWatcher = async (enable: boolean): Promise<any> => {
  const response = await api.post('/api/watcher/toggle', null, {
    params: { enable }
  });
  return response.data;
};

// Columns
export const getColumnLineage = async (columnId: number): Promise<ColumnWithLineage> => {
  const response = await api.get<ColumnWithLineage>(`/columns/${columnId}/lineage`);
  return response.data;
};

export const createColumnLineage = async (
  upstreamColumnId: number, 
  downstreamColumnId: number, 
  confidence?: number
): Promise<ColumnLineage> => {
  const params = new URLSearchParams();
  params.append('upstream_column_id', upstreamColumnId.toString());
  params.append('downstream_column_id', downstreamColumnId.toString());
  if (confidence !== undefined) params.append('confidence', confidence.toString());
  
  const response = await api.post(`/api/columns/lineage`, null, { params });
  return response.data;
};

export const deleteColumnLineage = async (lineageId: number): Promise<any> => {
  const response = await api.delete(`/api/columns/lineage/${lineageId}`);
  return response.data;
};

// Create a default export object with all functions
const apiService = {
  getProjects,
  getModels,
  getModel,
  getModelWithLineage,
  getLineage,
  updateModelDescription,
  updateColumnDescription,
  createUserCorrection,
  refreshMetadata,
  refreshModelMetadata,
  exportMetadataToJson,
  exportMetadataToYaml,
  getWatcherStatus,
  toggleWatcher,
  getColumnLineage,
  createColumnLineage,
  deleteColumnLineage,
  fetchModelDetail
};

export default apiService; 