// Log para confirmar que o arquivo foi carregado
console.log('[FERRAMENTAS.JS] Arquivo carregado!');

// Aguardar o DOM estar pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
} else {
    inicializar();
}

function inicializar() {
    console.log('[FERRAMENTAS.JS] Inicializando...');
    
    // Prevenir submissão de TODOS os formulários da página
    const todosFormularios = document.querySelectorAll('form');
    console.log('[FERRAMENTAS.JS] Formulários encontrados:', todosFormularios.length);
    
    todosFormularios.forEach((form, index) => {
        console.log(`[FERRAMENTAS.JS] Form ${index}:`, form.id);
        form.addEventListener('submit', (e) => {
            console.log('[FERRAMENTAS.JS] Submit capturado no form:', form.id);
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    });
    
    // Criar instância do gerenciador
    new GerenciadorFerramentas();
}

class GerenciadorFerramentas {
    constructor() {
        console.log('[GERENCIADOR] Construtor chamado');
        this.ferramentas = [];
        this.tabelaCorpo = document.querySelector('table tbody');
        this.init();
    }

    init() {
        console.log('[GERENCIADOR] Init chamado');
        this.cacheElements();
        this.bindEvents();
        this.carregarFerramentas();
    }

    cacheElements() {
        console.log('[GERENCIADOR] Cacheando elementos...');
        
        // Botões de ação principais
        this.btnAdicionar = document.getElementById('btnAdicionarFerramenta');
        this.btnImportar = document.getElementById('btnImportarFerramenta');
        this.btnAtualizar = document.getElementById('btnAtualizar');

        // Modal de Adicionar/Editar
        this.modalAdicionar = document.getElementById('modalAdicionarFerramenta');
        this.formAdicionar = document.getElementById('formAdicionarFerramenta');
        this.btnCancelarAdicionar = document.getElementById('btnCancelarAdicionar');

        // Modal de Importação
        this.modalImportar = document.getElementById('modalImportarFerramenta');
        this.formImportar = document.getElementById('formImportarFerramenta');
        this.btnExecutarImportacao = this.formImportar?.querySelector('button[type="submit"]');
        this.btnCancelarImportar = document.getElementById('btnCancelarImportar');
        
        console.log('[GERENCIADOR] Elementos encontrados:', {
            btnAdicionar: !!this.btnAdicionar,
            btnImportar: !!this.btnImportar,
            btnAtualizar: !!this.btnAtualizar,
            modalAdicionar: !!this.modalAdicionar,
            formAdicionar: !!this.formAdicionar,
            modalImportar: !!this.modalImportar,
            formImportar: !!this.formImportar,
            btnExecutarImportacao: !!this.btnExecutarImportacao
        });
    }

    bindEvents() {
        console.log('[GERENCIADOR] Vinculando eventos...');
        
        if (this.btnAdicionar) {
            this.btnAdicionar.addEventListener('click', (e) => {
                e.preventDefault();
                this.abrirModal(this.modalAdicionar);
            });
        }
        
        if (this.btnImportar) {
            this.btnImportar.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('[GERENCIADOR] Botão importar clicado');
                this.abrirModal(this.modalImportar);
            });
        }
        
        if (this.btnAtualizar) {
            this.btnAtualizar.addEventListener('click', (e) => {
                e.preventDefault();
                this.carregarFerramentas();
            });
        }
        
        if (this.btnCancelarAdicionar) {
            this.btnCancelarAdicionar.addEventListener('click', (e) => {
                e.preventDefault();
                this.fecharModal(this.modalAdicionar);
            });
        }
        
        if (this.btnCancelarImportar) {
            this.btnCancelarImportar.addEventListener('click', (e) => {
                e.preventDefault();
                this.fecharModal(this.modalImportar);
            });
        }
        
        // Evento no formulário de adicionar
        if (this.formAdicionar) {
            this.formAdicionar.addEventListener('submit', (e) => {
                console.log('[GERENCIADOR] Submit formAdicionar capturado');
                e.preventDefault();
                e.stopPropagation();
                this.salvarFerramenta();
                return false;
            });
        }

        // Evento no formulário de importar
        if (this.formImportar) {
            this.formImportar.addEventListener('submit', (e) => {
                console.log('[GERENCIADOR] Submit formImportar capturado!');
                e.preventDefault();
                e.stopPropagation();
                this.importarFerramentas();
                return false;
            });
        }
        
        // SEGURANÇA EXTRA: Capturar click direto no botão também
        if (this.btnExecutarImportacao) {
            this.btnExecutarImportacao.addEventListener('click', (e) => {
                console.log('[GERENCIADOR] Click no botão importar capturado');
                e.preventDefault();
                e.stopPropagation();
                this.importarFerramentas();
                return false;
            });
        }
    }

    async carregarFerramentas() {
        try {
            const resp = await fetch('/api/ferramentas');
            if (!resp.ok) throw new Error(`Erro HTTP: ${resp.status}`);
            this.ferramentas = await resp.json();
            this.renderTabela();
        } catch (err) {
            this.notificar(`Falha ao carregar ferramentas: ${err.message}`, 'danger');
            console.error(err);
        }
    }

    renderTabela() {
        this.tabelaCorpo.innerHTML = '';
        if (!this.ferramentas.length) {
            this.tabelaCorpo.innerHTML = `<tr><td colspan="9" class="text-center py-4">Nenhuma ferramenta cadastrada.</td></tr>`;
            return;
        }
        for (const f of this.ferramentas) {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-gray-200 hover:bg-gray-50';
            tr.innerHTML = `
                <td class="py-4 px-6">${f.codigo}</td>
                <td class="py-4 px-6">${f.descricao || ''}</td>
                <td class="py-4 px-6">${f.tipo}</td>
                <td class="py-4 px-6">${f.dimensao_metrica || ''}</td>
                <td class="py-4 px-6">${f.dimensao_polegada || ''}</td>
                <td class="py-4 px-6">${f.sufixo || ''}</td>
                <td class="py-4 px-6"><span class="status-label ${f.status}">${f.status}</span></td>
                <td class="py-4 px-6">${f.ultima_atualizacao || ''}</td>
                <td class="py-4 px-6 text-center">
                    <button class="text-blue-600 hover:text-blue-800 mr-2" title="Editar ferramenta"><i class="fas fa-edit"></i></button>
                    <button class="text-red-600 hover:text-red-800" title="Descartar ferramenta"><i class="fas fa-trash"></i></button>
                </td>
            `;
            this.tabelaCorpo.appendChild(tr);
        }
    }

    abrirModal(modal) {
        console.log('[GERENCIADOR] Abrindo modal:', modal?.id);
        modal?.classList.remove('hidden');
    }

    fecharModal(modal) {
        console.log('[GERENCIADOR] Fechando modal:', modal?.id);
        modal?.classList.add('hidden');
    }

    async salvarFerramenta() {
        const form = this.formAdicionar;
        const dados = {
            codigo: form.codigo.value.trim(),
            tipo: form.tipo.value.trim(),
            descricao: form.descricao.value.trim(),
            status: form.status.value
        };
        if (!dados.codigo || !dados.tipo) {
            this.notificar('Os campos Código e Tipo são obrigatórios.', 'danger');
            return;
        }
        try {
            const resp = await fetch('/api/ferramentas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
            const resultado = await resp.json();
            if (resultado.success) {
                this.notificar(resultado.message, 'success');
                this.fecharModal(this.modalAdicionar);
                this.carregarFerramentas();
            } else {
                throw new Error(resultado.error || 'Erro desconhecido');
            }
        } catch (err) {
            this.notificar(`Erro ao salvar: ${err.message}`, 'danger');
            console.error(err);
        }
    }

    async importarFerramentas() {
        console.log('[GERENCIADOR] importarFerramentas() chamada');
        
        if (!confirm('Deseja iniciar a importação de ferramentas do arquivo? Esta ação pode levar alguns instantes.')) {
            console.log('[GERENCIADOR] Usuário cancelou a importação');
            return;
        }
    
        console.log('[GERENCIADOR] Iniciando importação...');
        const btn = this.btnExecutarImportacao;
        
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Importando...';
        }
    
        try {
            console.log('[GERENCIADOR] Fazendo requisição para /api/ferramentas/importar');
            const resp = await fetch('/api/ferramentas/importar', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            console.log('[GERENCIADOR] Resposta recebida. Status:', resp.status);
            
            const resultado = await resp.json();
            console.log('[GERENCIADOR] Resultado JSON:', resultado);
            
            if (resp.ok && resultado.success === true) {
                console.log('[GERENCIADOR] Importação bem-sucedida');
                this.notificar(resultado.message, 'success');
                this.fecharModal(this.modalImportar);
                this.carregarFerramentas();
            } else {
                console.log('[GERENCIADOR] Importação falhou:', resultado);
                throw new Error(resultado.message || `Erro no servidor: ${resp.statusText}`);
            }
        } catch (err) {
            console.error('[GERENCIADOR] Erro capturado:', err);
            this.notificar(`Falha na importação: ${err.message}`, 'danger');
        } finally {
            console.log('[GERENCIADOR] Finalizando importação');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-upload mr-2"></i>Importar';
            }
        }
    }

    notificar(msg, tipo = 'success') {
        const div = document.createElement('div');
        div.className = `fixed top-5 right-5 p-4 rounded-lg text-white z-50 ${tipo === 'success' ? 'bg-green-500' : 'bg-red-500'}`;
        div.textContent = msg;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }
}