# Service Layer - Orchestrazione calcoli
# Questo layer fa da intermediario tra GUI e Domain (Calculators)

from .calculation_service import CalculationService, CalculationResult
from .frame_service import FrameService, FrameResult
from .project_service import ProjectService

__all__ = [
    'CalculationService',
    'CalculationResult',
    'FrameService',
    'FrameResult',
    'ProjectService'
]
