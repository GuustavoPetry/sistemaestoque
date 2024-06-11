import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
from sqlalchemy import create_engine, text
# from apimercadopago import gerar_link_pagamento
data = datetime.now().strftime('%Y-%m-%d')


def conexao_db():
    return mysql.connector.connect(
        host=st.secrets["db_host"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        database=st.secrets["database"]
    )


def conn_sqlalchemy():
    return create_engine(f"mysql+mysqlconnector://{st.secrets['db_user']}:{st.secrets['db_password']}"
                         f"@{st.secrets['db_host']}/{st.secrets['database']}")


def deleta_carrinho():
    conn = conexao_db()
    cursor = conn.cursor()
    sql1 = 'TRUNCATE TABLE carrinho;'
    cursor.execute(sql1)
    conn.commit()


def verifica_credenciais(username, password):
    try:
        conn = conexao_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nome_usuario, senha_usuario FROM usuarios "
                       "WHERE nome_usuario = %s AND senha_usuario = %s", (username, password))
        usuario = cursor.fetchone()
        print(usuario)
        conn.commit()
        return usuario
    except mysql.connector.errors.DatabaseError:
        pass
        st.error("❌ Dados de acesso inválidos!! ❌")


# Interface de login
def login():
    st.title("Sistema Estoque Inteligente")
    st.subheader("Informe os Dados de Acesso")
    nome_usuario = st.text_input("Nome de Usuário:")
    senha_usuario = st.text_input("Senha:", type="password")
    botao_login = st.button("Login")
    if botao_login:
        usuario = verifica_credenciais(nome_usuario, senha_usuario)
        print(usuario)
        if usuario:
            st.session_state['authenticated'] = True
            st.session_state['username'] = usuario['nome_usuario']
            st.experimental_rerun()
        else:
            st.error("❌ Dados de acesso inválidos!! ❌")


def menu():

    with st.sidebar:
        if st.button('Cadastrar Produtos'):
            st.session_state.form_to_show = 'cadastro-produtos'

        if st.button('Entrada de Produtos'):
            st.session_state.form_to_show = 'entrada-produtos'

        if st.button('Aplicar Promoções'):
            st.session_state.form_to_show = 'aplicar-promo'

        if st.button('Visualizar Relatórios'):
            st.session_state.form_to_show = 'relatorios'

        if st.button('Cadastrar Usuários'):
            st.session_state.form_to_show = 'cadastro-usuario'

        if st.button('Seção de Vendas'):
            st.session_state.form_to_show = 'secao-vendas'

        if st.sidebar.button("Sair"):
            st.session_state.form_to_show = None
            st.session_state['authenticated'] = False
            st.session_state.pop('username')
            st.session_state.clear()
            st.experimental_rerun()

    if st.session_state.form_to_show == 'cadastro-produtos':
        cadastrar_produto()

    elif st.session_state.form_to_show == 'entrada-produtos':
        entrada_produtos()

    elif st.session_state.form_to_show == 'aplicar-promo':
        aplicar_promocoes()

    elif st.session_state.form_to_show == 'relatorios':
        visualizar_relatorios()

    elif st.session_state.form_to_show == 'cadastro-usuario':
        cadastrar_usuario()

    elif st.session_state.form_to_show == 'secao-vendas':
        secao_vendas()


