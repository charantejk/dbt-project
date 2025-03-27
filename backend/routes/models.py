from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, func
import logging

from backend.models.schema import Model, ModelSummary, ModelWithLineage
from backend.models.database import Model as DBModel, Project as DBProject, ColumnLineage as DBColumnLineage
from backend.services.database import get_db
# from backend.services.ai_service import get_model_suggestions  # Comment out AI import
# from backend.models.models import ModelSuggestion  # Commented out AI-related import
from backend.services.model_service import ModelService

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Model])
def get_models(
    search: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all models with optional filtering
    """
    model_service = ModelService(db)
    return model_service.get_models(search, project_id)

@router.get("/{model_id}", response_model=Model)
def get_model(model_id: str, db: Session = Depends(get_db)):
    """
    Get a specific model by ID
    """
    model_service = ModelService(db)
    model = model_service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
        
    return model

@router.get("/{model_id}/lineage", response_model=Dict[str, Any])
async def get_model_lineage(model_id: str, db: Session = Depends(get_db)):
    """
    Get upstream and downstream models for a specific model
    """
    try:
        # Get the model
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        logging.info(f"Getting lineage for model {model_id} ({model.name})")

        # Get upstream and downstream models
        upstream_models = []
        downstream_models = []

        # Get upstream models
        upstream_relationships = db.query(ModelRelationship).filter(
            ModelRelationship.downstream_model_id == model_id
        ).all()

        for rel in upstream_relationships:
            upstream_model = db.query(Model).filter(Model.id == rel.upstream_model_id).first()
            if upstream_model:
                upstream_project = db.query(Project).filter(Project.id == upstream_model.project_id).first()
                upstream_model_dict = upstream_model.__dict__.copy()
                upstream_model_dict.pop('_sa_instance_state', None)
                
                # Include project name for cross-project references
                if upstream_project:
                    upstream_model_dict["project_name"] = upstream_project.name
                
                logging.info(f"  - {upstream_model.name} ({upstream_model.id})")
                upstream_models.append(upstream_model_dict)

        # Get downstream models
        downstream_relationships = db.query(ModelRelationship).filter(
            ModelRelationship.upstream_model_id == model_id
        ).all()

        for rel in downstream_relationships:
            downstream_model = db.query(Model).filter(Model.id == rel.downstream_model_id).first()
            if downstream_model:
                downstream_project = db.query(Project).filter(Project.id == downstream_model.project_id).first()
                downstream_model_dict = downstream_model.__dict__.copy()
                downstream_model_dict.pop('_sa_instance_state', None)
                
                # Include project name for cross-project references
                if downstream_project:
                    downstream_model_dict["project_name"] = downstream_project.name
                
                logging.info(f"  - {downstream_model.name} ({downstream_model.id})")
                downstream_models.append(downstream_model_dict)

        if upstream_models:
            logging.info(f"Found {len(upstream_models)} upstream models")
            for model in upstream_models:
                logging.info(f"  - {model['name']} ({model['id']})")
        else:
            logging.info("No upstream models found")

        if downstream_models:
            logging.info(f"Found {len(downstream_models)} downstream models")
            for model in downstream_models:
                logging.info(f"  - {model['name']} ({model['id']})")
        else:
            logging.info("No downstream models found")

        return {
            "upstream": upstream_models,
            "downstream": downstream_models
        }
    except Exception as e:
        logging.error(f"Error getting lineage for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/column-lineage", response_model=Dict[str, Any])
def get_model_column_lineage(model_id: str, db: Session = Depends(get_db)):
    """
    Get column-level lineage for a specific model
    
    Returns a dict with:
    - columns: list of columns in the model
    - upstream_columns: dict mapping column id to list of upstream columns
    - downstream_columns: dict mapping column id to list of downstream columns
    """
    model_service = ModelService(db)
    model = model_service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get all columns for this model
    model_columns = db.query(DBColumn).filter(DBColumn.model_id == model_id).all()
    
    # Initialize result structure
    result = {
        "columns": [],
        "upstream_columns": {},
        "downstream_columns": {}
    }
    
    # Add columns to result
    for column in model_columns:
        column_dict = {
            "id": column.id,
            "name": column.name,
            "data_type": column.data_type,
            "description": column.description
        }
        result["columns"].append(column_dict)
        
        # Get upstream columns
        upstream_relations = db.query(DBColumnLineage).filter(
            DBColumnLineage.downstream_column_id == column.id
        ).all()
        
        upstream_columns = []
        for relation in upstream_relations:
            upstream_column = db.query(DBColumn).filter(
                DBColumn.id == relation.upstream_column_id
            ).first()
            
            if upstream_column:
                upstream_model = db.query(DBModel).filter(
                    DBModel.id == upstream_column.model_id
                ).first()
                
                if upstream_model:
                    project = db.query(DBProject).filter(
                        DBProject.id == upstream_model.project_id
                    ).first()
                    
                    upstream_columns.append({
                        "id": upstream_column.id,
                        "name": upstream_column.name,
                        "model_id": upstream_model.id,
                        "model_name": upstream_model.name,
                        "project_name": project.name if project else "",
                        "confidence": relation.confidence
                    })
        
        result["upstream_columns"][column.id] = upstream_columns
        
        # Get downstream columns
        downstream_relations = db.query(DBColumnLineage).filter(
            DBColumnLineage.upstream_column_id == column.id
        ).all()
        
        downstream_columns = []
        for relation in downstream_relations:
            downstream_column = db.query(DBColumn).filter(
                DBColumn.id == relation.downstream_column_id
            ).first()
            
            if downstream_column:
                downstream_model = db.query(DBModel).filter(
                    DBModel.id == downstream_column.model_id
                ).first()
                
                if downstream_model:
                    project = db.query(DBProject).filter(
                        DBProject.id == downstream_model.project_id
                    ).first()
                    
                    downstream_columns.append({
                        "id": downstream_column.id,
                        "name": downstream_column.name,
                        "model_id": downstream_model.id,
                        "model_name": downstream_model.name,
                        "project_name": project.name if project else "",
                        "confidence": relation.confidence
                    })
        
        result["downstream_columns"][column.id] = downstream_columns
    
    return result

@router.get("/search/lineage")
def search_models_with_lineage(
    search: str = Query(..., description="Search term for models"),
    db: Session = Depends(get_db)
):
    """
    Search for models and return their lineage information
    """
    search_term = f"%{search}%"
    
    # Find matching models
    models = db.query(DBModel).filter(
        or_(
            DBModel.name.ilike(search_term),
            DBModel.description.ilike(search_term)
            # DBModel.ai_description.ilike(search_term)  # Comment out AI field
        )
    ).all()
    
    result = []
    for model in models:
        # Get upstream models
        upstream = []
        for edge in model.upstream_edges:
            upstream_model = edge.upstream_model
            upstream.append({
                "id": upstream_model.id,
                "name": upstream_model.name,
                "project_name": upstream_model.project.name
            })
        
        # Get downstream models
        downstream = []
        for edge in model.downstream_edges:
            downstream_model = edge.downstream_model
            downstream.append({
                "id": downstream_model.id,
                "name": downstream_model.name,
                "project_name": downstream_model.project.name
            })
        
        result.append({
            "id": model.id,
            "name": model.name,
            "project_name": model.project.name,
            "upstream": upstream,
            "downstream": downstream
        })
    
    return result 