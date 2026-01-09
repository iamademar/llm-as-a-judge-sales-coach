"""
API endpoints for managing evaluations and golden datasets.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import csv
import os
from pathlib import Path

from app.routers.deps import get_db
from app.core.jwt_dependency import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.evaluation_dataset import EvaluationDataset
from app.models.evaluation_run import EvaluationRun
from app.models.prompt_template import PromptTemplate
from app.schemas.evaluation import (
    EvaluationDatasetCreate,
    EvaluationDatasetUpdate,
    EvaluationDatasetResponse,
    EvaluationRunResponse,
    RunEvaluationRequest,
    EvaluationRunListResponse,
)
from app.crud import evaluation_dataset as dataset_crud
from app.crud import evaluation_run as run_crud
from app.services.evaluation_runner import run_dual_evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

# Directory for storing uploaded CSV files
UPLOAD_DIR = Path("/workspace/data/evaluation_datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Dataset endpoints
@router.post("/datasets", response_model=EvaluationDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new evaluation dataset by uploading a CSV file.
    
    The CSV should have columns: id, transcript, score_situation, score_problem,
    score_implication, score_need_payoff, score_flow, score_tone, score_engagement
    """
    # Validate file is CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{current_user.organization_id}_{file_id}{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    # Save uploaded file
    try:
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Count examples in CSV
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            num_examples = sum(1 for _ in reader)
    except Exception as e:
        # Clean up file if counting fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    if num_examples == 0:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="CSV file contains no data rows")
    
    # Create dataset record
    eval_dataset = dataset_crud.create(
        db,
        organization_id=current_user.organization_id,
        name=name,
        description=description,
        source_type="csv",
        source_path=str(file_path),
        num_examples=num_examples,
    )
    
    # Auto-upload to LangSmith if API key configured
    if settings.LANGCHAIN_API_KEY:
        try:
            from app.services.langsmith_dataset_upload import (
                upload_csv_to_langsmith,
                slugify_dataset_name
            )
            
            print(f"Uploading dataset to LangSmith...")
            slug = slugify_dataset_name(name)
            ls_name, ls_id = upload_csv_to_langsmith(
                csv_path=str(file_path),
                dataset_name=slug,
                description=description,
            )
            
            # Update dataset with LangSmith info
            eval_dataset.langsmith_dataset_name = ls_name
            eval_dataset.langsmith_dataset_id = ls_id
            db.commit()
            db.refresh(eval_dataset)
            
            print(f"✓ Dataset uploaded to LangSmith as: {ls_name}")
        except Exception as e:
            # Log warning but don't fail dataset creation
            print(f"⚠️  Failed to upload to LangSmith: {e}")
    
    return eval_dataset


@router.get("/datasets", response_model=List[EvaluationDatasetResponse])
def list_evaluation_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all evaluation datasets for the current organization."""
    datasets = dataset_crud.get_by_org(db, current_user.organization_id)
    return datasets


@router.get("/datasets/{dataset_id}", response_model=EvaluationDatasetResponse)
def get_evaluation_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific evaluation dataset."""
    dataset = dataset_crud.get_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return dataset


@router.patch("/datasets/{dataset_id}", response_model=EvaluationDatasetResponse)
def update_evaluation_dataset(
    dataset_id: uuid.UUID,
    dataset_update: EvaluationDatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an evaluation dataset."""
    dataset = dataset_crud.get_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_dataset = dataset_crud.update(
        db,
        dataset,
        name=dataset_update.name,
        description=dataset_update.description,
        source_type=dataset_update.source_type,
        source_path=dataset_update.source_path,
        num_examples=dataset_update.num_examples,
    )
    return updated_dataset


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an evaluation dataset."""
    dataset = dataset_crud.get_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    dataset_crud.delete(db, dataset)
    return None


# Run endpoints
@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation(
    request: RunEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an evaluation run for a prompt template against a dataset.
    
    This runs the evaluation pipeline and stores results in the database.
    Note: This can take several minutes for large datasets.
    """
    # Verify template belongs to user's org
    template = db.query(PromptTemplate).filter(PromptTemplate.id == request.prompt_template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    if template.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied to template")
    
    # Verify dataset belongs to user's org
    dataset = dataset_crud.get_by_id(db, request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied to dataset")
    
    # Verify dataset has a valid source path
    if not dataset.source_path:
        raise HTTPException(status_code=400, detail="Dataset has no source path configured")
    
    # Run evaluation (both local and LangSmith)
    try:
        eval_run = run_dual_evaluation(
            csv_path=dataset.source_path,
            prompt_template_id=request.prompt_template_id,
            dataset_id=request.dataset_id,
            experiment_name=request.experiment_name,
            organization_id=current_user.organization_id,
            db=db,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Evaluation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    return eval_run


@router.get("/runs", response_model=EvaluationRunListResponse)
def list_evaluation_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all evaluation runs for the current organization."""
    runs = run_crud.get_by_organization(db, current_user.organization_id)
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_evaluation_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details for a specific evaluation run."""
    run = run_crud.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    
    # Verify access via template's organization
    if run.prompt_template.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return run


@router.get("/templates/{template_id}/runs", response_model=List[EvaluationRunResponse])
def get_template_evaluation_runs(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all evaluation runs for a specific prompt template."""
    # Verify template belongs to user's org
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    runs = run_crud.get_by_template(db, template_id)
    return runs


@router.get("/templates/{template_id}/latest", response_model=EvaluationRunResponse)
def get_template_latest_evaluation(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest evaluation run for a template."""
    # Verify template belongs to user's org
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    run = run_crud.get_latest_for_template(db, template_id)
    if not run:
        raise HTTPException(status_code=404, detail="No evaluation runs found for this template")
    
    return run

