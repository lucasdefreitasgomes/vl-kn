from flask import Flask, render_template, request
import pandas as pd
import locale

app = Flask(__name__)

# Define a localidade para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

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
    # Carregar os dados do arquivo Excel
    df = pd.read_excel('Controle de Vale Pedágio - Riscos_0_1.xlsx', sheet_name='Conhecimentos Emitidos')

    filtros_selecionados = {}

    if request.method == 'POST':
        # Obter os valores dos filtros do formulário
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        filial = request.form['filial']

        # Salvar os filtros selecionados
        filtros_selecionados['data_inicio'] = data_inicio
        filtros_selecionados['data_fim'] = data_fim
        filtros_selecionados['filial'] = filial

        # Aplicar filtros aos dados do DataFrame
        if data_inicio and data_fim:
            df = df[(df['Dt. Emissão'] >= data_inicio) & (df['Dt. Emissão'] <= data_fim)]
        if filial:
            # Converter filial para inteiro antes de aplicar o filtro
            df = df[df['Filial Cod'] == (filial)]

    # Filiais disponíveis para seleção (incluindo todas as filiais, independentemente do filtro)
    filiais = df['Filial Cod'].unique()

    # Calcular total de pedágio pago e formatar para moeda brasileira
    total_pedagio_pago = formatar_valor(df['Pedagio'].sum())

    # Contagem de viagens por status atual
    viagens_por_status = df.drop_duplicates('file editado')['Status Atual'].value_counts()

    # Contagem de viagens por tipo de frete
    viagens_por_tipo_frete = df['Tipo Frete'].value_counts()

    # Consolidar os dados por tomador de serviço e calcular a média dos riscos
    df['Primeiro Nome'] = df['Tomador Servico'].str.split().str[0]  # Extrair primeiro nome
    df['Primeiro Nome'] = df['Primeiro Nome'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')  # Remover caracteres especiais
    risco_por_tomador = df.groupby('Primeiro Nome')['Risco'].mean().sort_values(ascending=False).map(formatar_valor)

    # Risco atual e risco reduzido
    risco_atual = formatar_valor(df['Risco'].sum())
    risco_reduzido = formatar_valor(df['Risco Reduzido'].sum())

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
    # Carregar os dados do arquivo Excel
    df = pd.read_excel('Controle de Vale Pedágio - Riscos_0_1.xlsx', sheet_name='Conhecimentos Emitidos')

    filtros_selecionados = {}

    if request.method == 'POST':
        # Obter os valores dos filtros do formulário
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        filial = request.form['filial']

        # Salvar os filtros selecionados
        filtros_selecionados['data_inicio'] = data_inicio
        filtros_selecionados['data_fim'] = data_fim
        filtros_selecionados['filial'] = filial

        # Aplicar filtros aos dados do DataFrame
        if data_inicio and data_fim:
            df = df[(df['Dt. Emissão'] >= data_inicio) & (df['Dt. Emissão'] <= data_fim)]
        if filial:
            # Converter filial para inteiro antes de aplicar o filtro
            df = df[df['Filial Cod'] == (filial)]

    # Contagem de viagens por status atual
    viagens_por_status = df.drop_duplicates('file editado')['Status Atual'].value_counts()

    # Filiais disponíveis para seleção (incluindo todas as filiais, independentemente do filtro)
    filiais = df['Filial Cod'].unique()

    # Contagem de viagens por status atual e emissor
    # Converter todos os nomes de usuário para minúsculas antes de agrupar
    df['Usuário Emissor'] = df['Usuário Emissor'].str.lower()
    viagens_por_status_e_emissor = df.drop_duplicates(['file editado', 'Usuário Emissor']) \
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
    # Carregar os dados do arquivo Excel
    df = pd.read_excel('Controle de Vale Pedágio - Riscos_0_1.xlsx', sheet_name='Conhecimentos Emitidos')

    # Obter os valores dos filtros do formulário
    data_inicio = request.form['data_inicio']
    data_fim = request.form['data_fim']
    filial = request.form['filial']

    # Aplicar filtros aos dados do DataFrame
    if data_inicio and data_fim:
        df = df[(df['Dt. Emissão'] >= data_inicio) & (df['Dt. Emissão'] <= data_fim)]
    if filial:
        # Converter filial para inteiro antes de aplicar o filtro
        df = df[df['Filial Cod'] == (filial)]

    # Retornar os dados filtrados em formato JSON
    return df.to_json(orient='records')

if __name__ == '__main__':
    app.run(debug=True)
