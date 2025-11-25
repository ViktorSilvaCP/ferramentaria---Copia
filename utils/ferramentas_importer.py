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


def _normalize_col_name(col):
    no_accents = normalize('NFKD', str(col)).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'\s+', '', no_accents).lower()


def _find_column(df, keywords):
    col_map = {col: _normalize_col_name(col) for col in df.columns}
    for col, norm in col_map.items():
        for kw in keywords:
            if kw in norm:
                return col
    return None


def extrair_indice_ferramenta(codigo_completo):
    if not codigo_completo or not isinstance(codigo_completo, str):
        return None
    
    codigo = codigo_completo.strip().upper()
    if codigo.startswith('DP018'):
        match = re.match(r'^([A-Z]{2}\d{5})', codigo)
        if match:
            return match.group(1)
    match = re.match(r'^([A-Z]{2}\d{3})', codigo)
    if match:
        return match.group(1)
    match = re.match(r'^([A-Z]+\d{3})', codigo)
    if match:
        return match.group(1)
    
    return None

def extrair_sufixo_numerico(codigo_completo):
    if not codigo_completo or not isinstance(codigo_completo, str):
        return None
    codigo = codigo_completo.strip()
    digitos = ''
    for char in reversed(codigo):
        if char.isdigit():
            digitos = char + digitos
        else:
            break
    return digitos.lstrip('0') or '0'


