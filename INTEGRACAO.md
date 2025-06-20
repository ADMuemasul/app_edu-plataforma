# Integração com o Sistema Principal

Este documento descreve como integrar o módulo de correção automática com o sistema educacional principal.

## 🔗 Arquitetura de Integração

### Cenário 1: Integração via API
O sistema de correção roda como um serviço separado e o sistema principal consome via API REST.

```
Sistema Principal (app.py)  ←→  API Correção (app_correção)
     ↓                              ↓
   Frontend                    Processamento
     ↓                              ↓
   MySQL                      Resultados JSON
```

### Cenário 2: Integração Direta
O sistema de correção é importado diretamente como módulo Python.

```python
# No app.py principal
from app_correção.core.scanner import GabaritoScanner
from app_correção.core.corrector import AutoCorrector
```

## 🚀 Implementação - Cenário 1 (API)

### 1. Modificar o app.py Principal

```python
import requests
import json
from typing import Dict, List

# Configurações
CORRECAO_API_URL = "http://localhost:5001"

@app.route('/api/cadernos/<int:caderno_id>/processar-gabaritos', methods=['POST'])
def processar_gabaritos_caderno(caderno_id):
    """
    Endpoint para processar gabaritos escaneados de um caderno
    """
    try:
        # Obter arquivos enviados
        files = request.files.getlist('gabaritos')
        if not files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        # Buscar caderno no banco
        caderno = Caderno.query.get(caderno_id)
        if not caderno:
            return jsonify({'error': 'Caderno não encontrado'}), 404
        
        # Criar gabarito oficial baseado no caderno
        gabarito_oficial = criar_gabarito_oficial(caderno)
        
        # Processar cada arquivo
        resultados = []
        for arquivo in files:
            resultado = processar_gabarito_arquivo(arquivo, gabarito_oficial)
            if resultado:
                resultados.append(resultado)
        
        # Salvar resultados no banco
        salvar_resultados_correcao(caderno_id, resultados)
        
        return jsonify({
            'success': True,
            'caderno_id': caderno_id,
            'total_processados': len(resultados),
            'resultados': resultados
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar gabaritos: {str(e)}")
        return jsonify({'error': str(e)}), 500

def processar_gabarito_arquivo(arquivo, gabarito_oficial):
    """
    Envia arquivo para API de correção e retorna resultado
    """
    try:
        # Preparar arquivo para envio
        files = {
            'file': (arquivo.filename, arquivo.stream, arquivo.content_type)
        }
        
        data = {
            'template': 'santa_quiteria',
            'gabarito_oficial': json.dumps(gabarito_oficial)
        }
        
        # Enviar para API de correção
        response = requests.post(
            f"{CORRECAO_API_URL}/api/upload",
            files=files,
            data=data,
            timeout=300  # 5 minutos
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Erro na API de correção: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao processar arquivo {arquivo.filename}: {str(e)}")
        return None

def criar_gabarito_oficial(caderno):
    """
    Cria gabarito oficial baseado nas questões do caderno
    """
    gabarito = {}
    
    # Buscar blocos do caderno
    blocos = BlocoCaderno.query.filter_by(caderno_id=caderno.id).all()
    
    questao_num = 1
    for bloco in blocos:
        # Buscar questões do bloco
        questoes = QuestaoBloco.query.filter_by(bloco_id=bloco.id).all()
        
        for questao in questoes:
            # Buscar resposta correta
            alternativa_correta = AlternativaQuestao.query.filter_by(
                questao_id=questao.id,
                correta=True
            ).first()
            
            if alternativa_correta:
                gabarito[str(questao_num)] = alternativa_correta.letra
            
            questao_num += 1
    
    return gabarito

def salvar_resultados_correcao(caderno_id, resultados):
    """
    Salva resultados da correção no banco de dados
    """
    for resultado in resultados:
        try:
            # Extrair dados do aluno
            student_info = resultado.get('student_info', {})
            summary = resultado.get('summary', {})
            
            # Buscar ou criar aluno
            aluno = buscar_ou_criar_aluno(student_info)
            
            # Criar registro de resultado
            resultado_correcao = ResultadoCorrecao(
                caderno_id=caderno_id,
                aluno_id=aluno.id,
                total_questoes=summary.get('total_questoes', 0),
                acertos=summary.get('acertos', 0),
                erros=summary.get('erros', 0),
                em_branco=summary.get('em_branco', 0),
                pontuacao=summary.get('pontuacao', 0),
                percentual=summary.get('percentual', 0),
                conceito=summary.get('conceito', ''),
                dados_completos=json.dumps(resultado)
            )
            
            db.session.add(resultado_correcao)
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultado: {str(e)}")
    
    db.session.commit()
```

