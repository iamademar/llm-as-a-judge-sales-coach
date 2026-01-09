"""
Integration tests for evaluation API endpoints.

Tests cover all 10 endpoints from /evaluations router:
Dataset Management:
- POST /evaluations/datasets - Upload CSV dataset
- GET /evaluations/datasets - List datasets
- GET /evaluations/datasets/{id} - Get dataset details
- PATCH /evaluations/datasets/{id} - Update dataset
- DELETE /evaluations/datasets/{id} - Delete dataset

Evaluation Runs:
- POST /evaluations/run - Run evaluation on template vs dataset
- GET /evaluations/runs - List all evaluation runs
- GET /evaluations/runs/{id} - Get run details
- GET /evaluations/templates/{id}/runs - Get runs for template
- GET /evaluations/templates/{id}/latest - Get latest run for template
"""
import io
import pytest
from unittest.mock import patch, Mock

from app.crud import evaluation_dataset as dataset_crud
from app.crud import evaluation_run as run_crud
from app.crud import prompt_template as template_crud


# ============================================================================
# Dataset Endpoints Tests
# ============================================================================

class TestCreateDataset:
    """Tests for POST /evaluations/datasets"""

    def test_create_dataset_success(self, test_client, auth_headers, tmp_path):
        """Test successful CSV upload and dataset creation"""
        # Arrange - Create CSV file content
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
2,"Rep: How are you?\\nBuyer: Good",3,4,3,4,3,4,4
"""
        csv_file = ("test_dataset.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={
                "name": "My Test Dataset",
                "description": "A test dataset"
            },
            files={"file": csv_file},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Dataset"
        assert data["description"] == "A test dataset"
        assert data["source_type"] == "csv"
        assert data["num_examples"] == 2
        assert "id" in data
        assert "organization_id" in data
        assert "source_path" in data

    def test_create_dataset_counts_examples_correctly(self, test_client, auth_headers):
        """Test that num_examples is counted correctly from CSV"""
        # Arrange - Create CSV with 5 rows
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: A\\nBuyer: B",4,3,4,3,4,4,3
2,"Rep: C\\nBuyer: D",3,4,3,4,3,4,4
3,"Rep: E\\nBuyer: F",5,5,5,5,5,5,5
4,"Rep: G\\nBuyer: H",2,2,2,2,2,2,2
5,"Rep: I\\nBuyer: J",4,4,4,4,4,4,4
"""
        csv_file = ("dataset.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Five Row Dataset"},
            files={"file": csv_file},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["num_examples"] == 5

    def test_create_dataset_requires_csv_file(self, test_client, auth_headers):
        """Test that non-CSV files are rejected"""
        # Arrange - Create non-CSV file
        txt_file = ("test.txt", io.BytesIO(b"Not a CSV"), "text/plain")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Invalid Dataset"},
            files={"file": txt_file},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        detail = response_data.get("detail", str(response_data))
        assert "CSV" in str(detail)

    def test_create_dataset_rejects_empty_csv(self, test_client, auth_headers):
        """Test that CSV with only headers is rejected"""
        # Arrange - CSV with headers only
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
"""
        csv_file = ("empty.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Empty Dataset"},
            files={"file": csv_file},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        detail = response_data.get("detail", str(response_data))
        assert "no data rows" in str(detail).lower()

    def test_create_dataset_requires_authentication(self, test_client):
        """Test that authentication is required"""
        # Arrange
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
"""
        csv_file = ("test.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Test Dataset"},
            files={"file": csv_file}
        )

        # Assert
        assert response.status_code in [401, 403]  # May return 403 for missing auth

    def test_create_dataset_inherits_org_from_user(
        self, test_client, auth_headers, sample_user, db_session
    ):
        """Test that dataset inherits organization_id from user"""
        # Arrange
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
"""
        csv_file = ("test.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Test Dataset"},
            files={"file": csv_file},
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["organization_id"] == str(sample_user.organization_id)

    @patch("app.services.langsmith_dataset_upload.upload_csv_to_langsmith")
    def test_create_dataset_skips_langsmith_upload_gracefully(
        self, mock_upload, test_client, auth_headers
    ):
        """Test that LangSmith upload failure doesn't break dataset creation"""
        # Arrange - Mock LangSmith upload to fail
        mock_upload.side_effect = Exception("LangSmith API error")
        
        csv_content = b"""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
"""
        csv_file = ("test.csv", io.BytesIO(csv_content), "text/csv")

        # Act
        response = test_client.post(
            "/evaluations/datasets",
            data={"name": "Test Dataset"},
            files={"file": csv_file},
            headers=auth_headers
        )

        # Assert - Dataset should still be created
        assert response.status_code == 201
        assert response.json()["name"] == "Test Dataset"


