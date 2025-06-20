@echo off
title Sistema de Correção Automática de Gabaritos
color 0A

echo ===============================================
echo  Sistema de Correção Automática de Gabaritos
echo ===============================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python não está instalado ou não está no PATH
    echo Instale Python 3.8+ e tente novamente
    pause
    exit /b 1
)

echo Python detectado com sucesso!
echo.

REM Verificar se as dependências estão instaladas
echo Verificando dependências...
python -c "import cv2, flask, loguru" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependências...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERRO: Falha ao instalar dependências
        pause
        exit /b 1
    )
)

echo Dependências verificadas!
echo.

REM Mostrar menu de opções
:menu
echo Escolha o modo de execução:
echo.
echo 1. API Server (recomendado)
echo 2. Linha de Comando - arquivo único
echo 3. Processamento em lote
echo 4. Sair
echo.
set /p opcao="Digite sua opção (1-4): "

if "%opcao%"=="1" goto api
if "%opcao%"=="2" goto cli
if "%opcao%"=="3" goto batch
if "%opcao%"=="4" goto sair
echo Opção inválida!
goto menu

:api
echo.
echo Iniciando servidor API na porta 5001...
echo Acesse: http://localhost:5001
echo Pressione Ctrl+C para parar o servidor
echo.
python main.py --mode api --debug
goto menu

:cli
echo.
set /p arquivo="Digite o caminho do arquivo de gabarito: "
if not exist "%arquivo%" (
    echo Arquivo não encontrado!
    goto menu
)

echo.
set /p gabarito="Digite o caminho do gabarito oficial (opcional): "

if "%gabarito%"=="" (
    python main.py --mode cli --file "%arquivo%"
) else (
    python main.py --mode cli --file "%arquivo%" --gabarito "%gabarito%"
)

echo.
echo Processamento concluído!
pause
goto menu

:batch
echo.
set /p pasta_entrada="Digite o caminho da pasta com gabaritos: "
if not exist "%pasta_entrada%" (
    echo Pasta não encontrada!
    goto menu
)

set /p pasta_saida="Digite o caminho da pasta de resultados: "
set /p gabarito="Digite o caminho do gabarito oficial (opcional): "

echo.
echo Processando arquivos...

if "%gabarito%"=="" (
    python main.py --mode batch --input "%pasta_entrada%" --output "%pasta_saida%"
) else (
    python main.py --mode batch --input "%pasta_entrada%" --output "%pasta_saida%" --gabarito "%gabarito%"
)

echo.
echo Processamento em lote concluído!
pause
goto menu

:sair
echo.
echo Encerrando...
echo Obrigado por usar o Sistema de Correção Automática!
timeout /t 2 >nul
exit /b 0 