### 2. Criar Modelo de Banco para Resultados

```python
class ResultadoCorrecao(db.Model):
    __tablename__ = 'resultado_correcao'
    
    id = db.Column(db.Integer, primary_key=True)
    caderno_id = db.Column(db.Integer, db.ForeignKey('caderno.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    
    # Estatísticas básicas
    total_questoes = db.Column(db.Integer, nullable=False)
    acertos = db.Column(db.Integer, nullable=False)
    erros = db.Column(db.Integer, nullable=False)
    em_branco = db.Column(db.Integer, nullable=False)
    
    # Pontuação
    pontuacao = db.Column(db.Float, nullable=False)
    percentual = db.Column(db.Float, nullable=False)
    conceito = db.Column(db.String(2), nullable=False)
    
    # Dados completos em JSON
    dados_completos = db.Column(db.Text)
    
    # Metadados
    data_processamento = db.Column(db.DateTime, default=datetime.utcnow)
    qualidade_scan = db.Column(db.Float)  # Score de qualidade 0-100
    
    # Relacionamentos
    caderno = db.relationship('Caderno', backref='resultados_correcao')
    aluno = db.relationship('Aluno', backref='resultados_correcao')
```

### 3. Adicionar Endpoints para Consulta

```python
@app.route('/api/cadernos/<int:caderno_id>/resultados', methods=['GET'])
def obter_resultados_caderno(caderno_id):
    """
    Obtém resultados de correção de um caderno
    """
    try:
        resultados = ResultadoCorrecao.query.filter_by(caderno_id=caderno_id).all()
        
        dados = []
        for resultado in resultados:
            dados.append({
                'id': resultado.id,
                'aluno': {
                    'id': resultado.aluno.id,
                    'nome': resultado.aluno.nome
                },
                'estatisticas': {
                    'total_questoes': resultado.total_questoes,
                    'acertos': resultado.acertos,
                    'erros': resultado.erros,
                    'em_branco': resultado.em_branco,
                    'pontuacao': resultado.pontuacao,
                    'percentual': resultado.percentual,
                    'conceito': resultado.conceito
                },
                'data_processamento': resultado.data_processamento.isoformat(),
                'qualidade_scan': resultado.qualidade_scan
            })
        
        return jsonify({
            'success': True,
            'caderno_id': caderno_id,
            'total_resultados': len(dados),
            'resultados': dados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resultados/<int:resultado_id>/detalhes', methods=['GET'])
def obter_detalhes_resultado(resultado_id):
    """
    Obtém detalhes completos de um resultado
    """
    try:
        resultado = ResultadoCorrecao.query.get(resultado_id)
        if not resultado:
            return jsonify({'error': 'Resultado não encontrado'}), 404
        
        # Retornar dados completos
        dados_completos = json.loads(resultado.dados_completos)
        
        return jsonify({
            'success': True,
            'resultado': dados_completos
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 🚀 Implementação - Cenário 2 (Direto)

### 1. Importar Módulos no app.py

```python
# Adicionar ao início do app.py
import sys
from pathlib import Path

# Adicionar path do módulo de correção
sys.path.append(str(Path(__file__).parent / 'app_correção'))

from core.scanner import GabaritoScanner
from core.corrector import AutoCorrector
from core.validator import ResultValidator

