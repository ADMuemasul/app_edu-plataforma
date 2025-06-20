# Sistema de Correção Automática de Gabaritos

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Sistema completo para correção automática de gabaritos educacionais usando técnicas de **OCR (Optical Character Recognition)** e **OMR (Optical Mark Recognition)**.

## 🎯 Funcionalidades Principais

### ✅ Processamento de Gabaritos
- **Múltiplos formatos**: PDF, JPG, PNG, TIFF
- **Templates configuráveis**: Santa Quitéria, Padrão Sistema
- **Correção automática de perspectiva**
- **Normalização de iluminação**
- **Detecção inteligente de marcações**

### 🔍 Extração de Dados
- **OCR avançado** para dados do cabeçalho (nome, escola, turma)
- **OMR preciso** para detecção de respostas marcadas
- **Validação automática** de consistência
- **Relatórios de qualidade** da detecção

### 📊 Correção e Análise
- **Correção automática** baseada em gabarito oficial
- **Estatísticas detalhadas** por aluno e turma
- **Feedback personalizado** por questão
- **Identificação de padrões** suspeitos

### 🔄 Múltiplos Modos de Uso
- **API REST** para integração com sistemas
- **Interface de linha de comando** para uso avulso
- **Processamento em lote** para turmas completas
- **Modo daemon** para processamento contínuo

## 🏗️ Arquitetura

```
app_correção/
├── core/                    # Funcionalidades principais
│   ├── scanner.py          # Escaneamento e análise
│   ├── corrector.py        # Correção automática
│   └── validator.py        # Validação de resultados
├── processing/             # Processamento de imagens
│   ├── image_processor.py  # Processador principal
│   ├── filters.py          # Filtros e melhorias
│   └── perspective.py      # Correção de perspectiva
├── ocr/                   # Reconhecimento óptico
│   ├── reader.py          # OCR principal
│   └── engines.py         # Diferentes engines OCR
├── api/                   # Interface REST
│   ├── app.py             # Aplicação Flask
│   ├── routes.py          # Endpoints
│   └── middleware.py      # Middleware
├── reports/               # Geração de relatórios
│   ├── generator.py       # Gerador principal
│   └── templates/         # Templates de relatório
├── utils/                 # Utilitários
│   ├── statistics.py      # Cálculos estatísticos
│   ├── geometry.py        # Geometria e transformações
│   └── quality_metrics.py # Métricas de qualidade
└── main.py               # Script principal
```

## 🚀 Instalação

### 1. Pré-requisitos

```bash
# Python 3.8 ou superior
python --version

# Tesseract OCR (para Windows)
# Baixar e instalar: https://github.com/UB-Mannheim/tesseract/wiki

# Para Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-por

# Para macOS
brew install tesseract tesseract-lang
```

### 2. Instalar Dependências

```bash
# Navegar para o diretório
cd backend/app_correção

# Instalar dependências Python
pip install -r requirements.txt
```

### 3. Configuração

```bash
# Copiar arquivo de configuração (se necessário)
cp config.py.example config.py

# Editar configurações conforme necessário
nano config.py
```

## 📖 Uso

### Modo API Server

```bash
# Iniciar servidor API
python main.py --mode api --port 5001

# Com debug habilitado
python main.py --mode api --debug

# Endpoints disponíveis:
# POST /api/upload     - Upload de gabaritos
# GET  /api/jobs/<id>  - Status do processamento
# GET  /api/results/<id> - Resultados da correção
```

### Modo Linha de Comando

```bash
# Processar um único gabarito
python main.py --mode cli --file gabarito.pdf

# Com gabarito oficial
python main.py --mode cli --file gabarito.pdf --gabarito oficial.json

# Especificar template
python main.py --mode cli --file gabarito.pdf --template santa_quiteria
```

### Modo Processamento em Lote

```bash
# Processar pasta de gabaritos
python main.py --mode batch --input pasta_gabaritos/ --output resultados/

# Com gabarito oficial
python main.py --mode batch --input pasta/ --output resultados/ --gabarito oficial.json
```

## 🔧 Configuração de Templates

### Template Santa Quitéria

```python
GABARITO_CONFIGS = {
    'santa_quiteria': {
        'areas_deteccao': {
            'cabecalho': {'x': 0, 'y': 0, 'width': 595, 'height': 150},
            'bloco_01': {'x': 50, 'y': 200, 'width': 250, 'height': 400},
            'bloco_02': {'x': 350, 'y': 200, 'width': 250, 'height': 400}
        },
        'marcacoes_por_questao': 4,  # A, B, C, D
        'questoes_por_bloco': 15,
        'tolerancia_marcacao': 0.3
    }
}
```

