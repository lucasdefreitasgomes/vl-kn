from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import locale

app = Flask(__name__)

# Define a localidade para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Carregar os dados do arquivo Excel uma vez
df = pd.read_excel('Controle de Vale Pedágio - Riscos_0_1.xlsx', sheet_name='Conhecimentos Emitidos')

# Função para formatar os valores
def formatar_valor(valor):
    if isinstance(valor, str):
        # Se o valor já for uma string, retorna sem modificação
        return valor
    else:
        # Converte o valor para string e substitui os separadores de milhares e decimais
        valor_formatado = f'{valor:,.2f}'
        valor_formatado = valor_formatado.replace('.', '|').replace(',', '.').replace('|', ',')
        # Adiciona o símbolo da moeda
        return f'R$ {valor_formatado}'

# Rota para a página inicial do dashboard
@app.route('/', methods=['GET', 'POST'])
def index():
    global df  # Acesso ao DataFrame global

    # Se a solicitação for POST, processar os filtros e retornar os dados filtrados
    if request.method == 'POST':
        # Obter os valores dos filtros do formulário
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        filial = request.form['filial']

        # Salvar os filtros selecionados
        filtros_selecionados = {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'filial': filial
        }

        # Aplicar filtros aos dados do DataFrame
        df_filtrado = df.copy()  # Copiar o DataFrame para preservar os dados originais
        if data_inicio and data_fim:
            df_filtrado = df_filtrado[(df_filtrado['Dt. Emissão'] >= data_inicio) & (df_filtrado['Dt. Emissão'] <= data_fim)]
        if filial:
            # Converter filial para inteiro antes de aplicar o filtro
            df_filtrado = df_filtrado[df_filtrado['Filial Cod'] == (filial)]
    else:
        # Se a solicitação for GET (primeira carga da página ou atualização), limpar os filtros e mostrar todos os dados
        df_filtrado = df.copy()
        filtros_selecionados = {
            'data_inicio': '',
            'data_fim': '',
            'filial': ''
        }

    # Calcular total de pedágio pago e formatar para moeda brasileira
    total_pedagio_pago = formatar_valor(df_filtrado['Pedagio'].sum())

    # Filiais disponíveis para seleção (incluindo todas as filiais, independentemente do filtro)
    filiais = df['Filial Cod'].unique()

    # Contagem de viagens por status atual
    viagens_por_status = df_filtrado.drop_duplicates('file editado')['Status Atual'].value_counts()

    # Contagem de viagens por tipo de frete
    viagens_por_tipo_frete = df['Tipo Frete'].value_counts()

    # Consolidar os dados por tomador de serviço e calcular a média dos riscos
    df_filtrado['Primeiro Nome'] = df_filtrado['Tomador Servico'].str.split().str[0]  # Extrair primeiro nome
    df_filtrado['Primeiro Nome'] = df_filtrado['Primeiro Nome'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')  # Remover caracteres especiais
    risco_por_tomador = df_filtrado.groupby('Primeiro Nome')['Risco'].sum().sort_values(ascending=False).map(formatar_valor)

    # Risco atual e risco reduzido
    risco_atual = formatar_valor(df_filtrado['Risco'].sum())
    risco_reduzido = formatar_valor(df_filtrado['Risco Reduzido'].sum())

    # Renderizar o template com os dados
    return render_template('index.html', total_pedagio_pago=total_pedagio_pago,
                           viagens_por_status=viagens_por_status,
                           viagens_por_tipo_frete=viagens_por_tipo_frete,
                           risco_por_tomador=risco_por_tomador,
                           risco_atual=risco_atual,
                           risco_reduzido=risco_reduzido,
                           filiais=filiais,
                           filtros=filtros_selecionados)

# Rota para a página de quantidade de viagens por status
@app.route('/viagens_por_status', methods=['GET', 'POST'])
def viagens_por_status():
    global df  # Acesso ao DataFrame global

    # Se a solicitação for POST, processar os filtros e retornar os dados filtrados
    if request.method == 'POST':
        # Obter os valores dos filtros do formulário
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        filial = request.form['filial']

        # Salvar os filtros selecionados
        filtros_selecionados = {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'filial': filial
        }

        # Aplicar filtros aos dados do DataFrame
        df_filtrado = df.copy()  # Copiar o DataFrame para preservar os dados originais
        if data_inicio and data_fim:
            df_filtrado = df_filtrado[(df_filtrado['Dt. Emissão'] >= data_inicio) & (df_filtrado['Dt. Emissão'] <= data_fim)]
        if filial:
            # Converter filial para inteiro antes de aplicar o filtro
            df_filtrado = df_filtrado[df_filtrado['Filial Cod'] == (filial)]
    else:
        # Se a solicitação for GET (primeira carga da página ou atualização), limpar os filtros e mostrar todos os dados
        df_filtrado = df.copy()
        filtros_selecionados = {
            'data_inicio': '',
            'data_fim': '',
            'filial': ''
        }

    # Contagem de viagens por status atual
    viagens_por_status = df_filtrado.drop_duplicates('file editado')['Status Atual'].value_counts()

    # Filiais disponíveis para seleção (incluindo todas as filiais, independentemente do filtro)
    filiais = df['Filial Cod'].unique()

    # Contagem de viagens por status atual e emissor
    # Converter todos os nomes de usuário para minúsculas antes de agrupar
    df_filtrado['Usuário Emissor'] = df_filtrado['Usuário Emissor'].str.lower()
    viagens_por_status_e_emissor = df_filtrado.drop_duplicates(['file editado', 'Usuário Emissor']) \
                                     .groupby(['Usuário Emissor', 'Status Atual']).size().unstack(fill_value=0)

    # Converter os dados para HTML
    viagens_por_status_e_emissor_html = viagens_por_status_e_emissor.to_html(classes='data-table custom-table', header='true')

    # Renderizar o template com os dados
    return render_template('viagens_por_status.html', viagens_por_status=viagens_por_status,
                           viagens_por_status_e_emissor_html=viagens_por_status_e_emissor_html,
                           filiais=filiais, filtros=filtros_selecionados)


# Rota para a tabela de dados filtrados
@app.route('/tabela_filtrada', methods=['POST'])
def tabela_filtrada():
    global df  # Acesso ao DataFrame global

    # Obter os valores dos filtros do formulário
    data_inicio = request.form['data_inicio']
    data_fim = request.form['data_fim']
    filial = request.form['filial']

    # Aplicar filtros aos dados do DataFrame
    df_filtrado = df.copy()  # Copiar o DataFrame para preservar os dados originais
    if data_inicio and data_fim:
        df_filtrado = df_filtrado[(df_filtrado['Dt. Emissão'] >= data_inicio) & (df_filtrado['Dt. Emissão'] <= data_fim)]
    if filial:
        # Converter filial para inteiro antes de aplicar o filtro
        df_filtrado = df_filtrado[df_filtrado['Filial Cod'] == (filial)]

    # Retornar os dados filtrados em formato JSON
    return df_filtrado.to_json(orient='records')

if __name__ == '__main__':
    app.run(debug=True)