# Instanciar componentes globalmente
gabarito_scanner = GabaritoScanner('santa_quiteria')
auto_corrector = AutoCorrector()
result_validator = ResultValidator()
```

### 2. Implementar Processamento Direto

```python
@app.route('/api/cadernos/<int:caderno_id>/processar-gabaritos-direto', methods=['POST'])
def processar_gabaritos_direto(caderno_id):
    """
    Processa gabaritos usando integração direta
    """
    try:
        files = request.files.getlist('gabaritos')
        if not files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        # Buscar caderno
        caderno = Caderno.query.get(caderno_id)
        if not caderno:
            return jsonify({'error': 'Caderno não encontrado'}), 404
        
        # Criar gabarito oficial
        gabarito_oficial = criar_gabarito_oficial(caderno)
        auto_corrector.set_gabarito_oficial(gabarito_oficial)
        
        # Processar arquivos
        resultados = []
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        for arquivo in files:
            try:
                # Salvar arquivo temporariamente
                temp_path = temp_dir / arquivo.filename
                arquivo.save(temp_path)
                
                # Escanear gabarito
                scan_result = gabarito_scanner.scan_file(temp_path)
                
                if scan_result['success'] and scan_result['pages']:
                    page_data = scan_result['pages'][0]
                    
                    # Validar resultado
                    validation = result_validator.validate_scan_result(scan_result)
                    
                    if validation['overall_valid']:
                        # Corrigir gabarito
                        student_info = page_data.get('header_data', {})
                        answers = page_data.get('answers', {})
                        
                        correction_result = auto_corrector.correct_single_student(
                            answers, student_info
                        )
                        
                        resultados.append(correction_result)
                    else:
                        logger.warning(f"Gabarito inválido: {arquivo.filename}")
                
                # Limpar arquivo temporário
                temp_path.unlink()
                
            except Exception as e:
                logger.error(f"Erro ao processar {arquivo.filename}: {str(e)}")
        
        # Salvar resultados
        salvar_resultados_correcao(caderno_id, resultados)
        
        return jsonify({
            'success': True,
            'caderno_id': caderno_id,
            'total_processados': len(resultados),
            'resultados': resultados
        })
        
    except Exception as e:
        logger.error(f"Erro no processamento direto: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

## 🎨 Frontend - Adições ao cadernos.html

### 1. Adicionar Botão de Upload

```html
<!-- Adicionar no modal de detalhes do caderno -->
<div class="caderno-actions-modal">
    <button class="action-btn primary-btn" onclick="gerarGabarito(${caderno.id});">
        <i class="fas fa-file-pdf"></i>
        Gerar Gabarito OCR/OMR
    </button>
    
    <!-- NOVO BOTÃO -->
    <button class="action-btn success-btn" onclick="abrirModalProcessamento(${caderno.id})">
        <i class="fas fa-upload"></i>
        Processar Gabaritos Preenchidos
    </button>
</div>
```

### 2. Criar Modal de Upload

```html
<!-- Modal de Processamento de Gabaritos -->
<div id="modal-processamento" class="modal-overlay" style="display:none;">
    <div class="modal-content">
        <div class="modal-header">
            <h2><i class="fas fa-upload"></i> Processar Gabaritos</h2>
            <button class="modal-close" onclick="fecharModal('modal-processamento')">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <div class="upload-area" id="upload-area">
                <div class="upload-icon">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <h3>Envie os gabaritos preenchidos</h3>
                <p>Arraste e solte os arquivos ou clique para selecionar</p>
                <p class="formats">Formatos aceitos: PDF, JPG, PNG</p>
                <input type="file" id="gabarito-files" multiple accept=".pdf,.jpg,.jpeg,.png">
            </div>
            
            <div class="files-list" id="files-list" style="display:none;">
                <!-- Lista de arquivos será preenchida dinamicamente -->
            </div>
            
            <div class="processing-options">
                <label>
                    <input type="checkbox" id="validacao-automatica" checked>
                    Validação automática de qualidade
                </label>
                <label>
                    <input type="checkbox" id="revisao-manual">
                    Solicitar revisão manual para casos duvidosos
                </label>
            </div>
            
            <div class="modal-actions">
                <button id="btn-processar" class="btn btn-primary" disabled onclick="iniciarProcessamento()">
                    <i class="fas fa-cogs"></i>
                    Processar Gabaritos
                </button>
                <button class="btn btn-secondary" onclick="fecharModal('modal-processamento')">
                    Cancelar
                </button>
            </div>
        </div>
    </div>
</div>
```

### 3. JavaScript para Upload

```javascript
let cadernoAtualProcessamento = null;
let arquivosParaProcessar = [];

function abrirModalProcessamento(cadernoId) {
    cadernoAtualProcessamento = cadernoId;
    document.getElementById('modal-processamento').style.display = 'flex';
    
    // Configurar drag & drop
    setupDragAndDrop();
}

function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('gabarito-files');
    
    // Click para selecionar arquivos
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag & Drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        adicionarArquivos(files);
    });
    
    // Seleção via input
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        adicionarArquivos(files);
    });
}

function adicionarArquivos(files) {
    const validFiles = files.filter(file => {
        const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
        return validTypes.includes(file.type);
    });
    
    arquivosParaProcessar = [...arquivosParaProcessar, ...validFiles];
    atualizarListaArquivos();
    
    document.getElementById('btn-processar').disabled = arquivosParaProcessar.length === 0;
}

function atualizarListaArquivos() {
    const filesList = document.getElementById('files-list');
    
    if (arquivosParaProcessar.length > 0) {
        filesList.style.display = 'block';
        filesList.innerHTML = `
            <h4>Arquivos selecionados (${arquivosParaProcessar.length})</h4>
            <div class="files-grid">
                ${arquivosParaProcessar.map((file, index) => `
                    <div class="file-item">
                        <i class="fas fa-file-${file.type.includes('pdf') ? 'pdf' : 'image'}"></i>
                        <span class="file-name">${file.name}</span>
                        <button class="remove-file" onclick="removerArquivo(${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        filesList.style.display = 'none';
    }
}

function removerArquivo(index) {
    arquivosParaProcessar.splice(index, 1);
    atualizarListaArquivos();
    document.getElementById('btn-processar').disabled = arquivosParaProcessar.length === 0;
}

async function iniciarProcessamento() {
    if (!cadernoAtualProcessamento || arquivosParaProcessar.length === 0) {
        return;
    }
    
    // Mostrar loading
    mostrarModalProcessamento();
    
    try {
        // Preparar FormData
        const formData = new FormData();
        
        arquivosParaProcessar.forEach(file => {
            formData.append('gabaritos', file);
        });
        
        // Configurações
        formData.append('validacao_automatica', document.getElementById('validacao-automatica').checked);
        formData.append('revisao_manual', document.getElementById('revisao-manual').checked);
        
        // Enviar para processamento
        const response = await fetch(`/api/cadernos/${cadernoAtualProcessamento}/processar-gabaritos`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Sucesso!', `${result.total_processados} gabaritos processados com sucesso!`);
            
            // Mostrar modal com resultados
            mostrarResultadosProcessamento(result);
        } else {
            showError('Erro', result.error || 'Erro ao processar gabaritos');
        }
        
    } catch (error) {
        console.error('Erro no processamento:', error);
        showError('Erro', 'Erro de comunicação com o servidor');
    } finally {
        esconderModalProcessamento();
        fecharModal('modal-processamento');
        
        // Limpar arquivos
        arquivosParaProcessar = [];
        atualizarListaArquivos();
    }
}

function mostrarResultadosProcessamento(result) {
    // Criar modal com estatísticas dos resultados
    const modalHtml = `
        <div id="modal-resultados-processamento" class="modal-overlay">
            <div class="modal-content large">
                <div class="modal-header">
                    <h2><i class="fas fa-chart-bar"></i> Resultados do Processamento</h2>
                    <button class="modal-close" onclick="fecharModal('modal-resultados-processamento')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="stats-summary">
                        <div class="stat-card">
                            <h3>${result.total_processados}</h3>
                            <p>Gabaritos Processados</p>
                        </div>
                        <div class="stat-card">
                            <h3>${calcularMediaTurma(result.resultados).toFixed(1)}%</h3>
                            <p>Média da Turma</p>
                        </div>
                        <div class="stat-card">
                            <h3>${contarAprovados(result.resultados)}</h3>
                            <p>Aprovados (≥60%)</p>
                        </div>
                    </div>
                    
                    <div class="results-table-container">
                        <table class="results-table">
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Escola</th>
                                    <th>Turma</th>
                                    <th>Acertos</th>
                                    <th>Erros</th>
                                    <th>Percentual</th>
                                    <th>Conceito</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${result.resultados.map(r => `
                                    <tr>
                                        <td>${r.student_info.nome || 'N/A'}</td>
                                        <td>${r.student_info.escola || 'N/A'}</td>
                                        <td>${r.student_info.turma || 'N/A'}</td>
                                        <td>${r.summary.acertos}</td>
                                        <td>${r.summary.erros}</td>
                                        <td>${r.summary.percentual.toFixed(1)}%</td>
                                        <td class="conceito-${r.summary.conceito}">${r.summary.conceito}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="modal-actions">
                        <button class="btn btn-primary" onclick="exportarResultados()">
                            <i class="fas fa-download"></i>
                            Exportar Relatório
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    setTimeout(() => document.getElementById('modal-resultados-processamento').classList.add('show'), 10);
}

function calcularMediaTurma(resultados) {
    if (resultados.length === 0) return 0;
    const soma = resultados.reduce((acc, r) => acc + r.summary.percentual, 0);
    return soma / resultados.length;
}

function contarAprovados(resultados) {
    return resultados.filter(r => r.summary.percentual >= 60).length;
}
```

## 📊 Monitoramento e Logs

### 1. Dashboard de Monitoramento

```python
@app.route('/api/correcao/dashboard', methods=['GET'])
def dashboard_correcao():
    """
    Dashboard com estatísticas do sistema de correção
    """
    try:
        # Estatísticas gerais
        total_processados = ResultadoCorrecao.query.count()
        
        # Última semana
        uma_semana_atras = datetime.utcnow() - timedelta(days=7)
        processados_semana = ResultadoCorrecao.query.filter(
            ResultadoCorrecao.data_processamento >= uma_semana_atras
        ).count()
        
        # Qualidade média dos scans
        qualidade_media = db.session.query(
            db.func.avg(ResultadoCorrecao.qualidade_scan)
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_processados': total_processados,
                'processados_ultima_semana': processados_semana,
                'qualidade_media_scan': round(qualidade_media, 1),
                'status_sistema': 'online'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 2. Sistema de Logs

```python
import logging
from logging.handlers import RotatingFileHandler

# Configurar logger específico para correção
correcao_logger = logging.getLogger('correcao')
correcao_logger.setLevel(logging.INFO)

# Handler para arquivo rotativo
handler = RotatingFileHandler(
    'logs/correcao.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
correcao_logger.addHandler(handler)

# Usar nos endpoints
def log_processamento(caderno_id, total_arquivos, sucessos, falhas):
    correcao_logger.info(
        f"Processamento caderno {caderno_id}: "
        f"{total_arquivos} arquivos, {sucessos} sucessos, {falhas} falhas"
    )
```

## 🔧 Configurações de Produção

### 1. Variáveis de Ambiente

```bash
# .env
CORRECAO_API_URL=http://localhost:5001
CORRECAO_API_TIMEOUT=300
CORRECAO_MAX_FILES=50
CORRECAO_MAX_FILE_SIZE=10485760
CORRECAO_ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png
```

### 2. Nginx (se usando API separada)

```nginx
# Proxy para API de correção
location /api/correcao/ {
    proxy_pass http://localhost:5001/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    client_max_body_size 50M;
}
```

## ✅ Checklist de Implementação

- [ ] Escolher cenário de integração (API ou Direto)
- [ ] Implementar endpoints no app.py principal
- [ ] Criar modelos de banco para resultados
- [ ] Adicionar interface no frontend
- [ ] Configurar sistema de logs
- [ ] Testar com gabaritos reais
- [ ] Implementar monitoramento
- [ ] Documentar para usuários finais
- [ ] Configurar backup dos resultados
- [ ] Implementar sistema de notificações

---

Esta integração permite que o sistema principal utilize toda a funcionalidade de correção automática de forma transparente para os usuários! 