### Gabarito Oficial (JSON)

```json
{
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": "A",
    ...
    "30": "C"
}
```

## 📊 Exemplo de Resultado

```json
{
    "student_info": {
        "nome": "João Silva",
        "escola": "Escola Municipal",
        "turma": "5º A",
        "serie": "5"
    },
    "summary": {
        "total_questoes": 30,
        "acertos": 24,
        "erros": 4,
        "em_branco": 2,
        "pontuacao": 80.0,
        "percentual": 80.0,
        "conceito": "B"
    },
    "questoes": {
        "1": {
            "resposta_aluno": "A",
            "resposta_correta": "A",
            "status": "correto",
            "pontos": 1.0
        },
        ...
    },
    "feedback": {
        "geral": "Muito bom! Bom domínio do conteúdo com pequenas lacunas.",
        "recomendacoes": ["Revisar questões 15-18"],
        "pontos_fortes": ["Boa compreensão geral do conteúdo"]
    }
}
```

## 🔌 API Endpoints

### Upload de Gabarito

```bash
POST /api/upload
Content-Type: multipart/form-data

# Parâmetros:
# - file: Arquivo do gabarito (PDF/imagem)
# - template: Tipo de template (opcional)
# - gabarito_oficial: ID ou JSON do gabarito (opcional)

curl -X POST \
  -F "file=@gabarito.pdf" \
  -F "template=santa_quiteria" \
  http://localhost:5001/api/upload
```

### Consultar Status

```bash
GET /api/jobs/{job_id}

# Resposta:
{
    "job_id": "JOB_20240101_120000",
    "status": "processing|completed|failed",
    "progress": 75,
    "estimated_time": 30,
    "result_id": "RESULT_123" # se concluído
}
```

### Obter Resultados

```bash
GET /api/results/{result_id}

# Resposta: JSON com resultado completo da correção
```

## 🧪 Qualidade e Validação

### Métricas de Qualidade

- **Resolução da imagem**: Verificação de DPI adequado
- **Nitidez**: Análise de foco e clareza
- **Contraste**: Avaliação de legibilidade
- **Alinhamento**: Detecção de inclinação/perspectiva

### Validação Automática

- **Consistência de dados**: Verificação de campos obrigatórios
- **Padrões suspeitos**: Detecção de marcações anômalas
- **Completude**: Análise de questões não respondidas
- **Confiança**: Score geral da detecção

## 📈 Estatísticas e Relatórios

### Estatísticas por Aluno
- Pontuação total e percentual
- Distribuição de acertos/erros
- Análise por questão
- Recomendações personalizadas

### Estatísticas da Turma
- Média e desvio padrão
- Distribuição de conceitos
- Questões mais erradas
- Ranking de desempenho

### Exportação
- **JSON**: Dados estruturados completos
- **Excel**: Planilhas para análise
- **PDF**: Relatórios formatados
- **CSV**: Dados tabulares simples

## 🐛 Troubleshooting

### Problemas Comuns

**Erro: "Tesseract não encontrado"**
```bash
# Configurar caminho do Tesseract
export TESSERACT_CMD=/usr/bin/tesseract
# ou editar config.py
```

**Baixa precisão de detecção**
- Verificar qualidade da imagem (300 DPI recomendado)
- Garantir boa iluminação
- Verificar alinhamento do gabarito
- Ajustar parâmetros de detecção

**Erro de importação**
```bash
# Verificar instalação das dependências
pip install -r requirements.txt

# Verificar OpenCV
python -c "import cv2; print(cv2.__version__)"
```

### Logs e Debug

```bash
# Executar com debug
python main.py --mode api --debug --log-level DEBUG

# Logs são salvos em:
logs/correção_YYYY-MM-DD.log
```

## 🤝 Contribuição

1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License. Veja [LICENSE](LICENSE) para detalhes.

## 🔗 Links Úteis

- [OpenCV Documentation](https://docs.opencv.org/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Loguru Logging](https://github.com/Delgan/loguru)

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma [Issue](../../issues)
- Entre em contato com a equipe de desenvolvimento
- Consulte a documentação completa

---

**Desenvolvido pela Equipe EduPlataforma** 🎓 