def cadastrar_produto():
    tab1, tab2, tab3, tab4 = st.tabs(['Cadastrar Produto', 'Atualizar Preço', 'Atualizar Marca', 'Atualizar Nome'])
    if st.session_state.form_to_show == 'cadastro-produtos':

        with tab1:

            with st.form('cadastrar-produto', True):
                st.title("Seção para Cadastro de Produtos")
                st.subheader("informe os Dados do Produto que deseja Cadastrar")
                marca_produto = st.text_input('Marca:', placeholder='Marca do Produto')
                nome_produto = st.text_input('Nome:', placeholder='Nome do Produto')
                cod_barras = st.text_input('Cód. Barras:', placeholder='Código de Barras')
                preco_produto = st.number_input('Preço:')
                botao_cad = st.form_submit_button("Cadastrar")
                if botao_cad:
                    conn = conexao_db()
                    cursor = conn.cursor()
                    sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                    dados = (st.session_state['username'],)
                    cursor.execute(sql, dados)
                    nivel_acesso = cursor.fetchall()[0][0]
                    if nivel_acesso == 3:

                        if marca_produto != '' and nome_produto != '' and cod_barras != '' and preco_produto > 0:
                            try:

                                sql1 = ('INSERT INTO produtos(marca_produto, nome_produto, cod_barras, preco, '
                                        'numero_vendas) VALUES (%s, %s, %s, %s, %s);')
                                dados1 = (marca_produto, nome_produto, cod_barras, preco_produto, 0)
                                cursor.execute(sql1, dados1)

                                select = f'SELECT id FROM produtos WHERE cod_barras = {cod_barras}'
                                cursor.execute(select)
                                produto_id = cursor.fetchall()[0][0]

                                sql2 = ('INSERT INTO precos_produtos(produto_id, cod_barras, preco_produto, '
                                        'data_inicio, data_termino) VALUES (%s, %s, %s, %s, %s);')
                                sql3 = 'INSERT INTO estoque(produto_id, cod_barras, qtd_estoque) VALUES (%s, %s, %s);'

                                dados2 = (produto_id, cod_barras, preco_produto, data, data)
                                dados3 = (produto_id, cod_barras, 0)
                                print(produto_id, cod_barras, data)

                                cursor.execute(sql2, dados2)
                                cursor.execute(sql3, dados3)
                                conn.commit()
                                print('finalizado')
                                st.success('✅ Produto Cadastrado no Sistema ✅')
                            except mysql.connector.errors.IntegrityError:
                                st.error('❌ Erro! Já existe um cadastro com este código de barras ou nome ❌')
                        else:
                            st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')
                    else:
                        st.error('❌ Nível de acesso não permitido para esta ação! ❌')
        with tab2:
            with st.form('atualizar-preco', True):
                st.title('Atualizar Preço de Produto')
                st.subheader('Preencha os Campos para Atualizar o Preço do Produto')
                cod_barras_up = st.text_input('Informe o Código de Barras do Produto:', placeholder='Código de Barras')
                preco_up = st.number_input('Escolha um novo Preço para o produto:')

                if st.form_submit_button('Atualizar Preço'):
                    if cod_barras_up != '' and preco_up > 0:
                        conn = conexao_db()
                        cursor = conn.cursor()
                        sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                        dados = (st.session_state['username'],)
                        cursor.execute(sql, dados)
                        nivel_acesso = cursor.fetchall()[0][0]

                        if nivel_acesso == 3:
                            sql = ('UPDATE produtos p1 JOIN (SELECT id FROM produtos WHERE cod_barras = %s) '
                                   'p2 ON p1.id = p2.id SET p1.preco = %s;')
                            dados = (cod_barras_up, preco_up)
                            cursor.execute(sql, dados)
                            conn.commit()
                            st.success(f'O Preço do Produto foi Atualizado para R${preco_up} ✅')
                        else:
                            st.error('Nível de Acesso não permitido para está ação ❌')
                    else:
                        st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')

        with tab3:
            with st.form('atualizar-marca', True):
                st.title('Atualizar Marca de Produto')
                st.subheader('Preencha os Campos para Atualizar a Marca do Produto')
                cod_barras_up = st.text_input('Informe o Código de Barras do Produto:', placeholder='Código de Barras')
                marca_up = st.text_input('Escolha uma Nova Marca:', placeholder='Nova Marca do Produto')

                if st.form_submit_button('Atualizar Marca'):
                    if cod_barras_up != '' and marca_up != '':
                        conn = conexao_db()
                        cursor = conn.cursor()
                        sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                        dados = (st.session_state['username'],)
                        cursor.execute(sql, dados)
                        nivel_acesso = cursor.fetchall()[0][0]

                        if nivel_acesso == 3:
                            sql = ('UPDATE produtos p1 JOIN (SELECT id FROM produtos WHERE cod_barras = %s) '
                                   'p2 ON p1.id = p2.id SET p1.marca_produto = %s;')
                            dados = (cod_barras_up, marca_up)
                            cursor.execute(sql, dados)
                            conn.commit()
                            st.success(f'Marca do Produto Atualizada para {marca_up} ✅')
                        else:
                            st.error('Nível de Acesso não permitido para esta ação ❌')
                    else:
                        st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')

        with tab4:
            with st.form('atualizar-nome-produto'):
                st.title('Atualizar Nome de Produto')
                st.subheader('Preencha os Campos para Atualizar o Nome do Produto')
                cod_barras_up = st.text_input('Informe o Código de Barras do Produto:', placeholder='Código de Barras')
                nome_produto_up = st.text_input('Escolha um Novo Nome:', placeholder='Novo Nome do Produto')

                if st.form_submit_button('Atualizar Nome'):
                    if cod_barras_up != '' and nome_produto_up != '':
                        conn = conexao_db()
                        cursor = conn.cursor()
                        sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                        dados = (st.session_state['username'],)
                        cursor.execute(sql, dados)
                        nivel_acesso = cursor.fetchall()[0][0]

                        if nivel_acesso == 3:
                            sql = ('UPDATE produtos p1 JOIN (SELECT id FROM produtos WHERE cod_barras = %s) '
                                   'p2 ON p1.id = p2.id SET p1.nome_produto = %s;')
                            dados = (cod_barras_up, nome_produto_up)
                            cursor.execute(sql, dados)
                            conn.commit()
                            st.success(f'Nome do Produto Atualizado para {nome_produto_up} ✅')
                        else:
                            st.error('Nível de Acesso não permitido para está ação ❌')
                    else:
                        st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')


