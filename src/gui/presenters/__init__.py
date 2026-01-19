# Presenter Layer - Logica di presentazione
# Pattern MVP: Model-View-Presenter

from .base_presenter import BasePresenter
from .input_presenter import InputPresenter
from .openings_presenter import OpeningsPresenter
from .calc_presenter import CalcPresenter

__all__ = [
    'BasePresenter',
    'InputPresenter',
    'OpeningsPresenter',
    'CalcPresenter'
]
