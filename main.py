#!/usr/bin/env python3
"""
Aplicação de Correção Automática de Gabaritos - Script Principal
================================================================

Script principal para executar o sistema de correção automática.
Pode ser usado em diferentes modos: API server, linha de comando, ou daemon.

Uso:
    python main.py --mode api                 # Executar API server
    python main.py --mode cli --file path    # Processar arquivo via CLI
    python main.py --mode daemon             # Executar como daemon
"""

import argparse
import sys
from pathlib import Path
from loguru import logger

# Adicionar path para imports
sys.path.append(str(Path(__file__).parent.parent))

from api.app import run_app, create_app
from core.scanner import GabaritoScanner
from core.corrector import AutoCorrector
from utils.cli_interface import CLIInterface
from utils.daemon_runner import DaemonRunner


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Sistema de Correção Automática de Gabaritos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --mode api                              # Iniciar servidor API
  python main.py --mode cli --file gabarito.pdf         # Processar arquivo
  python main.py --mode batch --input folder/ --output results/  # Lote
  python main.py --mode daemon --config config.json    # Executar como daemon
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['api', 'cli', 'batch', 'daemon'],
        default='api',
        help='Modo de execução (padrão: api)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Arquivo de gabarito para processar (modo cli)'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Diretório de entrada (modo batch)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Diretório de saída (modo batch)'
    )
    
    parser.add_argument(
        '--gabarito',
        type=str,
        help='Arquivo com gabarito oficial (JSON ou ID)'
    )
    
    parser.add_argument(
        '--template',
        type=str,
        help='Template do gabarito (santa_quiteria, padrao_sistema)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Arquivo de configuração personalizada'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host para API server (padrão: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5001,
        help='Porta para API server (padrão: 5001)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Executar em modo debug'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nível de log (padrão: INFO)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    logger.remove()
    logger.add(
        sys.stderr,
        level=args.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    # Executar modo selecionado
    try:
        if args.mode == 'api':
            run_api_mode(args)
        elif args.mode == 'cli':
            run_cli_mode(args)
        elif args.mode == 'batch':
            run_batch_mode(args)
        elif args.mode == 'daemon':
            run_daemon_mode(args)
    except KeyboardInterrupt:
        logger.info("Execução interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_api_mode(args):
    """Executa modo API server"""
    logger.info("=== MODO API SERVER ===")
    logger.info(f"Iniciando servidor em {args.host}:{args.port}")
    
    run_app(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


def run_cli_mode(args):
    """Executa modo linha de comando"""
    logger.info("=== MODO LINHA DE COMANDO ===")
    
    if not args.file:
        logger.error("Arquivo não especificado. Use --file caminho/para/arquivo")
        sys.exit(1)
    
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    # Configurar template
    template_tipo = args.template or 'santa_quiteria'
    
    # Inicializar componentes
    scanner = GabaritoScanner(template_tipo)
    corrector = AutoCorrector()
    
    # Carregar gabarito oficial se especificado
    if args.gabarito:
        gabarito_path = Path(args.gabarito)
        if gabarito_path.exists():
            import json
            with open(gabarito_path, 'r', encoding='utf-8') as f:
                gabarito_oficial = json.load(f)
            corrector.set_gabarito_oficial(gabarito_oficial)
        else:
            logger.warning(f"Gabarito oficial não encontrado: {gabarito_path}")
    
    logger.info(f"Processando arquivo: {file_path}")
    
    # 1. Escanear arquivo
    logger.info("1. Escaneando gabarito...")
    scan_result = scanner.scan_file(file_path)
    
    if not scan_result['success']:
        logger.error(f"Erro no escaneamento: {scan_result.get('error', 'Erro desconhecido')}")
        sys.exit(1)
    
    # 2. Extrair dados do primeiro aluno (CLI simples)
    if scan_result['pages']:
        page_data = scan_result['pages'][0]
        student_info = page_data.get('header_data', {})
        answers = page_data.get('answers', {})
        
        logger.info("2. Dados extraídos:")
        logger.info(f"   Nome: {student_info.get('nome', 'Não detectado')}")
        logger.info(f"   Escola: {student_info.get('escola', 'Não detectado')}")
        logger.info(f"   Turma: {student_info.get('turma', 'Não detectado')}")
        logger.info(f"   Respostas detectadas: {len(answers)}")
        
        # 3. Corrigir se gabarito oficial disponível
        if corrector.gabarito_oficial:
            logger.info("3. Corrigindo gabarito...")
            correction_result = corrector.correct_single_student(answers, student_info)
            
            summary = correction_result['summary']
            logger.success("=== RESULTADO DA CORREÇÃO ===")
            logger.info(f"Total de questões: {summary['total_questoes']}")
            logger.info(f"Acertos: {summary['acertos']}")
            logger.info(f"Erros: {summary['erros']}")
            logger.info(f"Em branco: {summary['em_branco']}")
            logger.info(f"Pontuação: {summary['pontuacao']:.1f}")
            logger.info(f"Percentual: {summary['percentual']:.1f}%")
            logger.info(f"Conceito: {summary['conceito']}")
            
            # Salvar resultado
            output_path = file_path.with_suffix('.json')
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(correction_result, f, indent=2, ensure_ascii=False)
            logger.info(f"Resultado salvo em: {output_path}")
        else:
            logger.warning("Gabarito oficial não fornecido - apenas dados extraídos")
            
            # Salvar apenas dados escaneados
            output_path = file_path.with_suffix('_scan.json')
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scan_result, f, indent=2, ensure_ascii=False)
            logger.info(f"Dados de escaneamento salvos em: {output_path}")


def run_batch_mode(args):
    """Executa modo processamento em lote"""
    logger.info("=== MODO PROCESSAMENTO EM LOTE ===")
    
    if not args.input:
        logger.error("Diretório de entrada não especificado. Use --input pasta/")
        sys.exit(1)
    
    input_dir = Path(args.input)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Diretório de entrada inválido: {input_dir}")
        sys.exit(1)
    
    output_dir = Path(args.output) if args.output else input_dir / "results"
    output_dir.mkdir(exist_ok=True)
    
    # Encontrar arquivos de gabarito
    extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    files = []
    for ext in extensions:
        files.extend(input_dir.glob(f"*{ext}"))
        files.extend(input_dir.glob(f"*{ext.upper()}"))
    
    if not files:
        logger.error(f"Nenhum arquivo de gabarito encontrado em: {input_dir}")
        sys.exit(1)
    
    logger.info(f"Encontrados {len(files)} arquivos para processar")
    
    # Configurar componentes
    template_tipo = args.template or 'santa_quiteria'
    scanner = GabaritoScanner(template_tipo)
    corrector = AutoCorrector()
    
    # Carregar gabarito oficial
    if args.gabarito:
        gabarito_path = Path(args.gabarito)
        if gabarito_path.exists():
            import json
            with open(gabarito_path, 'r', encoding='utf-8') as f:
                gabarito_oficial = json.load(f)
            corrector.set_gabarito_oficial(gabarito_oficial)
    
    # Processar arquivos
    results = []
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"Processando ({i}/{len(files)}): {file_path.name}")
        
        try:
            # Escanear
            scan_result = scanner.scan_file(file_path)
            
            if scan_result['success'] and scan_result['pages']:
                page_data = scan_result['pages'][0]
                student_info = page_data.get('header_data', {})
                answers = page_data.get('answers', {})
                
                # Corrigir se possível
                if corrector.gabarito_oficial:
                    result = corrector.correct_single_student(answers, student_info)
                    results.append(result)
                    
                    # Salvar resultado individual
                    output_file = output_dir / f"{file_path.stem}_resultado.json"
                    import json
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                
                successful += 1
                logger.success(f"Processado com sucesso: {file_path.name}")
                
            else:
                failed += 1
                logger.error(f"Falha no processamento: {file_path.name}")
        
        except Exception as e:
            failed += 1
            logger.error(f"Erro ao processar {file_path.name}: {e}")
    
    # Gerar relatório consolidado
    if results and corrector.gabarito_oficial:
        logger.info("Gerando relatório consolidado...")
        
        batch_result = {
            'total_arquivos': len(files),
            'sucessos': successful,
            'falhas': failed,
            'resultados': results,
            'estatisticas_turma': _calculate_class_statistics(results)
        }
        
        # Salvar relatório
        report_file = output_dir / "relatorio_turma.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, indent=2, ensure_ascii=False)
        
        # Exportar para Excel se disponível
        try:
            _export_to_excel(results, output_dir / "resultados_turma.xlsx")
            logger.info("Resultados exportados para Excel")
        except ImportError:
            logger.warning("pandas não disponível - Excel não exportado")
    
    logger.success(f"Processamento em lote concluído: {successful} sucessos, {failed} falhas")


def run_daemon_mode(args):
    """Executa modo daemon"""
    logger.info("=== MODO DAEMON ===")
    logger.info("Funcionalidade em desenvolvimento...")
    
    # TODO: Implementar daemon runner
    daemon = DaemonRunner(args.config)
    daemon.run()


def _calculate_class_statistics(results):
    """Calcula estatísticas da turma"""
    if not results:
        return {}
    
    pontuacoes = [r['summary']['percentual'] for r in results]
    
    return {
        'media': sum(pontuacoes) / len(pontuacoes),
        'maior_nota': max(pontuacoes),
        'menor_nota': min(pontuacoes),
        'aprovados': len([p for p in pontuacoes if p >= 60]),
        'reprovados': len([p for p in pontuacoes if p < 60])
    }


def _export_to_excel(results, output_path):
    """Exporta resultados para Excel"""
    import pandas as pd
    
    data = []
    for result in results:
        summary = result['summary']
        student_info = result['student_info']
        
        data.append({
            'Nome': student_info.get('nome', ''),
            'Escola': student_info.get('escola', ''),
            'Turma': student_info.get('turma', ''),
            'Total_Questoes': summary['total_questoes'],
            'Acertos': summary['acertos'],
            'Erros': summary['erros'],
            'Em_Branco': summary['em_branco'],
            'Pontuacao': summary['pontuacao'],
            'Percentual': summary['percentual'],
            'Conceito': summary['conceito']
        })
    
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)


if __name__ == '__main__':
    main() 