def entrada_produtos():
    if st.session_state.form_to_show == 'entrada-produtos':
        with st.form('entrada-produtos', True):
            st.title("Seção para Entrada de Produtos")
            st.subheader("preencha os Campos para Entrada de Produtos")
            cod_barras = st.text_input("Código de Barras:", placeholder='Cód. Barras')
            preco_entrada = st.number_input("Preço de Entrada:")
            quantidade = st.text_input("Quantidade:", placeholder='Quantidade')
            botao_cad = st.form_submit_button('Registrar')
            if botao_cad:
                if cod_barras != '' and preco_entrada != '' and quantidade != '':
                    try:
                        conn = conexao_db()
                        cursor = conn.cursor()
                        select = f'SELECT id FROM produtos WHERE cod_barras = {cod_barras}'
                        cursor.execute(select)
                        produto_id = cursor.fetchall()[0][0]

                        sql1 = ('INSERT INTO entradas(produto_id, cod_barras, preco, qtd_entrada, data_entrada) '
                                'VALUES (%s, %s, %s , %s, %s);')
                        sql2 = 'UPDATE estoque SET qtd_estoque =  qtd_estoque + %s WHERE cod_barras = %s;'

                        dados1 = (produto_id, cod_barras, preco_entrada, quantidade, data)
                        dados2 = (quantidade, cod_barras)

                        cursor.execute(sql1, dados1)
                        cursor.execute(sql2, dados2)
                        conn.commit()
                        st.success('✅ O Produto foi inserido no estoque ✅')
                    except mysql.connector.errors.DatabaseError:
                        st.error('❌ Erro! Somente números inteiros para quantidade ❌')
                    except IndexError:
                        st.error('❌ Erro! O Produto não está cadastrado no sistema ❌')
                else:
                    st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')


def aplicar_promocoes():
    if st.session_state.form_to_show == 'aplicar-promo':

        with st.form('aplicar-promocao', True):
            st.title("Seção para Aplicar Promoções")
            st.subheader("preencha as Informações da Promoção")
            cod_barras = st.text_input('Código de Barras:', placeholder='Cód. Barras')
            preco_promo = st.text_input('Preço Promocional', placeholder='Valor Promocional')
            data_inicio = data
            data_termino = st.date_input('Data FIM da Promoção:')
            botao_cad = st.form_submit_button('Aplicar')

            if botao_cad:
                conn = conexao_db()
                cursor = conn.cursor()
                sql = 'SELECT cod_barras FROM produtos;'
                cursor.execute(sql)

                if cod_barras in cursor.fetchall() and cod_barras != '' and preco_promo != '':
                    select = f'SELECT id FROM produtos WHERE cod_barras = {cod_barras}'
                    cursor.execute(select)
                    produto_id = cursor.fetchall()[0][0]

                    sql = ('INSERT INTO precos_produtos(produto_id, cod_barras, preco_produto, data_inicio, '
                           'data_termino) VALUES (%s, %s, %s, %s, %s);')
                    dados = (produto_id, cod_barras, preco_promo, data_inicio, data_termino)
                    cursor.execute(sql, dados)
                    conn.commit()
                else:
                    st.error('❌ Erro! O Produto não é cadastrado no sistema ❌')