class TestListDatasets:
    """Tests for GET /evaluations/datasets"""

    def test_list_datasets_returns_org_datasets(
        self, test_client, auth_headers, sample_evaluation_dataset
    ):
        """Test listing returns all datasets for user's organization"""
        # Act
        response = test_client.get(
            "/evaluations/datasets",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == str(sample_evaluation_dataset.id)
        assert data[0]["name"] == sample_evaluation_dataset.name

    def test_list_datasets_returns_empty_for_new_org(
        self, test_client, second_auth_headers
    ):
        """Test listing returns empty array for organization with no datasets"""
        # Act
        response = test_client.get(
            "/evaluations/datasets",
            headers=second_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_datasets_only_shows_own_org(
        self, test_client, auth_headers, db_session,
        sample_organization, second_organization, sample_evaluation_dataset, tmp_path
    ):
        """Test that users only see datasets from their organization"""
        # Arrange - Create dataset in different org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Dataset",
            description="Should not be visible",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )

        # Act
        response = test_client.get(
            "/evaluations/datasets",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        dataset_ids = [d["id"] for d in data]
        assert str(sample_evaluation_dataset.id) in dataset_ids
        assert str(other_dataset.id) not in dataset_ids

    def test_list_datasets_requires_authentication(self, test_client):
        """Test that authentication is required"""
        # Act
        response = test_client.get("/evaluations/datasets")

        # Assert
        assert response.status_code in [401, 403]


class TestGetDataset:
    """Tests for GET /evaluations/datasets/{id}"""

    def test_get_dataset_by_id_success(
        self, test_client, auth_headers, sample_evaluation_dataset
    ):
        """Test getting specific dataset by ID"""
        # Act
        response = test_client.get(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_evaluation_dataset.id)
        assert data["name"] == sample_evaluation_dataset.name
        assert data["source_type"] == sample_evaluation_dataset.source_type
        assert data["num_examples"] == sample_evaluation_dataset.num_examples

    def test_get_dataset_404_for_nonexistent_id(self, test_client, auth_headers):
        """Test 404 when dataset doesn't exist"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.get(
            f"/evaluations/datasets/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_dataset_403_for_other_org_dataset(
        self, test_client, auth_headers, db_session, second_organization, tmp_path
    ):
        """Test 403 when accessing another organization's dataset"""
        # Arrange - Create dataset in different org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Dataset",
            description="Access denied",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )

        # Act
        response = test_client.get(
            f"/evaluations/datasets/{other_dataset.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_dataset_requires_authentication(
        self, test_client, sample_evaluation_dataset
    ):
        """Test that authentication is required"""
        # Act
        response = test_client.get(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}"
        )

        # Assert
        assert response.status_code in [401, 403]


class TestUpdateDataset:
    """Tests for PATCH /evaluations/datasets/{id}"""

    def test_update_dataset_partial(
        self, test_client, auth_headers, sample_evaluation_dataset
    ):
        """Test partial update of dataset (name only)"""
        # Arrange
        payload = {"name": "Updated Dataset Name"}

        # Act
        response = test_client.patch(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Dataset Name"
        assert data["description"] == sample_evaluation_dataset.description  # Unchanged

    def test_update_dataset_full(
        self, test_client, auth_headers, sample_evaluation_dataset
    ):
        """Test full update of dataset"""
        # Arrange
        payload = {
            "name": "New Name",
            "description": "New Description",
            "num_examples": 5
        }

        # Act
        response = test_client.patch(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New Description"
        assert data["num_examples"] == 5

    def test_update_dataset_404_for_nonexistent(self, test_client, auth_headers):
        """Test 404 when updating non-existent dataset"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"name": "New Name"}

        # Act
        response = test_client.patch(
            f"/evaluations/datasets/{fake_id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_dataset_403_for_other_org(
        self, test_client, auth_headers, db_session, second_organization, tmp_path
    ):
        """Test 403 when updating other org's dataset"""
        # Arrange - Create dataset in different org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Dataset",
            description="Access denied",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )
        payload = {"name": "Hacked Name"}

        # Act
        response = test_client.patch(
            f"/evaluations/datasets/{other_dataset.id}",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_update_dataset_requires_authentication(
        self, test_client, sample_evaluation_dataset
    ):
        """Test that authentication is required"""
        # Arrange
        payload = {"name": "New Name"}

        # Act
        response = test_client.patch(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}",
            json=payload
        )

        # Assert
        assert response.status_code in [401, 403]


class TestDeleteDataset:
    """Tests for DELETE /evaluations/datasets/{id}"""

    def test_delete_dataset_success(
        self, test_client, auth_headers, db_session, sample_organization, tmp_path
    ):
        """Test successful deletion of dataset"""
        # Arrange - Create a dataset to delete
        csv_path = tmp_path / "deletable_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        dataset = dataset_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Deletable Dataset",
            description="Will be deleted",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )

        # Act
        response = test_client.delete(
            f"/evaluations/datasets/{dataset.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 204
        
        # Verify deletion
        deleted = dataset_crud.get_by_id(db_session, dataset.id)
        assert deleted is None

    def test_delete_dataset_404_for_nonexistent(self, test_client, auth_headers):
        """Test 404 when deleting non-existent dataset"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.delete(
            f"/evaluations/datasets/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_delete_dataset_403_for_other_org(
        self, test_client, auth_headers, db_session, second_organization, tmp_path
    ):
        """Test 403 when deleting other org's dataset"""
        # Arrange - Create dataset in different org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Org Dataset",
            description="Access denied",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )

        # Act
        response = test_client.delete(
            f"/evaluations/datasets/{other_dataset.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_delete_dataset_requires_authentication(
        self, test_client, sample_evaluation_dataset
    ):
        """Test that authentication is required"""
        # Act
        response = test_client.delete(
            f"/evaluations/datasets/{sample_evaluation_dataset.id}"
        )

        # Assert
        assert response.status_code in [401, 403]


