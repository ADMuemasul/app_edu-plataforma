#!/usr/bin/env python3
"""
Script de Execução Simplificado
==============================

Script simples para executar rapidamente a aplicação de correção.
Para uso mais avançado, utilize main.py com argumentos.
"""

import sys
from pathlib import Path

# Adicionar path para imports
sys.path.append(str(Path(__file__).parent.parent))

from main import main

if __name__ == '__main__':
    # Se não houver argumentos, executar em modo API
    if len(sys.argv) == 1:
        sys.argv.extend(['--mode', 'api', '--debug'])
    
    main() 