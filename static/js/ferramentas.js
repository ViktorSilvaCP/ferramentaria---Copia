class GerenciadorFerramentas {
    constructor() {
        this.ferramentas = [];
        this.ferramentasFiltradas = [];
        this.init();
    }
 
    init() {
        this.cacheElementos();
        this.adicionarEventos();
        this.carregarFerramentas();
    }
 
    cacheElementos() {
        // Botões principais
        this.btnAdicionarFerramenta = document.getElementById('btnAdicionarFerramenta');
        this.btnImportarFerramenta = document.getElementById('btnImportarFerramenta');
        this.btnAtualizar = document.getElementById('btnAtualizar');
 
        // Tabela
        this.tabelaCorpo = document.querySelector('table tbody');
 
        // Modal de Adicionar/Editar
        this.modalAdicionar = document.getElementById('modalAdicionarFerramenta');
        this.formAdicionar = document.getElementById('formAdicionarFerramenta');
        this.inputCodigo = document.getElementById('codigo');
        this.inputTipo = document.getElementById('tipo');
        this.inputDescricao = document.getElementById('descricao');
        this.selectStatus = document.getElementById('status');
        this.btnSalvar = this.modalAdicionar.querySelector('button[type="submit"]');
        this.btnCancelarAdicionar = document.getElementById('btnCancelarAdicionar');
 
        // Modal de Importação
        this.modalImportar = document.getElementById('modalImportarFerramenta');
        this.formImportar = document.getElementById('formImportarFerramenta');
        this.btnConfirmarImportar = this.modalImportar.querySelector('button[type="submit"]');
        this.btnCancelarImportar = document.getElementById('btnCancelarImportar');
    }
 
    adicionarEventos() {
        this.btnAdicionarFerramenta.addEventListener('click', () => this.abrirModalAdicionar());
        this.btnAtualizar.addEventListener('click', () => this.carregarFerramentas());
        this.btnCancelarAdicionar.addEventListener('click', () => this.fecharModalAdicionar());
 
        if (this.btnImportarFerramenta) {
            this.btnImportarFerramenta.addEventListener('click', () => this.abrirModalImportar());
        }
 
        if (this.formImportar) {
            this.formImportar.addEventListener('submit', (e) => {
                e.preventDefault();
                this.importarFerramentas();
            });
        }
 
        this.btnCancelarImportar.addEventListener('click', () => this.fecharModalImportar());
 
        this.formAdicionar.addEventListener('submit', (e) => {
            e.preventDefault();
            this.salvarFerramenta();
        });

        document.addEventListener('DOMContentLoaded', function () {
            const btn = document.getElementById('btnConsumir');
            const out = document.getElementById('resultado');
    
            if (!btn) return;
    
            btn.addEventListener('click', async function () {
                btn.disabled = true;
                out.textContent = 'Iniciando consumo...';
                try {
                    const resp = await fetch('/api/consumir_ferramentas', { method: 'POST' });
                    if (!resp.ok) {
                        const txt = await resp.text();
                        out.textContent = `Erro HTTP ${resp.status}: ${txt}`;
                    } else {
                        const data = await resp.json();
                        out.textContent = JSON.stringify(data, null, 2);
                    }
                } catch (err) {
                    out.textContent = 'Falha ao chamar API: ' + (err.message || err);
                } finally {
                    btn.disabled = false;
                }
            });
        });
    }
 
    async carregarFerramentas() {
        try {
            this.tabelaCorpo.innerHTML = `<tr><td colspan="9" class="text-center py-4"><i class="fas fa-spinner fa-spin mr-2"></i>Carregando ferramentas...</td></tr>`;
            const response = await fetch('/api/ferramentas');
            if (!response.ok) throw new Error('Erro ao carregar ferramentas.');
 
            this.ferramentas = await response.json();
            this.ferramentasFiltradas = this.ferramentas;
            this.renderizarTabela();
        } catch (error) {
            console.error('Erro:', error);
            this.mostrarNotificacao('Falha ao carregar ferramentas.', 'danger');
        }
    }
 
    renderizarTabela() {
        this.tabelaCorpo.innerHTML = '';
        const ferramentas = this.ferramentasFiltradas;

        if (ferramentas.length === 0) {
            this.tabelaCorpo.innerHTML = `<tr><td colspan="9" class="text-center py-4">Nenhuma ferramenta encontrada.</td></tr>`;
            return;
        }
 
        ferramentas.forEach(f => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-gray-200 hover:bg-gray-50';
            tr.innerHTML = `
                <td class="py-4 px-6">${f.codigo}</td>
                <td class="py-4 px-6">${f.descricao || 'N/A'}</td>
                <td class="py-4 px-6">${f.tipo || 'N/A'}</td>
                <td class="py-4 px-6">${f.dimensao_metrica || 'N/A'}</td>
                <td class="py-4 px-6">${f.dimensao_polegada || 'N/A'}</td>
                <td class="py-4 px-6">${f.sufixo || 'N/A'}</td>
                <td class="py-4 px-6">
                    <span class="status-label ${f.status}">${f.status}</span>
                </td>
                <td class="py-4 px-6">${f.ultima_atualizacao || 'N/A'}</td>
                <td class="py-4 px-6 text-center">
                    <button class="text-blue-600 hover:text-blue-800 mr-2" title="Editar ferramenta">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-red-600 hover:text-red-800" title="Descartar ferramenta">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            this.tabelaCorpo.appendChild(tr);
        });
    }
 
    abrirModalAdicionar() {
        this.formAdicionar.reset();
        this.modalAdicionar.classList.remove('hidden');
    }
 
    fecharModalAdicionar() {
        this.modalAdicionar.classList.add('hidden');
    }
 
    abrirModalImportar() {
        this.modalImportar.classList.remove('hidden');
    }
 
    fecharModalImportar() {
        this.modalImportar.classList.add('hidden');
    }
 
    async salvarFerramenta() {
        const codigo = this.inputCodigo.value.trim();
        const tipo = this.inputTipo.value.trim();
        const descricao = this.inputDescricao.value.trim();
        const status = this.selectStatus.value;
 
        if (!codigo || !tipo) {
            this.mostrarNotificacao('Código e Tipo são obrigatórios.', 'danger');
            return;
        }
 
        try {
            const response = await fetch('/api/ferramentas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo, tipo, descricao, status })
            });
 
            const resultado = await response.json();
 
            if (resultado.success) {
                this.mostrarNotificacao(resultado.message, 'success');
                this.fecharModalAdicionar();
                this.carregarFerramentas();
            } else {
                throw new Error(resultado.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('Erro ao salvar ferramenta:', error);
            this.mostrarNotificacao(`Erro ao salvar: ${error.message}`, 'danger');
        }
    }
 
    async importarFerramentas() {
         try {
            const response = await fetch('/api/ferramentas/importar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
 
            if (!response.ok) throw new Error('A resposta do servidor não foi bem-sucedida.');
 
            const resultado = await response.json();
            if (resultado.success) {
                this.mostrarNotificacao(resultado.message, 'success');
                this.fecharModalImportar();
                this.carregarFerramentas();
            } else {
                throw new Error(resultado.message || 'Erro desconhecido na importação.');
            }
        } catch (error) {
            console.error('Erro:', error);
            this.mostrarNotificacao(`Erro ao importar: ${error.message}`, 'danger');
        }
    }
 
    mostrarNotificacao(mensagem, tipo) {
        const notificacao = document.createElement('div');
        notificacao.className = `fixed top-5 right-5 p-4 rounded-lg text-white ${tipo === 'success' ? 'bg-green-500' : 'bg-red-500'}`;
        notificacao.textContent = mensagem;
        document.body.appendChild(notificacao);
 
        setTimeout(() => {
            notificacao.remove();
        }, 3000);
    }
}
 
let gerenciador;
document.addEventListener('DOMContentLoaded', () => {
    gerenciador = new GerenciadorFerramentas();
});