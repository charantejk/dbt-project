from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from ..models.models import Model, ModelWithLineage, RelatedModel, Column, ColumnWithLineage
# from ..models.models import ModelSuggestion  # Commented out AI-related import
from ..db.models import (
    Model as DBModel,
    Project as DBProject,
    ColumnModel as DBColumn,
    Lineage as DBLineage,
    ColumnLineage as DBColumnLineage,
    # ModelSuggestion as DBModelSuggestion  # Commented out AI-related import
)

class ModelService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_models(
        self, 
        search: Optional[str] = None, 
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Model]:
        """Get models with optional filtering"""
        query = self.db.query(DBModel)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    DBModel.name.ilike(search_term),
                    DBModel.description.ilike(search_term)
                )
            )
        
        if project_id:
            query = query.filter(DBModel.project_id == project_id)
        
        # Join with project to get project_name
        query = query.join(DBProject, DBModel.project_id == DBProject.id)
        
        # Get column count
        query = query.outerjoin(
            DBColumn, 
            DBModel.id == DBColumn.model_id
        ).add_columns(
            func.count(DBColumn.id).label('column_count')
        ).group_by(DBModel.id, DBProject.id)
        
        # Add project name to results
        query = query.add_columns(DBProject.name.label('project_name'))
        
        # Execute query with limit
        results = query.limit(limit).all()
        
        # Format results
        models = []
        for result in results:
            model_data = result[0].__dict__
            model_data['column_count'] = result[1]
            model_data['project_name'] = result[2]
            
            # Remove SQLAlchemy instance state
            if '_sa_instance_state' in model_data:
                del model_data['_sa_instance_state']
            
            models.append(Model(**model_data))
        
        return models
    
    def get_model_by_id(self, model_id: str) -> Optional[Model]:
        """Get a single model by ID"""
        result = self.db.query(
            DBModel,
            DBProject.name.label('project_name'),
            func.count(DBColumn.id).label('column_count')
        ).join(
            DBProject, 
            DBModel.project_id == DBProject.id
        ).outerjoin(
            DBColumn,
            DBModel.id == DBColumn.model_id
        ).filter(
            DBModel.id == model_id
        ).group_by(
            DBModel.id, 
            DBProject.id
        ).first()
        
        if not result:
            return None
        
        model_data = result[0].__dict__
        model_data['project_name'] = result[1]
        model_data['column_count'] = result[2]
        
        # Remove SQLAlchemy instance state
        if '_sa_instance_state' in model_data:
            del model_data['_sa_instance_state']
        
        return Model(**model_data)
    
    def get_models_with_lineage(
        self, 
        search: Optional[str] = None, 
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ModelWithLineage]:
        """Get models with lineage information"""
        # First get filtered models
        models = self.get_models(search, project_id, limit)
        
        # Get lineage for each model
        models_with_lineage = []
        for model in models:
            lineage_model = self.get_model_lineage_by_id(model.id)
            if lineage_model:
                models_with_lineage.append(lineage_model)
        
        return models_with_lineage
    
    def get_model_lineage_by_id(self, model_id: str) -> Optional[ModelWithLineage]:
        """Get model with its upstream and downstream lineage"""
        # Get the model first
        model = self.get_model_by_id(model_id)
        if not model:
            return None
        
        # Get upstream models (parents)
        upstream_query = self.db.query(
            DBModel, 
            DBProject.name.label('project_name'),
            func.count(DBColumn.id).label('column_count'),
            DBLineage.id.label('lineage_id')
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).outerjoin(
            DBColumn,
            DBModel.id == DBColumn.model_id
        ).join(
            DBLineage,
            DBModel.id == DBLineage.upstream_id
        ).filter(
            DBLineage.downstream_id == model_id
        ).group_by(
            DBModel.id,
            DBProject.id,
            DBLineage.id
        ).all()
        
        # Get downstream models (children)
        downstream_query = self.db.query(
            DBModel,
            DBProject.name.label('project_name'),
            func.count(DBColumn.id).label('column_count'),
            DBLineage.id.label('lineage_id')
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).outerjoin(
            DBColumn,
            DBModel.id == DBColumn.model_id
        ).join(
            DBLineage,
            DBModel.id == DBLineage.downstream_id
        ).filter(
            DBLineage.upstream_id == model_id
        ).group_by(
            DBModel.id,
            DBProject.id,
            DBLineage.id
        ).all()
        
        # Format upstream models
        upstream_models = []
        for result in upstream_query:
            model_data = {
                'id': result[0].id,
                'name': result[0].name,
                'project_name': result[1],
                'lineage_id': result[3]
            }
            upstream_models.append(RelatedModel(**model_data))
        
        # Format downstream models
        downstream_models = []
        for result in downstream_query:
            model_data = {
                'id': result[0].id,
                'name': result[0].name,
                'project_name': result[1],
                'lineage_id': result[3]
            }
            downstream_models.append(RelatedModel(**model_data))
        
        # Create the model with lineage
        model_dict = model.dict()
        model_dict['upstream'] = upstream_models
        model_dict['downstream'] = downstream_models
        
        return ModelWithLineage(**model_dict)
    
    # Comment out AI-related method
    # def get_model_suggestions(self, model_id: str) -> List[ModelSuggestion]:
    #     """Get AI-generated suggestions for a model"""
    #     suggestions_query = self.db.query(
    #         DBModelSuggestion
    #     ).filter(
    #         DBModelSuggestion.model_id == model_id
    #     ).all()
    #     
    #     suggestions = []
    #     for suggestion in suggestions_query:
    #         suggestion_data = suggestion.__dict__
    #         
    #         if '_sa_instance_state' in suggestion_data:
    #             del suggestion_data['_sa_instance_state']
    #             
    #         suggestions.append(ModelSuggestion(**suggestion_data))
    #         
    #     return suggestions 