def visualizar_relatorios():
    if st.session_state.form_to_show == 'relatorios':
        st.title("Seção para Análise de Relatórios")
        st.subheader("Navegue entre as abas para visualizar os diferentes tipos de relatórios")
        tab1, tab2, tab3 = st.tabs(['Estoque Atual', '+ Vendidos (30 Dias)', '+ Vendidos (Geral)'])
        with tab1:
            conn = conn_sqlalchemy()
            with conn.connect():
                sql = text('SELECT estoque.cod_barras AS "CÓDIGO DE BARRAS", produtos.nome_produto AS PRODUTO, '
                           'estoque.qtd_estoque AS QUANTIDADE FROM estoque '
                           'INNER JOIN produtos ON estoque.produto_id = produtos.id '
                           'ORDER BY estoque.qtd_estoque ASC;')
                tabela_estoque = pd.read_sql(sql, conn)
                st.dataframe(tabela_estoque, hide_index=True, use_container_width=True)

        with tab2:
            conn = conn_sqlalchemy()
            with conn.connect():
                sql = text('''
                           SELECT 
                            pv.cod_barras AS "CÓDIGO DE BARRAS", 
                            p.nome_produto AS PRODUTO, 
                            SUM(pv.qtd_vendida) AS VENDAS
                           FROM 
                            produtos_vendidos pv
                           INNER JOIN 
                            produtos p ON pv.produto_id = p.id
                           WHERE 
                            pv.data_venda >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                           GROUP BY 
                            pv.cod_barras, p.nome_produto
                           ORDER BY VENDAS DESC;
                           ''')
                tabela_vendas30 = pd.read_sql(sql, conn)
                st.dataframe(tabela_vendas30, hide_index=True, use_container_width=True)

        with tab3:
            conn = conn_sqlalchemy()
            with conn.connect():
                sql = text('SELECT cod_barras AS "CÓDIGO DE BARRAS", nome_produto AS PRODUTO, '
                           'numero_vendas AS VENDAS FROM produtos ORDER BY numero_vendas DESC;')
                tabela_vendas_geral = pd.read_sql(sql, conn)
                st.dataframe(tabela_vendas_geral, hide_index=True, use_container_width=True)


