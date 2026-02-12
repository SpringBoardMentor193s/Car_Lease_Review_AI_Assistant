from fastapi import APIRouter, HTTPException, Depends
import logging
import json
from pathlib import Path

from negotiation_assistant.models.negotiation import (
    NegotiationRequest, 
    EmailGenerationRequest,
    NegotiationPoint
)
from negotiation_assistant.engine.negotiator import Negotiator
from negotiation_assistant.api.schemas import (
    NegotiationAssistantRequest, 
    NegotiationAssistantResponse,
    EmailGenerationRequestSchema,
    EmailTemplateResponseSchema
)

# Import from fairness_score_engine
from database.db import ContractFactsDB
from pipelines.scoring_pipeline import ScoringPipeline
from models.contract_facts import ContractFacts

logger = logging.getLogger(__name__)

router = APIRouter()

def get_negotiator():
    return Negotiator()

def get_db():
    # Use absolute path for database
    db_path = Path(__file__).resolve().parent.parent.parent / "fairness_score_engine" / "contract_facts.db"
    return ContractFactsDB(str(db_path))

def get_scoring_pipeline():
    # Use absolute paths to avoid issues with different CWDs
    base_dir = Path(__file__).resolve().parent.parent.parent / "fairness_score_engine"
    return ScoringPipeline(
        rules_path=str(base_dir / "data" / "scoring_rules.json"),
        benchmarks_path=str(base_dir / "data" / "market_benchmarks.json")
    )

@router.post("/negotiate", response_model=NegotiationAssistantResponse)
async def generate_negotiation_strategy(
    request: NegotiationAssistantRequest,
    negotiator: Negotiator = Depends(get_negotiator),
    db: ContractFactsDB = Depends(get_db),
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Generate a negotiation strategy from a stored contract record.
    """
    try:
        fact_fields = set(ContractFacts.__fields__.keys())
        db_facts = db.get_contract_facts_by_id(request.record_id)
        if not db_facts:
            raise HTTPException(status_code=404, detail=f"Record {request.record_id} not found")

        # Keep only ContractFacts fields (drop DB metadata such as id/created_at)
        contract_facts = {k: v for k, v in db_facts.items() if k in fact_fields}
        report = scoring_pipeline.run(contract_facts)
        # Convert Decimals/Enums to JSON-safe primitives.
        fairness_report = json.loads(report.json())

        # Convert API schema to engine model
        engine_request = NegotiationRequest(
            contract_facts=contract_facts,
            fairness_report=fairness_report,
            market_data=scoring_pipeline.benchmarks
        )
        
        # Generate strategy
        strategy = negotiator.generate_strategy(engine_request)
        
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating negotiation strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-email", response_model=EmailTemplateResponseSchema)
async def generate_email(
    request: EmailGenerationRequestSchema,
    negotiator: Negotiator = Depends(get_negotiator),
    db: ContractFactsDB = Depends(get_db),
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Auto-generate a professional negotiation email from a stored contract record.
    """
    try:
        fact_fields = set(ContractFacts.__fields__.keys())
        db_facts = db.get_contract_facts_by_id(request.record_id)
        if not db_facts:
            raise HTTPException(status_code=404, detail=f"Record {request.record_id} not found")

        contract_facts = {k: v for k, v in db_facts.items() if k in fact_fields}
        report = scoring_pipeline.run(contract_facts)
        fairness_report = json.loads(report.json())

        strategy_request = NegotiationRequest(
            contract_facts=contract_facts,
            fairness_report=fairness_report,
            market_data=scoring_pipeline.benchmarks,
        )
        strategy = negotiator.generate_strategy(strategy_request)
        if not strategy.contract_specific_points:
            raise HTTPException(
                status_code=422,
                detail="No contract-specific negotiation points were generated for this record",
            )

        engine_request = EmailGenerationRequest(
            contract_facts=contract_facts,
            negotiation_points=[
                NegotiationPoint(**p.dict()) for p in strategy.contract_specific_points
            ],
            user_tone=request.user_tone,
        )

        email_template = negotiator.generate_email(engine_request)
        return email_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