class ColumnService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_column_by_id(self, column_id: int) -> Optional[Column]:
        """Get a single column by ID"""
        result = self.db.query(
            DBColumn,
            DBModel.name.label('model_name'),
            DBProject.name.label('project_name')
        ).join(
            DBModel,
            DBColumn.model_id == DBModel.id
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).filter(
            DBColumn.id == column_id
        ).first()
        
        if not result:
            return None
        
        column_data = result[0].__dict__
        column_data['model_name'] = result[1]
        column_data['project_name'] = result[2]
        
        # Remove SQLAlchemy instance state
        if '_sa_instance_state' in column_data:
            del column_data['_sa_instance_state']
        
        return Column(**column_data)
    
    def get_columns_by_model_id(self, model_id: int) -> List[Column]:
        """Get all columns for a specific model"""
        results = self.db.query(
            DBColumn,
            DBModel.name.label('model_name'),
            DBProject.name.label('project_name')
        ).join(
            DBModel,
            DBColumn.model_id == DBModel.id
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).filter(
            DBModel.id == model_id
        ).all()
        
        columns = []
        for result in results:
            column_data = result[0].__dict__
            column_data['model_name'] = result[1]
            column_data['project_name'] = result[2]
            
            # Remove SQLAlchemy instance state
            if '_sa_instance_state' in column_data:
                del column_data['_sa_instance_state']
            
            columns.append(Column(**column_data))
        
        return columns
    
    def get_column_lineage_by_id(self, column_id: int) -> Optional[ColumnWithLineage]:
        """Get column with its upstream and downstream lineage"""
        # Get the column first
        column = self.get_column_by_id(column_id)
        if not column:
            return None
        
        # Get upstream columns (parents)
        upstream_query = self.db.query(
            DBColumn,
            DBModel.name.label('model_name'),
            DBProject.name.label('project_name'),
            DBColumnLineage.confidence.label('confidence')
        ).join(
            DBModel,
            DBColumn.model_id == DBModel.id
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).join(
            DBColumnLineage,
            DBColumn.id == DBColumnLineage.upstream_column_id
        ).filter(
            DBColumnLineage.downstream_column_id == column_id
        ).all()
        
        # Get downstream columns (children)
        downstream_query = self.db.query(
            DBColumn,
            DBModel.name.label('model_name'),
            DBProject.name.label('project_name'),
            DBColumnLineage.confidence.label('confidence')
        ).join(
            DBModel,
            DBColumn.model_id == DBModel.id
        ).join(
            DBProject,
            DBModel.project_id == DBProject.id
        ).join(
            DBColumnLineage,
            DBColumn.id == DBColumnLineage.downstream_column_id
        ).filter(
            DBColumnLineage.upstream_column_id == column_id
        ).all()
        
        # Format upstream columns
        upstream_columns = []
        for result in upstream_query:
            column_data = result[0].__dict__
            column_data['model_name'] = result[1]
            column_data['project_name'] = result[2]
            column_data['confidence'] = result[3]
            
            # Remove SQLAlchemy instance state
            if '_sa_instance_state' in column_data:
                del column_data['_sa_instance_state']
            
            upstream_columns.append(column_data)
        
        # Format downstream columns
        downstream_columns = []
        for result in downstream_query:
            column_data = result[0].__dict__
            column_data['model_name'] = result[1]
            column_data['project_name'] = result[2]
            column_data['confidence'] = result[3]
            
            # Remove SQLAlchemy instance state
            if '_sa_instance_state' in column_data:
                del column_data['_sa_instance_state']
            
            downstream_columns.append(column_data)
        
        # Create the column with lineage
        column_dict = column.dict()
        column_dict['upstream_columns'] = upstream_columns
        column_dict['downstream_columns'] = downstream_columns
        
        return ColumnWithLineage(**column_dict) 