def cadastrar_usuario():
    tab1, tab2, tab3 = st.tabs(['Cadastrar Usuário', 'Alterar Nome Usuário', 'Alterar Senha Usuário'])
    if st.session_state.form_to_show == 'cadastro-usuario':

        with tab1:
            with (st.form('cadastro_usuario', True)):
                st.title("Seção para Cadastro de Usuários")
                st.subheader("Preencha os dados do usuário que deseja cadastrar")
                nome = st.text_input('Nome Completo:', placeholder='Nome Completo')
                data_nascimento = st.date_input('Data de Nascimento')
                cpf = st.text_input('CPF:', placeholder='Informe o CPF')
                nome_usuario = st.text_input('Nome de Usuário:', placeholder='Username')
                senha_usuario = st.text_input('Senha:', type='password', placeholder='Senha')
                confirma_senha = st.text_input('Confirme a Senha:', type='password', placeholder='Senha')
                botao_cad = st.form_submit_button('Cadastrar')
                if botao_cad:
                    conn = conexao_db()
                    cursor = conn.cursor()
                    sql = 'SELECT nome_usuario, cpf FROM usuarios;'
                    cursor.execute(sql)
                    lista_usuarios = []

                    for user in cursor.fetchall():
                        lista_usuarios.append(user[0])
                        lista_usuarios.append(user[1])

                    sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                    dados = (st.session_state['username'],)
                    cursor.execute(sql, dados)
                    nivel_acesso = cursor.fetchall()[0][0]
                    if nivel_acesso == 3:
                        if nome_usuario not in lista_usuarios and cpf not in lista_usuarios:
                            if senha_usuario == confirma_senha:
                                if nome != '' and cpf != '' and nome_usuario != '' and senha_usuario != '':
                                    sql = ('INSERT INTO usuarios(nome_completo, data_nascimento, cpf, nome_usuario, '
                                           'senha_usuario, nivel_acesso) '
                                           'VALUES (%s, %s, %s, %s, %s, %s)')
                                    dados = (nome, data_nascimento, cpf, nome_usuario, senha_usuario, 1)
                                    cursor.execute(sql, dados)
                                    conn.commit()
                                    st.success('✅ Usuário Cadastrado com Sucesso ✅')
                                else:
                                    st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')
                            else:
                                st.error('❌ Erro! Você informou 2 senhas diferentes ❌')
                        else:
                            st.error('❌ Erro! Já existe um usuário com estes dados cadastrados! ❌')
                    else:
                        st.error('❌ Nível de acesso não permitido para esta ação! ❌')

        with tab2:
            with st.form('atualizar-nome-usuario', True):
                st.title('Alterar Nome de Usuário')
                st.subheader('Preencha os Campos para Alterar Nome de Usuário')
                cpf_up = st.text_input('CPF do Usuário que deseja Alterar o Nome:', placeholder='Informe o CPF')
                nome_usuario_up = st.text_input('Novo Nome de Usuário', placeholder='Escolha um novo Nome de Usuário')

                if st.form_submit_button('Alterar Username'):
                    if cpf_up != '' and nome_usuario_up != '':
                        conn = conexao_db()
                        cursor = conn.cursor()
                        sql = 'SELECT nivel_acesso FROM usuarios WHERE nome_usuario = %s;'
                        dados = (st.session_state['username'],)
                        cursor.execute(sql, dados)
                        nivel_acesso = cursor.fetchall()[0][0]

                        if nivel_acesso == 3:
                            conn = conexao_db()
                            cursor = conn.cursor()
                            sql = ('UPDATE usuarios user1 JOIN (SELECT id FROM usuarios WHERE cpf = %s) '
                                   'user2 ON user1.id = user2.id SET user1.nome_usuario = %s;')
                            dados = (cpf_up, nome_usuario_up)
                            cursor.execute(sql, dados)
                            conn.commit()
                            st.success(f'Nome de Usuário Alterado para {nome_usuario_up} ✅')
                        else:
                            st.error('Nível de Acesso não permitido para está ação ❌')
                    else:
                        st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')
        with tab3:
            with st.form('atualizar-senha-usuario', True):
                st.title('Alterar Senha de Usuário')
                st.subheader('Preencha os Campos para Alterar Senha do Usuário')
                cpf_up = st.text_input('CPF do Usuário que deseja Alterar a Senha:', placeholder='Informe o CPF')
                senha_usuario_up = st.text_input('Nova Senha do Usuário', placeholder='Escolha uma Nova Senha',
                                                 type='password')
                confirma_senha = st.text_input('Confirme a Senha:', placeholder='Insira a Senha Novamente',
                                               type='password')
                if st.form_submit_button('Alterar Senha'):
                    if cpf_up != '' and senha_usuario_up != '' and confirma_senha != '':
                        conn = conexao_db()
                        cursor = conn.cursor()
                        sql = 'SELECT nivel_acesso FROM usuarios WHERE cpf = %s;'
                        dados = (cpf_up,)
                        cursor.execute(sql, dados)
                        nivel_acesso = cursor.fetchall()[0][0]

                        if nivel_acesso == 3:
                            if senha_usuario_up == confirma_senha:
                                conn = conexao_db()
                                cursor = conn.cursor()
                                sql = ('UPDATE usuarios user1 JOIN (SELECT id FROM usuarios WHERE cpf = %s) '
                                       'user2 ON user1.id = user2.id SET user1.senha_usuario = %s;')
                                dados = (cpf_up, senha_usuario_up)
                                cursor.execute(sql, dados)
                                conn.commit()
                                st.success(f'Senha de Usuário Alterada com Sucesso ✅')
                            else:
                                st.error('Erro! Você informou 2 Senhas diferentes ❌')
                        else:
                            st.error('Nível de Acesso não permitido para está ação ❌')
                    else:
                        st.error('❌ Erro! Preencha todos os dados do produto corretamente ❌')


