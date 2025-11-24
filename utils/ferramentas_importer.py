import os
import pandas as pd
import logging
import re
from pathlib import Path
from unicodedata import normalize

logger = logging.getLogger(__name__)

INDICES_VALIDOS = {
    'CR023', 'CR022', 'DP01801', 'DP021', 'ID005', 'ID001',
    'PN011', 'PS052', 'PS090', 'PS053', 'PS059', 'PS054',
    'PS055', 'RD017', 'RD012', 'RS031', 'RS022'
}

CAMINHO_FONTE = r'F:\Doc_Comp\(Publico)\ferramentas'
COLUNAS_DESEJADAS = ['indeks', 'status', 'Wymiar metryczny', 'Wymiar calowy', 'Opis']


# helper functions
def _normalize_col_name(col):
    # Normaliza para facilitar comparação (remove acentos, espaços e transforma em lower)
    no_accents = normalize('NFKD', str(col)).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'\s+', '', no_accents).lower()


def _find_column(df, keywords):
    """
    Procura a primeira coluna do dataframe cujo nome normalizado contenha qualquer uma das keywords.
    keywords: lista de strings já normalizadas (sem espaços e em lower)
    Retorna o nome real da coluna ou None.
    """
    col_map = {col: _normalize_col_name(col) for col in df.columns}
    for col, norm in col_map.items():
        for kw in keywords:
            if kw in norm:
                return col
    return None


def extrair_indice_ferramenta(codigo_completo):
    """
    Ex: RS022000000103 -> RS022
    """
    if not codigo_completo or not isinstance(codigo_completo, str):
        return None
    codigo = codigo_completo.strip().upper()
    match = re.match(r'([A-Z]+[0-9]+)', codigo)
    if match:
        return match.group(1)
    return None


def extrair_sufixo_numerico(codigo_completo):
    """
    Ex: RS022000000103 -> 103 (remove zeros à esquerda)
    """
    if not codigo_completo or not isinstance(codigo_completo, str):
        return None
    codigo = codigo_completo.strip()
    # Extrai dígitos finais
    digitos = ''
    for char in reversed(codigo):
        if char.isdigit():
            digitos = char + digitos
        else:
            break
    return digitos.lstrip('0') or '0'


def importar_ferramentas_para_db(db, Ferramenta, dados):
    """
    Persiste lista de registros no banco.
    Retorna (adicionadas, atualizadas)
    """
    try:
        if not dados:
            logger.warning("Nenhum dado de ferramentas para importar")
            return 0, 0

        adicionadas = 0
        atualizadas = 0

        for item in dados:
            codigo = item['codigo']
            status = item.get('status', 'disponivel')
            wym_metryczny = item.get('Wymiar metryczny')
            descricao = item.get('Opis')
            wymiar_calowy = item.get('Wymiar calowy')
            tipo = f"{wym_metryczny or 'N/A'} / {wymiar_calowy or 'N/A'}"
            sufixo = item.get('sufixo')

            # Busca ferramenta existente
            ferramenta = Ferramenta.query.filter_by(codigo=codigo).first()

            if ferramenta:
                # Atualiza existente
                ferramenta.status = status
                ferramenta.tipo = tipo
                ferramenta.descricao = descricao
                ferramenta.dimensao_metrica = str(wym_metryczny) if wym_metryczny else None
                ferramenta.dimensao_polegada = str(wymiar_calowy) if wymiar_calowy else None
                ferramenta.sufixo = sufixo
                atualizadas += 1
            else:
                # Cria nova
                nova_ferramenta = Ferramenta(
                    codigo=codigo,
                    tipo=tipo,
                    status=status,
                    descricao=descricao,
                    dimensao_metrica=str(wym_metryczny) if wym_metryczny else None,
                    dimensao_polegada=str(wymiar_calowy) if wymiar_calowy else None,
                    sufixo=sufixo,
                    posicao=None
                )
                db.session.add(nova_ferramenta)
                adicionadas += 1

        db.session.commit()
        logger.info(f"Importação: {adicionadas} adicionadas, {atualizadas} atualizadas")
        return adicionadas, atualizadas

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao importar ferramentas para BD: {e}", exc_info=True)
        return 0, 0


