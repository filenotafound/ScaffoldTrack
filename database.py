import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="cmms_andaimes.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de clientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    contato TEXT,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de obras
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cliente_id INTEGER,
                    endereco TEXT,
                    responsavel TEXT,
                    telefone TEXT,
                    data_inicio DATE,
                    data_fim DATE,
                    status TEXT DEFAULT 'ativa',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            """)
            
            # Tabela de equipamentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    codigo TEXT,
                    medida TEXT,
                    quantidade INTEGER NOT NULL,
                    status TEXT DEFAULT 'disponivel',
                    observacoes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de movimentações
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    equipamento_id INTEGER,
                    obra_id INTEGER,
                    quantidade INTEGER NOT NULL,
                    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responsavel TEXT,
                    observacoes TEXT,
                    FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id),
                    FOREIGN KEY (obra_id) REFERENCES obras (id)
                )
            """)
            
            # Tabela de checklists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checklists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    obra_id INTEGER,
                    responsavel TEXT,
                    data_checklist TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    itens_verificados TEXT,
                    observacoes TEXT,
                    status TEXT DEFAULT 'pendente',
                    FOREIGN KEY (obra_id) REFERENCES obras (id)
                )
            """)
            
            # Tabela de manutenções
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manutencoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipamento_id INTEGER,
                    tipo TEXT NOT NULL,
                    descricao TEXT,
                    data_manutencao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responsavel TEXT,
                    custo REAL,
                    status TEXT DEFAULT 'pendente',
                    FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id)
                )
            """)
            
            conn.commit()
    
    # Métodos para clientes
    def add_cliente(self, nome, contato, telefone, email, endereco):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (nome, contato, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, contato, telefone, email, endereco))
            conn.commit()
            return cursor.lastrowid
    
    def get_clientes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes ORDER BY nome")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_clientes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clientes")
            return cursor.fetchone()[0]
    
    def update_cliente(self, id, nome, contato, telefone, email, endereco):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clientes 
                SET nome=?, contato=?, telefone=?, email=?, endereco=?
                WHERE id=?
            """, (nome, contato, telefone, email, endereco, id))
            conn.commit()
    
    def delete_cliente(self, id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id=?", (id,))
            conn.commit()
    
    # Métodos para obras
    def add_obra(self, nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO obras (nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim))
            conn.commit()
            return cursor.lastrowid
    
    def get_obras(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.nome as cliente_nome 
                FROM obras o 
                LEFT JOIN clientes c ON o.cliente_id = c.id 
                ORDER BY o.nome
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_obra(self, id, nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE obras 
                SET nome=?, cliente_id=?, endereco=?, responsavel=?, telefone=?, data_inicio=?, data_fim=?, status=?
                WHERE id=?
            """, (nome, cliente_id, endereco, responsavel, telefone, data_inicio, data_fim, status, id))
            conn.commit()
    
    def delete_obra(self, id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obras WHERE id=?", (id,))
            conn.commit()
    
    # Métodos para equipamentos
    def add_equipamento(self, descricao, codigo, medida, quantidade, observacoes):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO equipamentos (descricao, codigo, medida, quantidade, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (descricao, codigo, medida, quantidade, observacoes))
            conn.commit()
            return cursor.lastrowid
    
    def get_equipamentos(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipamentos ORDER BY descricao")
            return [dict(row) for row in cursor.fetchall()]
    
    def equipamento_existe(self, descricao, equipamento_id=None):
        """Verifica se já existe um equipamento com a mesma descrição"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if equipamento_id:
                # Para edição, excluir o próprio equipamento da verificação
                cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE descricao = ? AND id != ?", 
                             (descricao, equipamento_id))
            else:
                # Para novo cadastro
                cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE descricao = ?", (descricao,))
            
            return cursor.fetchone()[0] > 0
    
    def get_total_equipamentos(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(quantidade) FROM equipamentos")
            result = cursor.fetchone()[0]
            return result if result else 0
    
    def get_equipamentos_by_status(self, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipamentos WHERE status=?", (status,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_equipamentos_status_summary(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, SUM(quantidade) as quantidade 
                FROM equipamentos 
                GROUP BY status
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_equipamento(self, id, descricao, codigo, medida, quantidade, status, observacoes):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE equipamentos 
                SET descricao=?, codigo=?, medida=?, quantidade=?, status=?, observacoes=?
                WHERE id=?
            """, (descricao, codigo, medida, quantidade, status, observacoes, id))
            conn.commit()
    
    def delete_equipamento(self, id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM equipamentos WHERE id=?", (id,))
            conn.commit()
    
    # Métodos para movimentações
    def add_movimentacao(self, tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes, data_movimentacao=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if data_movimentacao:
                # Converter date para datetime se necessário
                if hasattr(data_movimentacao, 'strftime'):
                    data_str = data_movimentacao.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    data_str = str(data_movimentacao) + ' 00:00:00'
                
                cursor.execute("""
                    INSERT INTO movimentacoes (tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes, data_movimentacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes, data_str))
            else:
                cursor.execute("""
                    INSERT INTO movimentacoes (tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (tipo, equipamento_id, obra_id, quantidade, responsavel, observacoes))
            conn.commit()
            return cursor.lastrowid
    
    def get_movimentacoes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, e.descricao as equipamento_descricao, o.nome as obra_nome
                FROM movimentacoes m
                LEFT JOIN equipamentos e ON m.equipamento_id = e.id
                LEFT JOIN obras o ON m.obra_id = o.id
                ORDER BY m.data_movimentacao DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_movimentacoes(self, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.tipo, e.descricao as equipamento, o.nome as obra, m.quantidade, m.data_movimentacao
                FROM movimentacoes m
                LEFT JOIN equipamentos e ON m.equipamento_id = e.id
                LEFT JOIN obras o ON m.obra_id = o.id
                ORDER BY m.data_movimentacao DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Métodos para checklists
    def add_checklist(self, tipo, obra_id, responsavel, itens_verificados, observacoes):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checklists (tipo, obra_id, responsavel, itens_verificados, observacoes)
                VALUES (?, ?, ?, ?, ?)
            """, (tipo, obra_id, responsavel, itens_verificados, observacoes))
            conn.commit()
            return cursor.lastrowid
    
    def get_checklists(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, o.nome as obra_nome
                FROM checklists c
                LEFT JOIN obras o ON c.obra_id = o.id
                ORDER BY c.data_checklist DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_checklist_status(self, id, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE checklists SET status=? WHERE id=?", (status, id))
            conn.commit()
    
    # Métodos para manutenções
    def add_manutencao(self, equipamento_id, tipo, descricao, responsavel, custo):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO manutencoes (equipamento_id, tipo, descricao, responsavel, custo)
                VALUES (?, ?, ?, ?, ?)
            """, (equipamento_id, tipo, descricao, responsavel, custo))
            conn.commit()
            return cursor.lastrowid
    
    def get_manutencoes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, e.descricao as equipamento_descricao
                FROM manutencoes m
                LEFT JOIN equipamentos e ON m.equipamento_id = e.id
                ORDER BY m.data_manutencao DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # Métodos para controle de estoque
    def get_quantidade_disponivel(self, equipamento_id):
        """Calcula quantidade disponível baseada no estoque total menos envios e manutenções não retornados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Buscar quantidade total do equipamento
            cursor.execute("SELECT quantidade FROM equipamentos WHERE id = ?", (equipamento_id,))
            result = cursor.fetchone()
            if not result:
                return 0
            quantidade_total = result[0]
            
            # Calcular saldo de movimentações
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'envio' THEN quantidade ELSE 0 END), 0) as total_enviado,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno' THEN quantidade ELSE 0 END), 0) as total_retornado,
                    COALESCE(SUM(CASE WHEN tipo = 'manutencao' THEN quantidade ELSE 0 END), 0) as total_manutencao,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno_manutencao' THEN quantidade ELSE 0 END), 0) as total_retorno_manutencao,
                    COALESCE(SUM(CASE WHEN tipo = 'perda' THEN quantidade ELSE 0 END), 0) as total_perdas,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno_perda' THEN quantidade ELSE 0 END), 0) as total_retorno_perdas
                FROM movimentacoes 
                WHERE equipamento_id = ?
            """, (equipamento_id,))
            
            movimentacao = cursor.fetchone()
            total_enviado = movimentacao[0] if movimentacao else 0
            total_retornado = movimentacao[1] if movimentacao else 0
            total_manutencao = movimentacao[2] if movimentacao else 0
            total_retorno_manutencao = movimentacao[3] if movimentacao else 0
            total_perdas = movimentacao[4] if movimentacao else 0
            total_retorno_perdas = movimentacao[5] if movimentacao else 0
            
            # Quantidade fora do estoque = enviados não retornados + em manutenção + perdas líquidas
            quantidade_enviada = total_enviado - total_retornado
            quantidade_em_manutencao = total_manutencao - total_retorno_manutencao
            quantidade_perdida_liquida = total_perdas - total_retorno_perdas
            quantidade_indisponivel = quantidade_enviada + quantidade_em_manutencao + quantidade_perdida_liquida
            
            quantidade_disponivel = quantidade_total - quantidade_indisponivel
            
            return max(0, quantidade_disponivel)
    
    def get_equipamentos_enviados_obra(self, obra_id):
        """Retorna equipamentos enviados para uma obra específica com quantidades"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.descricao, 
                       SUM(CASE WHEN m.tipo = 'envio' THEN m.quantidade ELSE 0 END) -
                       SUM(CASE WHEN m.tipo = 'retorno' THEN m.quantidade ELSE 0 END) as quantidade_enviada
                FROM equipamentos e
                JOIN movimentacoes m ON e.id = m.equipamento_id
                WHERE m.obra_id = ?
                GROUP BY e.id, e.descricao
                HAVING quantidade_enviada > 0
            """, (obra_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_quantidade_enviada_obra(self, equipamento_id, obra_id):
        """Calcula quantidade enviada para uma obra específica"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'envio' THEN quantidade ELSE 0 END), 0) as enviado,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno' THEN quantidade ELSE 0 END), 0) as retornado
                FROM movimentacoes 
                WHERE equipamento_id = ? AND obra_id = ? AND tipo IN ('envio', 'retorno')
            """, (equipamento_id, obra_id))
            
            result = cursor.fetchone()
            enviado = result[0] if result else 0
            retornado = result[1] if result else 0
            
            return max(0, enviado - retornado)
    
    def get_quantidade_em_manutencao(self, equipamento_id):
        """Calcula quantidade em manutenção (enviadas para manutenção - retornadas da manutenção)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'manutencao' THEN quantidade ELSE 0 END), 0) as total_manutencao,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno_manutencao' THEN quantidade ELSE 0 END), 0) as total_retorno_manutencao
                FROM movimentacoes 
                WHERE equipamento_id = ?
            """, (equipamento_id,))
            
            result = cursor.fetchone()
            total_manutencao = result[0] if result else 0
            total_retorno_manutencao = result[1] if result else 0
            
            return max(0, total_manutencao - total_retorno_manutencao)
    
    def get_quantidade_perdida(self, equipamento_id):
        """Calcula quantidade perdida (perdas - retornos de perda)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN tipo = 'perda' THEN quantidade ELSE 0 END), 0) as total_perdas,
                    COALESCE(SUM(CASE WHEN tipo = 'retorno_perda' THEN quantidade ELSE 0 END), 0) as total_retorno_perdas
                FROM movimentacoes 
                WHERE equipamento_id = ?
            """, (equipamento_id,))
            
            result = cursor.fetchone()
            total_perdas = result[0] if result else 0
            total_retorno_perdas = result[1] if result else 0
            
            return max(0, total_perdas - total_retorno_perdas)
    
    def validar_movimentacao(self, tipo, equipamento_id, obra_id, quantidade):
        """Valida se a movimentação é possível"""
        if tipo == 'envio':
            disponivel = self.get_quantidade_disponivel(equipamento_id)
            if quantidade > disponivel:
                return False, f"Quantidade disponível insuficiente. Disponível: {disponivel}"
        
        elif tipo == 'retorno':
            if obra_id:
                enviada = self.get_quantidade_enviada_obra(equipamento_id, obra_id)
                if quantidade > enviada:
                    return False, f"Quantidade de retorno superior ao enviado. Enviado para esta obra: {enviada}"
            else:
                return False, "Obra é obrigatória para retornos"
        
        elif tipo == 'manutencao':
            disponivel = self.get_quantidade_disponivel(equipamento_id)
            if quantidade > disponivel:
                return False, f"Quantidade disponível insuficiente para manutenção. Disponível: {disponivel}"
        
        elif tipo == 'retorno_manutencao':
            em_manutencao = self.get_quantidade_em_manutencao(equipamento_id)
            if quantidade > em_manutencao:
                return False, f"Quantidade em manutenção insuficiente. Em manutenção: {em_manutencao}"
        
        elif tipo == 'retorno_perda':
            perdidas = self.get_quantidade_perdida(equipamento_id)
            if quantidade > perdidas:
                return False, f"Quantidade perdida insuficiente. Perdidas: {perdidas}"
        
        return True, "Movimentação válida"
