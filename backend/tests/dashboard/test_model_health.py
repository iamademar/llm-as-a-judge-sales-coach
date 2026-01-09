"""
Unit tests for GET /overview/model-health endpoint.

Tests cover:
- Returns None when no active template
- Returns None when no evaluation run exists
- Returns None when evaluation has no macro_qwk
- Returns valid response with evaluation data
- Status derivation from QWK (healthy >= 0.70, warning >= 0.50, critical < 0.50)
- Average latency calculation from recent 100 assessments
- Latency is None when no assessment data
- Organization filtering (uses current user's org)
- Filters assessments by model_name
- Uses active template's version
"""
import pytest
from datetime import datetime, timedelta

from app.models import Representative, Transcript, Assessment
from app.models.prompt_template import PromptTemplate
from app.models.evaluation_run import EvaluationRun


class TestModelHealthBasics:
    """Tests for basic model health functionality"""

    def test_model_health_returns_none_when_no_active_template(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify endpoint returns None when no active template exists"""
        # Act: No active template in database
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should return None (null in JSON)
        assert response.status_code == 200
        assert response.json() is None

    def test_model_health_returns_none_when_no_evaluation_run(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify endpoint returns None when no evaluation run exists for active template"""
        # Arrange: Create active template without evaluation run
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json() is None

    def test_model_health_returns_none_when_no_macro_qwk(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify endpoint returns None when evaluation run has no macro_qwk"""
        # Arrange: Create active template with evaluation run but no macro_qwk
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.75,
            macro_qwk=None  # No QWK score
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json() is None

    def test_model_health_returns_valid_response(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify endpoint returns complete health data with evaluation"""
        # Arrange: Create active template with evaluation run
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.78,
            macro_qwk=0.73
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data is not None
        assert "model_name" in data
        assert "prompt_version" in data
        assert "last_eval_date" in data
        assert "macro_pearson_r" in data
        assert "macro_qwk" in data
        assert "avg_latency_ms" in data
        assert "status" in data
        
        assert data["model_name"] == "gpt-4o-mini"
        assert data["prompt_version"] == "v1"
        assert data["macro_pearson_r"] == 0.78
        assert data["macro_qwk"] == 0.73


class TestModelHealthStatus:
    """Tests for status derivation from QWK score"""

    def test_model_health_status_healthy(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify status is 'healthy' when QWK >= 0.70"""
        # Arrange: QWK = 0.75 (healthy)
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.80,
            macro_qwk=0.75
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_model_health_status_warning(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify status is 'warning' when 0.50 <= QWK < 0.70"""
        # Arrange: QWK = 0.60 (warning)
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.65,
            macro_qwk=0.60
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"

    def test_model_health_status_critical(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify status is 'critical' when QWK < 0.50"""
        # Arrange: QWK = 0.40 (critical)
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.45,
            macro_qwk=0.40
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "critical"

    def test_model_health_status_boundary_healthy(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify status is 'healthy' at QWK = 0.70 (boundary)"""
        # Arrange: QWK = 0.70 (exactly at healthy threshold)
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.75,
            macro_qwk=0.70
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_model_health_status_boundary_warning(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify status is 'warning' at QWK = 0.50 (boundary)"""
        # Arrange: QWK = 0.50 (exactly at warning threshold)
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.55,
            macro_qwk=0.50
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"


class TestModelHealthLatency:
    """Tests for average latency calculation"""

    def test_model_health_latency_with_assessment_data(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify average latency is calculated from recent assessments"""
        # Arrange: Create active template with evaluation
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.78,
            macro_qwk=0.73
        )
        db_session.add(eval_run)
        db_session.commit()

        # Create representative and assessments with latency data
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Create 3 assessments with latencies: 1000, 1200, 1400 (avg = 1200)
        for i, latency in enumerate([1000, 1200, 1400]):
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Conversation {i}",
                metadata={}
            )
            db_session.add(transcript)
            db_session.commit()

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 4, "problem": 4, "implication": 4,
                    "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1",
                latency_ms=latency
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["avg_latency_ms"] == 1200

    def test_model_health_latency_none_when_no_assessments(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify latency is None when no assessment data exists"""
        # Arrange: Create active template with evaluation but no assessments
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.78,
            macro_qwk=0.73
        )
        db_session.add(eval_run)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["avg_latency_ms"] is None

    def test_model_health_latency_filters_by_model_name(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify latency calculation only includes assessments from same model"""
        # Arrange: Create active template with evaluation for gpt-4o-mini
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.78,
            macro_qwk=0.73
        )
        db_session.add(eval_run)
        db_session.commit()

        # Create representative
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Create assessment with matching model (should be included)
        t1 = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-001",
            transcript="Conversation 1",
            metadata={}
        )
        db_session.add(t1)
        db_session.commit()

        a1 = Assessment(
            transcript_id=t1.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4o-mini",  # Matches
            prompt_version="v1",
            latency_ms=1000
        )
        db_session.add(a1)

        # Create assessment with different model (should NOT be included)
        t2 = Transcript(
            representative_id=rep.id,
            buyer_id="BUYER-002",
            transcript="Conversation 2",
            metadata={}
        )
        db_session.add(t2)
        db_session.commit()

        a2 = Assessment(
            transcript_id=t2.id,
            scores={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            },
            coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
            model_name="gpt-4",  # Different model
            prompt_version="v1",
            latency_ms=5000  # High latency, should not affect result
        )
        db_session.add(a2)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should only use gpt-4o-mini assessment (1000ms)
        assert response.status_code == 200
        data = response.json()
        assert data["avg_latency_ms"] == 1000

    def test_model_health_latency_limits_to_100_assessments(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify latency calculation uses only most recent 100 assessments"""
        # Arrange: Create active template with evaluation
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        eval_run = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.78,
            macro_qwk=0.73
        )
        db_session.add(eval_run)
        db_session.commit()

        # Create representative
        rep = Representative(
            email="rep@test.com",
            full_name="Test Rep",
            organization_id=sample_organization.id,
            is_active=True
        )
        db_session.add(rep)
        db_session.commit()

        # Create 105 assessments with different timestamps
        # Oldest 5 have latency 5000, newest 100 have latency 1000
        for i in range(105):
            assessment_time = datetime.utcnow() - timedelta(hours=105-i)  # Oldest first
            
            transcript = Transcript(
                representative_id=rep.id,
                buyer_id=f"BUYER-{i:03d}",
                transcript=f"Conversation {i}",
                metadata={},
                created_at=assessment_time
            )
            db_session.add(transcript)
            db_session.commit()

            # First 5 have high latency, rest have low latency
            latency = 5000 if i < 5 else 1000

            assessment = Assessment(
                transcript_id=transcript.id,
                scores={
                    "situation": 4, "problem": 4, "implication": 4,
                    "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
                },
                coaching={"summary": "Test", "wins": [], "gaps": [], "next_actions": []},
                model_name="gpt-4o-mini",
                prompt_version="v1",
                latency_ms=latency,
                created_at=assessment_time  # Set assessment created_at to match transcript
            )
            db_session.add(assessment)

        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should use only most recent 100 (all with 1000ms latency)
        assert response.status_code == 200
        data = response.json()
        assert data["avg_latency_ms"] == 1000  # Not affected by old high-latency assessments


class TestModelHealthFiltering:
    """Tests for organization and template filtering"""

    def test_model_health_organization_filtering(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify model health only uses data from user's organization"""
        # Arrange: Create another organization
        from app.models.organization import Organization
        
        other_org = Organization(name="Other Org")
        db_session.add(other_org)
        db_session.commit()

        # Create template in other org (should NOT be used)
        other_template = PromptTemplate(
            organization_id=other_org.id,
            version="v_other",
            name="Other Template",
            system_prompt="Other system prompt",
            user_template="Other user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(other_template)
        db_session.commit()

        other_eval = EvaluationRun(
            prompt_template_id=other_template.id,
            model_name="gpt-4",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.50,
            macro_qwk=0.40
        )
        db_session.add(other_eval)

        # Create template in current user's org (should be used)
        my_template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="My Template",
            system_prompt="My system prompt",
            user_template="My user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(my_template)
        db_session.commit()

        my_eval = EvaluationRun(
            prompt_template_id=my_template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.80,
            macro_qwk=0.75
        )
        db_session.add(my_eval)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should use my org's data
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["model_name"] == "gpt-4o-mini"  # Not "gpt-4"
        assert data["prompt_version"] == "v1"  # Not "v_other"
        assert data["macro_qwk"] == 0.75  # Not 0.40

    def test_model_health_uses_active_template(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify model health uses only the active template"""
        # Arrange: Create inactive template
        inactive_template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v_old",
            name="Old Template",
            system_prompt="Old system prompt",
            user_template="Old user prompt with {transcript} placeholder",
            is_active=False  # Inactive
        )
        db_session.add(inactive_template)
        db_session.commit()

        inactive_eval = EvaluationRun(
            prompt_template_id=inactive_template.id,
            model_name="gpt-3.5",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.50,
            macro_qwk=0.40
        )
        db_session.add(inactive_eval)

        # Create active template
        active_template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v_current",
            name="Current Template",
            system_prompt="Current system prompt",
            user_template="Current user prompt with {transcript} placeholder",
            is_active=True  # Active
        )
        db_session.add(active_template)
        db_session.commit()

        active_eval = EvaluationRun(
            prompt_template_id=active_template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.80,
            macro_qwk=0.75
        )
        db_session.add(active_eval)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should use active template's data
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["model_name"] == "gpt-4o-mini"  # Not "gpt-3.5"
        assert data["prompt_version"] == "v_current"  # Not "v_old"
        assert data["macro_qwk"] == 0.75  # Not 0.40

    def test_model_health_uses_latest_evaluation_run(
        self, test_client, auth_headers, db_session, sample_organization
    ):
        """Verify model health uses most recent evaluation run for active template"""
        # Arrange: Create active template with 2 evaluation runs
        template = PromptTemplate(
            organization_id=sample_organization.id,
            version="v1",
            name="Test Template",
            system_prompt="Test system prompt",
            user_template="Test user prompt with {transcript} placeholder",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        # Older evaluation run
        old_eval = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.60,
            macro_qwk=0.55,
            created_at=datetime.utcnow() - timedelta(days=7)
        )
        db_session.add(old_eval)

        # Newer evaluation run (should be used)
        new_eval = EvaluationRun(
            prompt_template_id=template.id,
            model_name="gpt-4o-mini",
            num_examples=10,
            per_dimension_metrics={},
            macro_pearson_r=0.80,
            macro_qwk=0.75,
            created_at=datetime.utcnow()
        )
        db_session.add(new_eval)
        db_session.commit()

        # Act
        response = test_client.get(
            "/overview/model-health",
            headers=auth_headers
        )

        # Assert: Should use newest evaluation run
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["macro_qwk"] == 0.75  # Not 0.55
        assert data["macro_pearson_r"] == 0.80  # Not 0.60