def consumir_ferramentas(caminho_fonte, remover_apos_processar=True):
    """
    Lê XLS/XLSX do diretório e retorna os dados extraídos.
    Se remover_apos_processar=False, não deleta/move arquivos (útil para testes).
    Retorna um resumo dict: {'arquivos_processados': n, 'dados': [...], 'erros': [...]}
    """
    # 1. Inicialização do resumo (blocos de código desorganizados)
    resumo = {
        'arquivos_processados': 0,
        'dados': [],
        'erros': [],
    }
    
    # 2. Path (blocos de código desorganizados)
    path = Path(caminho_fonte)
    
    # Início do bloco try/except que estava faltando no seu código
    try:
    
        if not path.exists():
            msg = f"Diretório não encontrado: {caminho_fonte}"
            logger.warning(msg)
            resumo['erros'].append(msg)
            return resumo

        logging.info(f"Buscando arquivos em: {caminho_fonte}")
        arquivos = list(path.glob('*.xls')) + list(path.glob('*.xlsx'))
        if not arquivos:
            logger.warning("Nenhum arquivo de ferramentas (.xls, .xlsx) encontrado no diretório.")
            return resumo
        
        for arquivo in arquivos:
            try:
                # Tenta leitura com diferentes engines para maximizar compatibilidade (Comentário corrigido)
                try:
                    if str(arquivo).lower().endswith('.xlsx'):
                        df = pd.read_excel(arquivo, engine='openpyxl')
                    else:
                        df = pd.read_excel(arquivo)
                except Exception as e1:
                    logger.debug(f"Falha engine padrão para {arquivo.name}: {e1}. Tentando xlrd...")
                    try:
                        df = pd.read_excel(arquivo, engine='xlrd')
                    except Exception as e2:
                        raise RuntimeError(f"Não foi possível ler {arquivo.name}: {e2}")

                if df.empty:
                    logger.warning(f"Arquivo {arquivo.name} vazio. Pulando.")
                    if remover_apos_processar:
                        try:
                            arquivo.unlink()
                        except Exception:
                            pass
                    continue

                # Normalizar nomes de colunas (apenas para busca; não renomear o df)
                # Procurar colunas candidatas
                codigo_col = _find_column(df, ['indeks', 'index', 'codigo', 'kod', 'code'])
                status_col = _find_column(df, ['status', 'stan', 'stato'])
                wym_metryczny_col = _find_column(df, ['wymiarmetryczny', 'metryczny', 'metryka', 'wymiar'])
                wym_calowy_col = _find_column(df, ['wymiarcalowy', 'calowy', 'cal', 'inch'])
                opis_col = _find_column(df, ['opis', 'description', 'desc', 'descr'])

                if not codigo_col:
                    msg = f"Coluna de código não encontrada em {arquivo.name}"
                    logger.error(msg + f". Colunas disponíveis: {df.columns.tolist()}")
                    resumo['erros'].append(msg)
                    # mover para pasta erros se for para remover
                    if remover_apos_processar:
                        pasta_erro = path / 'erros'
                        pasta_erro.mkdir(exist_ok=True)
                        try:
                            arquivo.rename(pasta_erro / arquivo.name)
                        except Exception as me:
                            logger.error(f"Falha mover {arquivo.name} para erros: {me}")
                    continue

                # Garantir que os valores sejam strings (para extrair índices)
                df[codigo_col] = df[codigo_col].astype(str).str.strip()
                # Criar colunas auxiliares
                df['indice_base'] = df[codigo_col].apply(lambda x: extrair_indice_ferramenta(x) if pd.notna(x) else None)
                df_filtrado = df[df['indice_base'].isin(INDICES_VALIDOS)].copy()

                logger.info(f"{len(df_filtrado)} linhas válidas em {arquivo.name}")
                if df_filtrado.empty:
                    msg = f"Nenhuma ferramenta válida em {arquivo.name}"
                    logger.warning(msg)
                    resumo['erros'].append(msg)
                    if remover_apos_processar:
                        pasta_erro = path / 'erros'
                        pasta_erro.mkdir(exist_ok=True)
                        try:
                            arquivo.rename(pasta_erro / arquivo.name)
                        except Exception as e:
                            logger.error(f"Falha mover {arquivo.name} para erros: {e}")
                    continue

                # Extrair sufixo
                df_filtrado['sufixo'] = df_filtrado[codigo_col].apply(lambda x: extrair_sufixo_numerico(x) if pd.notna(x) else None)

                # Montar dados padronizados para importação
                dados = [] # Variável local 'dados' foi reintroduzida, mas os dados estão sendo adicionados diretamente em resumo['dados']
                for _, row in df_filtrado.iterrows():
                    # Fechamento do dicionário e do append que estava faltando
                    resumo['dados'].append({
                        'codigo': row.get(codigo_col),
                        'status': row.get(status_col) if status_col in row.index else 'disponivel',
                        'Wymiar metryczny': row.get(wym_metryczny_col) if wym_metryczny_col in row.index else None,
                        'Wymiar calowy': row.get(wym_calowy_col) if wym_calowy_col in row.index else None,
                        'Opis': row.get(opis_col) if opis_col in row.index else None,
                        'sufixo': row.get('sufixo')
                    }) # Chaves e parênteses de fechamento adicionados

                resumo['arquivos_processados'] += 1

                if remover_apos_processar:
                    try:
                        arquivo.unlink()
                        logger.info(f"Arquivo removido: {arquivo.name}") # Mensagem de log corrigida
                    except Exception as e: # Variável 'e' adicionada ao except
                        logger.error(f"Erro ao remover {arquivo.name}: {e}") # Variável 'e' usada

            except Exception as e: # Variável 'e' adicionada ao except
                msg = f"Erro ao processar arquivo {arquivo.name}: {e}" # Variável 'msg' e 'e' corrigidas
                logger.error(msg, exc_info=True)
                # Bloco de mover para erros (indentação e variáveis corrigidas)
                if remover_apos_processar:
                    pasta_erro = path / 'erros'
                    pasta_erro.mkdir(exist_ok=True)
                    try:
                        arquivo.rename(pasta_erro / arquivo.name)
                    except Exception as me:
                        logger.error(f"Falha mover {arquivo.name} para erros: {me}")
        
        return resumo # Retorno do resumo movido para o final do try

    except Exception as e:
        logger.error(f"Erro ao consumir ferramentas: {e}", exc_info=True)
        resumo['erros'].append(str(e))
        return resumo


# Expose a small wrapper for API usage (não remove arquivos por default)
def importar_ferramentas_para_db_direto(db, Ferramenta, caminho_fonte=CAMINHO_FONTE):
    """
    Função completa que consome e importa para o DB.
    """
    resultado_consumo = consumir_ferramentas(caminho_fonte, remover_apos_processar=True)
    if resultado_consumo['dados'] and not resultado_consumo['erros']:
        adicionadas, atualizadas = importar_ferramentas_para_db(db, Ferramenta, resultado_consumo['dados'])
        return adicionadas + atualizadas
    return 0