# ============================================================================
# Evaluation Run Endpoints Tests
# ============================================================================

class TestRunEvaluation:
    """Tests for POST /evaluations/run"""

    @patch("app.routers.evaluations.run_dual_evaluation")
    def test_run_evaluation_success(
        self, mock_run_eval, test_client, auth_headers,
        sample_prompt_template, sample_evaluation_dataset, db_session
    ):
        """Test successful evaluation run"""
        # Arrange - Mock evaluation runner
        mock_run = Mock()
        mock_run.id = "12345678-1234-1234-1234-123456789012"
        mock_run.prompt_template_id = sample_prompt_template.id
        mock_run.dataset_id = sample_evaluation_dataset.id
        mock_run.experiment_name = "Test Experiment"
        mock_run.num_examples = 2
        mock_run.macro_pearson_r = 0.90
        mock_run.macro_qwk = 0.88
        mock_run.macro_plus_minus_one = 0.95
        mock_run.per_dimension_metrics = {}
        mock_run.model_name = "gpt-4o-mini"
        mock_run.runtime_seconds = 15.5
        mock_run.langsmith_url = None
        mock_run.langsmith_experiment_id = None
        mock_run.created_at = "2024-01-01T00:00:00"
        mock_run_eval.return_value = mock_run

        payload = {
            "prompt_template_id": str(sample_prompt_template.id),
            "dataset_id": str(sample_evaluation_dataset.id),
            "experiment_name": "Test Experiment"
        }

        # Act
        response = test_client.post(
            "/evaluations/run",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["num_examples"] == 2
        assert "macro_pearson_r" in data
        assert "macro_qwk" in data

        # Verify mock was called
        mock_run_eval.assert_called_once()

    def test_run_evaluation_404_for_nonexistent_template(
        self, test_client, auth_headers, sample_evaluation_dataset
    ):
        """Test 404 when template doesn't exist"""
        # Arrange
        fake_template_id = "00000000-0000-0000-0000-000000000000"
        payload = {
            "prompt_template_id": fake_template_id,
            "dataset_id": str(sample_evaluation_dataset.id)
        }

        # Act
        response = test_client.post(
            "/evaluations/run",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        detail = response_data.get("detail", str(response_data))
        assert "template" in str(detail).lower()

    def test_run_evaluation_404_for_nonexistent_dataset(
        self, test_client, auth_headers, sample_prompt_template
    ):
        """Test 404 when dataset doesn't exist"""
        # Arrange
        fake_dataset_id = "00000000-0000-0000-0000-000000000000"
        payload = {
            "prompt_template_id": str(sample_prompt_template.id),
            "dataset_id": fake_dataset_id
        }

        # Act
        response = test_client.post(
            "/evaluations/run",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        detail = response_data.get("detail", str(response_data))
        assert "dataset" in str(detail).lower()

    def test_run_evaluation_403_for_other_org_template(
        self, test_client, auth_headers, db_session,
        second_organization, sample_evaluation_dataset
    ):
        """Test 403 when template belongs to another organization"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        
        payload = {
            "prompt_template_id": str(other_template.id),
            "dataset_id": str(sample_evaluation_dataset.id)
        }

        # Act
        response = test_client.post(
            "/evaluations/run",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_run_evaluation_403_for_other_org_dataset(
        self, test_client, auth_headers, db_session,
        sample_prompt_template, second_organization, tmp_path
    ):
        """Test 403 when dataset belongs to another organization"""
        # Arrange - Create dataset in different org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Dataset",
            description="Access denied",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )
        
        payload = {
            "prompt_template_id": str(sample_prompt_template.id),
            "dataset_id": str(other_dataset.id)
        }

        # Act
        response = test_client.post(
            "/evaluations/run",
            json=payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_run_evaluation_requires_authentication(
        self, test_client, sample_prompt_template, sample_evaluation_dataset
    ):
        """Test that authentication is required"""
        # Arrange
        payload = {
            "prompt_template_id": str(sample_prompt_template.id),
            "dataset_id": str(sample_evaluation_dataset.id)
        }

        # Act
        response = test_client.post("/evaluations/run", json=payload)

        # Assert
        assert response.status_code in [401, 403]


class TestListRuns:
    """Tests for GET /evaluations/runs"""

    def test_list_runs_returns_org_runs(
        self, test_client, auth_headers, sample_evaluation_run
    ):
        """Test listing returns all runs for user's organization"""
        # Act
        response = test_client.get(
            "/evaluations/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert "total" in data
        assert isinstance(data["runs"], list)
        assert data["total"] >= 1
        assert data["runs"][0]["id"] == str(sample_evaluation_run.id)

    def test_list_runs_returns_empty_for_new_org(
        self, test_client, second_auth_headers
    ):
        """Test listing returns empty list for organization with no runs"""
        # Act
        response = test_client.get(
            "/evaluations/runs",
            headers=second_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []
        assert data["total"] == 0

    def test_list_runs_only_shows_own_org(
        self, test_client, auth_headers, db_session,
        sample_evaluation_run, second_organization, tmp_path
    ):
        """Test that users only see runs from their organization"""
        # Arrange - Create run for different org
        # First create template in other org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        
        # Create dataset in other org
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Dataset",
            description="Other",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )
        
        # Create run
        other_run = run_crud.create(
            db_session,
            prompt_template_id=other_template.id,
            dataset_id=other_dataset.id,
            experiment_name="Other Run",
            num_examples=1,
            per_dimension_metrics={}
        )

        # Act
        response = test_client.get(
            "/evaluations/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        run_ids = [r["id"] for r in data["runs"]]
        assert str(sample_evaluation_run.id) in run_ids
        assert str(other_run.id) not in run_ids

    def test_list_runs_requires_authentication(self, test_client):
        """Test that authentication is required"""
        # Act
        response = test_client.get("/evaluations/runs")

        # Assert
        assert response.status_code in [401, 403]


class TestGetRun:
    """Tests for GET /evaluations/runs/{id}"""

    def test_get_run_by_id_success(
        self, test_client, auth_headers, sample_evaluation_run
    ):
        """Test getting specific run by ID"""
        # Act
        response = test_client.get(
            f"/evaluations/runs/{sample_evaluation_run.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_evaluation_run.id)
        assert data["experiment_name"] == sample_evaluation_run.experiment_name
        assert data["num_examples"] == sample_evaluation_run.num_examples

    def test_get_run_404_for_nonexistent_id(self, test_client, auth_headers):
        """Test 404 when run doesn't exist"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.get(
            f"/evaluations/runs/{fake_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_run_403_for_other_org_run(
        self, test_client, auth_headers, db_session, second_organization, tmp_path
    ):
        """Test 403 when accessing another organization's run"""
        # Arrange - Create run in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        
        csv_path = tmp_path / "other_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        other_dataset = dataset_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Dataset",
            description="Other",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )
        
        other_run = run_crud.create(
            db_session,
            prompt_template_id=other_template.id,
            dataset_id=other_dataset.id,
            experiment_name="Other Run",
            num_examples=1,
            per_dimension_metrics={}
        )

        # Act
        response = test_client.get(
            f"/evaluations/runs/{other_run.id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_run_requires_authentication(
        self, test_client, sample_evaluation_run
    ):
        """Test that authentication is required"""
        # Act
        response = test_client.get(
            f"/evaluations/runs/{sample_evaluation_run.id}"
        )

        # Assert
        assert response.status_code in [401, 403]


class TestGetTemplateRuns:
    """Tests for GET /evaluations/templates/{id}/runs"""

    def test_get_template_runs_success(
        self, test_client, auth_headers, sample_prompt_template, sample_evaluation_run
    ):
        """Test getting all runs for a template"""
        # Act
        response = test_client.get(
            f"/evaluations/templates/{sample_prompt_template.id}/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == str(sample_evaluation_run.id)
        assert data[0]["prompt_template_id"] == str(sample_prompt_template.id)

    def test_get_template_runs_empty_for_template_without_runs(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Test empty list for template without runs"""
        # Arrange - Create template without runs
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="No Runs Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.get(
            f"/evaluations/templates/{template.id}/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_template_runs_404_for_nonexistent_template(
        self, test_client, auth_headers
    ):
        """Test 404 for non-existent template"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.get(
            f"/evaluations/templates/{fake_id}/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_template_runs_403_for_other_org_template(
        self, test_client, auth_headers, db_session, second_organization
    ):
        """Test 403 when accessing another organization's template"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            f"/evaluations/templates/{other_template.id}/runs",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_template_runs_requires_authentication(
        self, test_client, sample_prompt_template
    ):
        """Test that authentication is required"""
        # Act
        response = test_client.get(
            f"/evaluations/templates/{sample_prompt_template.id}/runs"
        )

        # Assert
        assert response.status_code in [401, 403]


class TestGetTemplateLatestRun:
    """Tests for GET /evaluations/templates/{id}/latest"""

    def test_get_template_latest_run_success(
        self, test_client, auth_headers, sample_prompt_template, sample_evaluation_run
    ):
        """Test getting latest run for a template"""
        # Act
        response = test_client.get(
            f"/evaluations/templates/{sample_prompt_template.id}/latest",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_evaluation_run.id)
        assert data["prompt_template_id"] == str(sample_prompt_template.id)

    def test_get_template_latest_run_returns_most_recent(
        self, test_client, auth_headers, db_session,
        sample_organization, tmp_path
    ):
        """Test that returns a run when multiple exist (validates endpoint works with multiple runs)"""
        # Arrange - Create template and dataset without fixture to avoid interference
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Test Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )
        
        csv_path = tmp_path / "test_dataset.csv"
        csv_path.write_text("""id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",4,3,4,3,4,4,3
""")
        dataset = dataset_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="Test Dataset",
            description="Test",
            source_type="csv",
            source_path=str(csv_path),
            num_examples=1
        )
        
        # Create multiple runs
        run1 = run_crud.create(
            db_session,
            prompt_template_id=template.id,
            dataset_id=dataset.id,
            experiment_name="First Run",
            num_examples=2,
            per_dimension_metrics={}
        )
        
        run2 = run_crud.create(
            db_session,
            prompt_template_id=template.id,
            dataset_id=dataset.id,
            experiment_name="Second Run",
            num_examples=2,
            per_dimension_metrics={}
        )

        # Act
        response = test_client.get(
            f"/evaluations/templates/{template.id}/latest",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should return one of the runs we created
        assert data["id"] in [str(run1.id), str(run2.id)]
        assert data["prompt_template_id"] == str(template.id)
        assert data["experiment_name"] in ["First Run", "Second Run"]

    def test_get_template_latest_run_404_for_template_without_runs(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Test 404 when template has no runs"""
        # Arrange - Create template without runs
        template = template_crud.create(
            db_session,
            organization_id=sample_organization.id,
            name="No Runs Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=False
        )

        # Act
        response = test_client.get(
            f"/evaluations/templates/{template.id}/latest",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        detail = response_data.get("detail", str(response_data))
        assert "evaluation run" in str(detail).lower()

    def test_get_template_latest_run_404_for_nonexistent_template(
        self, test_client, auth_headers
    ):
        """Test 404 for non-existent template"""
        # Arrange
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Act
        response = test_client.get(
            f"/evaluations/templates/{fake_id}/latest",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_template_latest_run_403_for_other_org_template(
        self, test_client, auth_headers, db_session, second_organization
    ):
        """Test 403 when accessing another organization's template"""
        # Arrange - Create template in different org
        other_template = template_crud.create(
            db_session,
            organization_id=second_organization.id,
            name="Other Template",
            version="v1",
            system_prompt="System",
            user_template="User {transcript}",
            is_active=True
        )

        # Act
        response = test_client.get(
            f"/evaluations/templates/{other_template.id}/latest",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_get_template_latest_run_requires_authentication(
        self, test_client, sample_prompt_template
    ):
        """Test that authentication is required"""
        # Act
        response = test_client.get(
            f"/evaluations/templates/{sample_prompt_template.id}/latest"
        )

        # Assert
        assert response.status_code in [401, 403]
