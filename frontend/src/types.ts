import { ReactNode } from "react";
import { MarkerType } from 'reactflow';

// Basic model types
export interface Column {
  id: string | number;
  name: string;
  data_type?: string;
  is_primary_key?: boolean;
  description: string | null;
  ai_description?: string | null;
  user_edited?: boolean;
  model_id?: string;
  model_name?: string;
  project_name?: string;
  type: string;
}

export interface RelatedModel {
  id: string;
  name: string;
  project?: string;
  project_name?: string;
  description?: string;
  column_lineage?: ColumnLineageLink[];
}

export interface Model {
  id: string;
  name: string;
  project: string;
  project_name?: string;
  description: string | null;
  ai_description?: string | null;
  user_edited?: boolean;
  columns: Column[];
  sql?: string | null;
  file_path?: string;
  materialized?: string;
  schema?: string;
  database?: string;
  tags?: string[];
  column_lineage?: ColumnLineageLink[];
}

export interface ModelWithLineage extends Model {
  upstream: RelatedModel[];
  downstream: RelatedModel[];
}

// Project types
export interface Project {
  id: number | string;
  name: string;
  model_count?: number;
  path?: string;
  description?: string;
  created_at?: string | number | Date;
  updated_at?: string | number | Date;
}

export interface ProjectSummary extends Project {
  model_count: number;
}

// Additional types
export interface ModelSummary {
  id: string | number;
  name: string;
  project_name: string;
  project_id: string | number;
  description: string | null;
  ai_description?: string | null;
  user_edited?: boolean;
  column_count: number;
  schema?: string;
}

export interface ColumnWithRelations extends Column {
  id: string | number;
  model_name?: string;
  project_name?: string;
  upstream_columns?: Column[];
  downstream_columns?: Column[];
}

export interface UserCorrection {
  id: string | number;
  target_type: 'model' | 'column';
  target_id: string | number;
  field: string;
  old_value: string | null;
  new_value: string;
  created_at: string;
}

export interface LineageLink {
  source: string;
  target: string;
  columnLinks: ColumnLineageLink[];
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  type: string;
  animated: boolean;
  style: {
    stroke: string;
    strokeWidth: number;
  };
  markerEnd: {
    type: MarkerType;
    width: number;
    height: number;
    color: string;
  };
  data?: {
    columnLinks?: ColumnLineageLink[];
  };
}

export interface ColumnWithLineage extends Column {
  model_name: string;
  project_name: string;
  upstream_columns: Array<{
    id: number;
    name: string;
    model_name: string;
    project_name: string;
    confidence: number;
  }>;
  downstream_columns: Array<{
    id: number;
    name: string;
    model_name: string;
    project_name: string;
    confidence: number;
  }>;
}

export interface ColumnLineage {
  id: number;
  upstream_column_id: number | string;
  downstream_column_id: number | string;
  confidence: number;
}

export interface LineageGraphModel {
  id: string;
  name: string;
  project: string;
  description?: string;
  columns?: Column[];
}

export interface LineageGraphLink {
  source: string;
  target: string;
  columnLinks: ColumnLineageLink[];
}

export interface ColumnLineageLink {
  sourceColumn: string;
  targetColumn: string;
  confidence: number;
}

export interface SearchResult {
  id: number | string;
  name: string;
  description?: string;
  project_name: string;
  schema?: string;
  type: 'model' | 'column';
  model_id?: number | string;
  model_name?: string;
}

export interface RelatedColumn {
  id: string | number;
  name: string;
  model_id: string | number;
  model_name: string;
  project_name?: string;
  confidence: number;
} 