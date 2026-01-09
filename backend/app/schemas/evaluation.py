"""
Schemas for evaluation datasets and runs.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List
from datetime import datetime
import uuid


class EvaluationDatasetCreate(BaseModel):
    """Schema for creating an evaluation dataset via form data (no file upload)."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")


class EvaluationDatasetUpdate(BaseModel):
    """Schema for updating an evaluation dataset."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    source_type: Optional[str] = Field(None, pattern="^(csv|langsmith|database)$")
    source_path: Optional[str] = Field(None, max_length=500)
    num_examples: Optional[int] = Field(None, gt=0)


class EvaluationDatasetResponse(BaseModel):
    """Schema for evaluation dataset responses."""
    
    id: uuid.UUID = Field(..., description="Dataset identifier")
    organization_id: uuid.UUID = Field(..., description="Organization identifier")
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    source_type: str = Field(..., description="Source type")
    source_path: Optional[str] = Field(None, description="Source path")
    num_examples: int = Field(..., description="Number of examples")
    langsmith_dataset_name: Optional[str] = Field(None, description="LangSmith dataset name")
    langsmith_dataset_id: Optional[str] = Field(None, description="LangSmith dataset ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class EvaluationMetricsSummary(BaseModel):
    """Schema for macro-averaged metrics."""
    
    pearson_r: float = Field(..., description="Pearson correlation coefficient")
    qwk: float = Field(..., description="Quadratic Weighted Kappa")
    plus_minus_one_accuracy: float = Field(..., description="±1 band accuracy")


class EvaluationRunResponse(BaseModel):
    """Schema for evaluation run responses."""
    
    id: uuid.UUID = Field(..., description="Run identifier")
    prompt_template_id: uuid.UUID = Field(..., description="Prompt template identifier")
    dataset_id: Optional[uuid.UUID] = Field(None, description="Dataset identifier")
    experiment_name: Optional[str] = Field(None, description="Experiment name")
    num_examples: int = Field(..., description="Number of examples evaluated")
    macro_pearson_r: Optional[float] = Field(None, description="Macro-averaged Pearson r")
    macro_qwk: Optional[float] = Field(None, description="Macro-averaged QWK")
    macro_plus_minus_one: Optional[float] = Field(None, description="Macro-averaged ±1 accuracy")
    per_dimension_metrics: Dict = Field(..., description="Per-dimension metrics")
    model_name: Optional[str] = Field(None, description="LLM model used")
    runtime_seconds: Optional[float] = Field(None, description="Runtime in seconds")
    langsmith_url: Optional[str] = Field(None, description="LangSmith web UI URL")
    langsmith_experiment_id: Optional[str] = Field(None, description="LangSmith experiment ID")
    created_at: datetime = Field(..., description="Run timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RunEvaluationRequest(BaseModel):
    """Schema for triggering an evaluation run."""
    
    prompt_template_id: uuid.UUID = Field(..., description="Prompt template to evaluate")
    dataset_id: uuid.UUID = Field(..., description="Dataset to use for evaluation")
    experiment_name: Optional[str] = Field(None, max_length=100, description="Optional experiment name")


class EvaluationRunListResponse(BaseModel):
    """Schema for listing evaluation runs."""
    
    runs: List[EvaluationRunResponse] = Field(..., description="List of evaluation runs")
    total: int = Field(..., description="Total number of runs")

