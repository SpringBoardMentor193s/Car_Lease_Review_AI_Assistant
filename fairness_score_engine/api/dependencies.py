"""
API dependencies for the Car Lease Review AI Assistant
"""

from database.db import ContractFactsDB
from pipelines.extract_pipeline import ExtractPipeline

def get_db() -> ContractFactsDB:
    """Dependency to get database instance"""
    return ContractFactsDB()

def get_extract_pipeline() -> ExtractPipeline:
    """Dependency to get extraction pipeline instance"""
    return ExtractPipeline()
