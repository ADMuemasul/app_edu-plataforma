"""
Configurações da Aplicação de Correção Automática
================================================

Centralizando todas as configurações para facilitar manutenção
e permitir diferentes ambientes (dev, test, prod).
"""

import os
from pathlib import Path

# Diretórios Base
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
UPLOADS_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

# Criar diretórios necessários
for directory in [UPLOADS_DIR, TEMP_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(exist_ok=True)

class Config:
    """Configuração base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-correcao-2024'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///correcao.db'
    
    # Uploads
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'}
    UPLOAD_FOLDER = str(UPLOADS_DIR)
    
    # OCR Configurações
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or 'tesseract'
    OCR_LANGUAGES = ['por', 'eng']  # Português e Inglês
    
    # Processamento de Imagem
    IMAGE_DPI = 300
    IMAGE_QUALITY = 95
    GABARITO_TEMPLATE_SIMILARITY_THRESHOLD = 0.8
    
    # Machine Learning
    ML_MODEL_CONFIDENCE_THRESHOLD = 0.85
    ML_BATCH_SIZE = 32
    
    # API
    API_RATE_LIMIT = "1000 per hour"
    API_TIMEOUT = 300  # 5 minutos
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
    
    # Processamento
    MAX_CONCURRENT_JOBS = 4
    PROCESSING_TIMEOUT = 600  # 10 minutos por gabarito

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATABASE_URL = 'sqlite:///correcao_dev.db'

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB para testes
    LOG_LEVEL = "WARNING"

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    # Em produção, usar MySQL
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'mysql://user:pass@localhost/correcao'

# Configurações específicas por tipo de gabarito
GABARITO_CONFIGS = {
    'santa_quiteria': {
        'template_path': 'templates/santa_quiteria_template.pdf',
        'areas_deteccao': {
            'cabecalho': {'x': 0, 'y': 0, 'width': 595, 'height': 150},
            'bloco_01': {'x': 50, 'y': 200, 'width': 250, 'height': 400},
            'bloco_02': {'x': 350, 'y': 200, 'width': 250, 'height': 400}
        },
        'marcacoes_por_questao': 4,  # A, B, C, D
        'questoes_por_bloco': 15,
        'tolerancia_marcacao': 0.3
    },
    'padrao_sistema': {
        'template_path': 'templates/padrao_template.pdf',
        'areas_deteccao': {
            'cabecalho': {'x': 0, 'y': 0, 'width': 595, 'height': 100},
            'gabarito': {'x': 50, 'y': 150, 'width': 500, 'height': 600}
        },
        'marcacoes_por_questao': 4,
        'questoes_por_bloco': 20,
        'tolerancia_marcacao': 0.25
    }
}

# Configurações de Detecção
DETECTION_SETTINGS = {
    # Parâmetros para detecção de círculos (marcações)
    'circle_detection': {
        'dp': 1,
        'min_dist': 30,
        'param1': 50,
        'param2': 30,
        'min_radius': 8,
        'max_radius': 25
    },
    
    # Parâmetros para detecção de contornos
    'contour_detection': {
        'threshold_min': 127,
        'threshold_max': 255,
        'min_area': 100,
        'max_area': 5000
    },
    
    # Parâmetros para correção de perspectiva
    'perspective_correction': {
        'corners_detection_accuracy': 0.02,
        'corner_refinement': True,
        'max_rotation_angle': 15  # graus
    }
}

# Seleção de configuração por ambiente
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Retorna configuração baseada no ambiente"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'default')
    return config_map.get(env, DevelopmentConfig) 