def secao_vendas():
    if st.session_state.form_to_show == 'secao-vendas':
        col1, col2 = st.columns([0.3, 0.7])

        with col1:
            with st.form('secao-vendas', True):
                st.subheader("Leia o código de todos os produtos")
                cod_barras = st.text_input('Código de Barras:', placeholder='Scaneie o código de barras')
                quantidade = st.number_input('Quantidade:', min_value=1)
                codigos_produtos = []
                if st.form_submit_button('Inserir'):
                    conn = conexao_db()
                    cursor = conn.cursor()
                    sql = 'SELECT cod_barras FROM produtos'
                    cursor.execute(sql)
                    for codigos in cursor.fetchall():
                        codigos_produtos.append(codigos[0])

                    if cod_barras in codigos_produtos:
                        sql1 = 'SELECT nome_produto FROM produtos WHERE cod_barras = %s'
                        dados = (cod_barras,)
                        cursor.execute(sql1, dados)
                        nome_produto = cursor.fetchall()[0][0]

                        try:
                            sql2 = ('SELECT preco_produto FROM precos_produtos WHERE cod_barras = %s '
                                    'AND data_termino > CURDATE() ORDER BY data_termino DESC;')
                            cursor.execute(sql2, dados)
                            preco = cursor.fetchall()[0][0]
                            sql = ('INSERT INTO carrinho(nome_produto, preco, quantidade, valor_total, cod_barras) '
                                   'VALUES (%s, %s, %s, %s, %s);')
                            dados = (nome_produto, preco, quantidade, preco * quantidade, cod_barras)
                            cursor.execute(sql, dados)
                            conn.commit()

                        except IndexError:
                            sql = 'SELECT preco FROM produtos WHERE cod_barras = %s;'
                            dados = (cod_barras,)
                            cursor.execute(sql, dados)
                            preco = cursor.fetchall()[0][0]

                            sql = ('INSERT INTO carrinho(nome_produto, preco, quantidade, valor_total, cod_barras) '
                                   'VALUES (%s, %s, %s, %s, %s);')
                            dados = (nome_produto, preco, quantidade, preco * quantidade, cod_barras)
                            cursor.execute(sql, dados)
                            conn.commit()
                    else:
                        st.error('Erro! O Código informado não está cadastrado no sistema ❌')

            with st.form('cancelar-produto'):
                cancelar_id = st.number_input('Retirar do Carrinho Produto ID:', min_value=1)
                cancelar = st.form_submit_button('Retirar')
                if cancelar:
                    conn = conexao_db()
                    cursor = conn.cursor()
                    sql = 'DELETE FROM carrinho WHERE id = %s;'
                    dados = (cancelar_id,)
                    cursor.execute(sql, dados)
                    conn.commit()

        with col2:
            with st.form('carrinho'):
                st.subheader('Carrinho')
                conn = conn_sqlalchemy()
                with conn.connect():
                    sql = text('SELECT id as ID, nome_produto as PRODUTO, preco AS PRECO, quantidade QUANTIDADE, '
                               'valor_total "VALOR TOTAL" FROM carrinho;')
                    tabela_carrinho = pd.read_sql(sql, conn)
                    st.dataframe(tabela_carrinho, hide_index=True, use_container_width=True)

                if st.form_submit_button('Finalizar Compra'):
                    conn = conexao_db()
                    cursor = conn.cursor()

                    sql = 'SELECT * FROM carrinho;'
                    cursor.execute(sql)
                    if len(cursor.fetchall()) > 0:

                        sql = 'SELECT SUM(valor_total) FROM carrinho'
                        cursor.execute(sql)
                        total_compra = cursor.fetchall()[0][0]

                        sql = 'INSERT INTO vendas(data_venda, valor_venda) VALUES (%s, %s);'
                        dados = (data, total_compra)
                        cursor.execute(sql, dados)
                        conn.commit()

                        sql = 'SELECT MAX(id) FROM vendas;'
                        cursor.execute(sql)
                        venda_id = cursor.fetchall()[0][0]

                        sql = 'SELECT cod_barras, quantidade FROM carrinho;'
                        cursor.execute(sql)
                        carrinho = cursor.fetchall()

                        for item in carrinho:
                            cod_barras = item[0]
                            quantidade = item[1]

                            sql = "SELECT id FROM produtos WHERE cod_barras = %s;"
                            dados = (cod_barras,)
                            cursor.execute(sql, dados)
                            produto_id = cursor.fetchall()[0][0]

                            sql1 = 'UPDATE estoque SET qtd_estoque = qtd_estoque - %s WHERE cod_barras = %s;'
                            sql2 = 'UPDATE produtos SET numero_vendas = numero_vendas + %s WHERE cod_barras = %s;'
                            sql3 = ('INSERT INTO produtos_vendidos(produto_id, venda_id, cod_barras, qtd_vendida, '
                                    'data_venda) VALUES (%s, %s, %s, %s, %s);')

                            dados1 = (quantidade, cod_barras)
                            dados2 = (quantidade, cod_barras)
                            dados3 = (produto_id, venda_id, cod_barras, quantidade, data)

                            cursor.execute(sql1, dados1)
                            cursor.execute(sql2, dados2)
                            cursor.execute(sql3, dados3)
                            conn.commit()

                        carrinho.clear()
                        deleta_carrinho()
                        st.experimental_rerun()

                if st.form_submit_button('Cancelar Compra'):
                    deleta_carrinho()
                    st.experimental_rerun()


