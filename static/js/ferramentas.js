
class GerenciadorFerramentas {
    constructor() {
        this.ferramentas = []; // Armazena todas as ferramentas carregadas
        this.tabelaCorpo = document.querySelector('table tbody');
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.carregarFerramentas();
    }

    cacheElements() {
        // Botões de ação principais
        this.btnAdicionar = document.getElementById('btnAdicionarFerramenta');
        this.btnImportar = document.getElementById('btnImportarFerramenta');
        this.btnAtualizar = document.getElementById('btnAtualizar');

        // Modal de Adicionar/Editar
        this.modalAdicionar = document.getElementById('modalAdicionarFerramenta');
        this.formAdicionar = document.getElementById('formAdicionarFerramenta');
        this.btnSalvarFerramenta = this.formAdicionar.querySelector('button[type="submit"]');
        this.btnCancelarAdicionar = document.getElementById('btnCancelarAdicionar');

        // Modal de Importação
        this.modalImportar = document.getElementById('modalImportarFerramenta');
        this.formImportar = document.getElementById('formImportarFerramenta');
        this.btnExecutarImportacao = this.formImportar.querySelector('button[type="submit"]');
        this.btnCancelarImportar = document.getElementById('btnCancelarImportar');
    }

    bindEvents() {
        this.btnAdicionar?.addEventListener('click', () => this.abrirModal(this.modalAdicionar));
        this.btnImportar?.addEventListener('click', () => this.abrirModal(this.modalImportar));
        this.btnAtualizar?.addEventListener('click', () => this.carregarFerramentas());
        this.btnCancelarAdicionar?.addEventListener('click', () => this.fecharModal(this.modalAdicionar));
        this.btnCancelarImportar?.addEventListener('click', () => this.fecharModal(this.modalImportar));
        
        this.btnSalvarFerramenta.addEventListener('click', (e) => {
            e.preventDefault(); 
            this.salvarFerramenta();
        });

        this.btnExecutarImportacao.addEventListener('click', (e) => {
            e.preventDefault();
            this.importarFerramentas();
        });
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
        modal?.classList.remove('hidden');
    }

    fecharModal(modal) {
        modal?.classList.add('hidden');
    }

    async salvarFerramenta() {        const form = this.formAdicionar;
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
        if (!confirm('Deseja iniciar a importação de ferramentas do arquivo? Esta ação pode levar alguns instantes.')) return;
    
        const btn = this.btnExecutarImportacao;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Importando...';
    
        try {
            const resp = await fetch('/api/ferramentas/importar', { method: 'POST' });
            const resultado = await resp.json();
            if (resp.ok && resultado.success) {
                this.notificar(resultado.message, 'success');
                this.fecharModal(this.modalImportar);
                this.carregarFerramentas();
            } else {
                throw new Error(resultado.message || `Erro no servidor: ${resp.statusText}`);
            }
        } catch (err) {
            this.notificar(`Falha na importação: ${err.message}`, 'danger');
            console.error(err);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload mr-2"></i>Importar';
        }
    }


    notificar(msg, tipo = 'success') {
        const div = document.createElement('div');
        div.className = `fixed top-5 right-5 p-4 rounded-lg text-white ${tipo === 'success' ? 'bg-green-500' : 'bg-red-500'}`;
        div.textContent = msg;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }
}
document.addEventListener('DOMContentLoaded', () => new GerenciadorFerramentas());
