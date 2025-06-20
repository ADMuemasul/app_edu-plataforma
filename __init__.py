"""
Aplicação de Correção Automática de Gabaritos
============================================

Este módulo contém todas as funcionalidades para:
- Processamento de imagens de gabaritos
- Detecção OCR/OMR de marcações
- Análise e correção automática
- Geração de relatórios de resultados

Estrutura:
- core/: Funcionalidades principais
- processing/: Processamento de imagens
- ocr/: Reconhecimento óptico
- reports/: Geração de relatórios
- api/: Endpoints da API REST
- utils/: Utilitários diversos
"""

__version__ = "1.0.0"
__author__ = "Equipe EduPlataforma"

from .core.scanner import GabaritoScanner
from .core.corrector import AutoCorrector
from .processing.image_processor import ImageProcessor
from .ocr.reader import OCRReader
from .reports.generator import ReportGenerator

__all__ = [
    'GabaritoScanner',
    'AutoCorrector', 
    'ImageProcessor',
    'OCRReader',
    'ReportGenerator'
] 