def main():
    st.set_page_config(page_title="Estoque Inteligente", layout="wide", page_icon="🍻")
    css_botao()
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.session_state['authenticated']:
        if 'form_to_show' not in st.session_state:
            st.session_state.form_to_show = 'secao-vendas'
        menu()
    else:
        login()


def css_botao():
    # Adiciona o CSS personalizado
    css = """
    <style>
    .stButton>button {
        background-color: #041360;
        color: #dae6e6;
        text-align: center;
        display: inline-block;
        width: 100%;
        padding: 12px;
    }
    .stButton>button:hover {
        background-color: #271bda;
        color: #dae6e6;
    }
    .e1f1d6gn4:nth-child(7) .ef3psqc12:hover {
        background-color: #942020;
        color: white;
    }
    .e1f1d6gn4:nth-child(7) .ef3psqc12 {
        color: #dae6e6;
        background-color: #6d0f0f;
    }
    .e1f1d6gn4:nth-child(9) .ef3psqc12{
        color: #dae6e6;
        background-color: #6d0f0f;
    }
    .e1f1d6gn4:nth-child(9) .ef3psqc12:hover {
        background-color: #942020;
        color: white;
    }
    .e1f1d6gn4:nth-child(8) .ef3psqc12{
        color: #dae6e6;
        background-color: #6d0f0f;
        width: 100%;
        padding: 0px;
    }
    .e1f1d6gn4:nth-child(8) .ef3psqc12:hover {
        background-color: #942020;
        color: white;
    }
    .e1f1d6gn4:nth-child(6) .ef3psqc12 {
        color: #dae6e6;
        background-color: #096004;
    }
    .e1f1d6gn4:nth-child(6) .ef3psqc12:hover {
        color: #dae6e6;
        background-color: #12b716;
    }
    .e1f1d6gn4:nth-child(3) .ef3psqc7 {
        color: #dae6e6;
        background-color: #096004;
    }
    .e1f1d6gn4:nth-child(3) .ef3psqc7:hover {
        color: #dae6e6;
        background-color: #12b716;
    }
    .e10yg2by1+ .e10yg2by1 .ef3psqc7 {
        color: #dae6e6;
        background-color: #6d0f0f;
        padding: 0px
    }
    .e10yg2by1+ .e10yg2by1 .ef3psqc7:hover {
        background-color: #942020;
        color: white;
    }
    .ea3mdgi8 {
        background-color: #0c1020;
    }
    .ezrtsby2 {
        background-color: #0c1020;
    }
    .eczjsme3 {
        background-color: #1a1a1d;
    }
    .e1nzilvr1 {
        color: #bec1ca;
    }
    #root :nth-child(1) {
        color: #dae6e6;
    }
    .st-emotion-cache-uko8fv .ef3psqc7 {
        background-color: #041360;
        color: #dae6e6;
    }
    .st-bx, .st-b9, .st-bw, .e116k4er1, .st-bb, .st-by, .e116k4er3 {
        background-color: #1a1a1d;
        border-color: #041360;  
    }
    .st-di {
        background-color: #0c1020;
        border-color: #041360;
    }
    </style>
    """
    return st.markdown(css, unsafe_allow_html=True)


# Chamada da função de login
if __name__ == '__main__':
    main()