def importar_ferramentas_para_db(db, Ferramenta, dados):
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
            wymiar_calowy = item.get('Wymiar calowy')
            tipo = f"{wym_metryczny or 'N/A'} / {wymiar_calowy or 'N/A'}"
            sufixo = item.get('sufixo')

            ferramenta = Ferramenta.query.filter_by(codigo=codigo).first()

            if ferramenta:
                ferramenta.status = status
                ferramenta.tipo = tipo
                ferramenta.dimensao_metrica = str(wym_metryczny) if wym_metryczny else None
                ferramenta.dimensao_polegada = str(wymiar_calowy) if wymiar_calowy else None
                ferramenta.sufixo = sufixo
                atualizadas += 1
            else:
                nova_ferramenta = Ferramenta(
                    codigo=codigo,
                    tipo=tipo,
                    status=status,
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


def consumir_ferramentas(caminho_fonte=CAMINHO_FONTE, remover_apos_processar=True):
    resumo = {
        'arquivos_processados': 0,
        'dados': [],
        'erros': [],
    }

    path = Path(caminho_fonte)

    try:
        if not path.exists():
            msg = f"Diretório não encontrado: {caminho_fonte}"
            logger.warning(msg)
            resumo['erros'].append(msg)
            return resumo

        logger.info(f"Buscando arquivos em: {caminho_fonte}")
        arquivos = list(path.glob('*.xls')) + list(path.glob('*.xlsx'))
        
        # Ignorar arquivos temporários do Excel
        arquivos = [a for a in arquivos if not a.name.startswith('~$')]
        
        if not arquivos:
            logger.warning("Nenhum arquivo de ferramentas (.xls, .xlsx) encontrado no diretório.")
            resumo['erros'].append("Nenhum arquivo Excel (.xls, .xlsx) encontrado para importar.")
            return resumo
        
        logger.info(f"Arquivos encontrados (excluindo temporários): {[a.name for a in arquivos]}")
        
        for arquivo in arquivos:
            try:
                logger.info(f"Processando arquivo: {arquivo.name}")
                
                # Leitura com diferentes engines 
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
                        logger.error(f"Falha ao ler {arquivo.name} com xlrd: {e2}")
                        raise RuntimeError(f"Não foi possível ler o arquivo {arquivo.name} com os motores disponíveis.")

                if df.empty:
                    logger.warning(f"Arquivo {arquivo.name} vazio. Pulando.")
                    if remover_apos_processar:
                        try:
                            arquivo.unlink()
                        except Exception:
                            pass
                    continue

                logger.info(f"Arquivo {arquivo.name} carregado com {len(df)} linhas")
                logger.info(f"Colunas encontradas: {df.columns.tolist()}")
                codigo_col = _find_column(df, ['indeks', 'index', 'codigo', 'kod', 'code'])
                status_col = _find_column(df, ['status', 'stan', 'stato'])
                wym_metryczny_col = _find_column(df, ['wymiarmetryczny', 'metryczny', 'metryka', 'wymiar'])
                wym_calowy_col = _find_column(df, ['wymiarcalowy', 'calowy', 'cal', 'inch'])

                logger.info(f"Mapeamento de colunas: codigo={codigo_col}, status={status_col}, metryczny={wym_metryczny_col}, calowy={wym_calowy_col}")

                if not codigo_col:
                    msg = f"Coluna de código não encontrada em {arquivo.name}"
                    logger.error(msg + f". Colunas disponíveis: {df.columns.tolist()}")
                    resumo['erros'].append(msg)
                    if remover_apos_processar:
                        pasta_erro = path / 'erros'
                        pasta_erro.mkdir(exist_ok=True)
                        try:
                            arquivo.rename(pasta_erro / arquivo.name)
                        except Exception as me:
                            logger.error(f"Falha mover {arquivo.name} para erros: {me}")
                    continue
                df[codigo_col] = df[codigo_col].astype(str).str.strip()
                logger.info(f"Primeiros 5 códigos: {df[codigo_col].head().tolist()}")
                df['indice_base'] = df[codigo_col].apply(lambda x: extrair_indice_ferramenta(x) if pd.notna(x) else None)
                logger.info(f"Primeiros 5 índices extraídos: {df['indice_base'].head().tolist()}")
                logger.info(f"Índices únicos encontrados: {sorted(set([i for i in df['indice_base'].unique() if i is not None]))}")
                logger.info(f"Índices válidos configurados: {sorted(INDICES_VALIDOS)}")
                
                df_filtrado = df[df['indice_base'].isin(INDICES_VALIDOS)].copy()

                logger.info(f"{len(df_filtrado)} linhas válidas em {arquivo.name} (de {len(df)} total)")
                
                if df_filtrado.empty:
                    msg = f"Nenhuma ferramenta válida em {arquivo.name}. Verifique se os códigos começam com índices válidos."
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

                # Montar dados padronizados
                for idx, row in df_filtrado.iterrows():
                    resumo['dados'].append({
                        'codigo': row.get(codigo_col),
                        'status': row.get(status_col) if status_col and status_col in row.index else 'disponivel',
                        'Wymiar metryczny': row.get(wym_metryczny_col) if wym_metryczny_col else None,
                        'Wymiar calowy': row.get(wym_calowy_col) if wym_calowy_col else None,
                        'sufixo': row.get('sufixo')
                    })

                resumo['arquivos_processados'] += 1
                logger.info(f"Arquivo {arquivo.name} processado com sucesso. Total de dados coletados até agora: {len(resumo['dados'])}")

                if remover_apos_processar:
                    try:
                        arquivo.unlink()
                        logger.info(f"Arquivo removido: {arquivo.name}")
                    except Exception as e:
                        logger.error(f"Erro ao remover {arquivo.name}: {e}")

            except Exception as e:
                msg = f"Erro ao processar arquivo {arquivo.name}: {e}"
                logger.error(msg, exc_info=True)
                resumo['erros'].append(msg)
                if remover_apos_processar:
                    pasta_erro = path / 'erros'
                    pasta_erro.mkdir(exist_ok=True)
                    try:
                        arquivo.rename(pasta_erro / arquivo.name)
                    except Exception as me:
                        logger.error(f"Falha mover {arquivo.name} para erros: {me}")
        
        logger.info(f"Resumo final: {resumo['arquivos_processados']} arquivos processados, {len(resumo['dados'])} ferramentas encontradas")
        return resumo

    except Exception as e:
        logger.error(f"Erro ao consumir ferramentas: {e}", exc_info=True)
        resumo['erros'].append(str(e))
        return resumo