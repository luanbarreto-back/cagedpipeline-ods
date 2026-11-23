Dinâmica do Emprego Formal e Rotatividade Setorial na Bahia

Uma análise interseccional por gênero, raça/cor e setor econômico — Novo CAGED, 2025

Pipeline de engenharia e análise de dados em nuvem desenvolvido para investigar a dinâmica do emprego formal na Bahia, considerando diferenças por sexo, raça/cor e setor econômico. O projeto utiliza microdados públicos do Novo CAGED, realiza o processamento por meio de um pipeline ETL em Python, armazena os dados em PostgreSQL gerenciado na Aiven e disponibiliza os indicadores em um dashboard interativo desenvolvido com Streamlit.

O trabalho dialoga com a ODS 5 (Igualdade de Gênero) e com a ODS 18 (Igualdade Étnico-Racial), conforme o recorte temático adotado pelo projeto.

Informações do projeto
Item	Informação
Disciplina: Cloud Compunting
Tema: Dinâmica de Emprego Formal e Turnover Setorial
Recorte geográfico	Bahia (código IBGE 29)
Período analisado	Janeiro a dezembro de 2025
Integrantes:	Luan Barreto e Robert Santos
Dashboard online	https://luanbarreto-back-cagedpipeline-ods-appapp-qxqo7u.streamlit.app/
Repositório	https://github.com/luanbarreto-back/cagedpipeline-ods
1. Problema e objetivo

O projeto busca responder à seguinte questão:

Como as admissões e os desligamentos do emprego formal na Bahia se distribuem quando analisados conjuntamente por sexo, raça/cor e setor econômico?

Para responder a essa pergunta, são utilizados os microdados não identificados do Novo CAGED. Os registros são processados e agregados por competência, setor econômico, sexo, raça/cor, faixa etária e grau de instrução. Em seguida, os dados são armazenados em um banco PostgreSQL na nuvem e apresentados em um dashboard com filtros dinâmicos.

Recorte da análise
Dimensão	Definição
Unidade da Federação	Bahia, código IBGE 29
Período	Janeiro a dezembro de 2025
Granularidade	Competência, setor, sexo, raça/cor, faixa etária e escolaridade
Fonte	Microdados de movimentações do Novo CAGED

A agregação é realizada antes da carga no banco para reduzir o volume armazenado e adequar o projeto ao limite de 1 GB do plano gratuito da Aiven.

Limitação da base pública

Os microdados utilizados são não identificados: não apresentam um identificador individual do trabalhador nem informações suficientes para calcular o tempo de permanência de cada pessoa no emprego. Por esse motivo, o projeto não calcula permanência individual. A análise utiliza indicadores agregados, como a razão entre desligamentos e admissões e o saldo de movimentações.

2. Arquitetura da solução
┌────────────────────────────┐
│ Portal PDET/MTE (FTP)      │
│ Novo CAGED (.7z)           │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ ETL em Python              │
│ pandas + SQLAlchemy        │
│ filtro UF 29, tratamento   │
│ e agregação                │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐               ┌────────────────────────────┐
│ Aiven for PostgreSQL       │◄─ provisiona ─│ Terraform                  │
│ Free Tier (1 GB)           │               │ provider aiven/aiven       │
└────────────────────────────┘               └────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ Dashboard Streamlit        │
│ Streamlit Community Cloud  │
└────────────────────────────┘

Fluxo em texto: Portal PDET/MTE (Novo CAGED) → ETL em Python → Aiven for PostgreSQL → Dashboard Streamlit. O Terraform provisiona a infraestrutura do banco de dados na Aiven.

Tecnologias utilizadas
Camada	Tecnologia	Finalidade
Fonte de dados	Novo CAGED (PDET/MTE)	Fornecimento dos microdados de movimentações
Linguagem	Python	Desenvolvimento do pipeline ETL
Processamento	pandas e py7zr	Leitura, extração, tratamento e agregação
Conexão e persistência	SQLAlchemy e psycopg2	Comunicação com o PostgreSQL
Banco de dados	Aiven for PostgreSQL (plano free-1-1gb)	Armazenamento dos dados processados
Infraestrutura como código	Terraform (provider aiven/aiven)	Provisionamento do serviço de banco
Dashboard	Streamlit	Interface interativa
Gráficos	Plotly	Visualização dos indicadores
Versionamento	Git e GitHub	Controle de versão e hospedagem do código

Observação: Kafka, OpenSearch e MySQL, opcionais no enunciado, não fazem parte da implementação. A solução utiliza PostgreSQL, Terraform e Streamlit como componentes centrais.

3. Estrutura do repositório
cagedpipeline-ods/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── etl/
│   ├── baixar.py
│   ├── inspecionar.py
│   ├── baixar_layout.py
│   ├── criar_dimensoes.py
│   ├── carregar.py
│   ├── pipeline_meses.py
│   └── testar_conexao.py
├── app/
│   └── app.py
├── docs/
├── requirements.txt
└── README.md
Responsabilidade dos principais arquivos
Arquivo	Responsabilidade
terraform/main.tf	Configuração do provider e dos recursos da Aiven
terraform/variables.tf	Declaração das variáveis utilizadas pelo Terraform
terraform/outputs.tf	Exposição dos dados de conexão do serviço
etl/baixar.py	Download de um arquivo mensal do Novo CAGED
etl/inspecionar.py	Extração e inspeção das colunas do arquivo
etl/baixar_layout.py	Download do layout oficial da base
etl/criar_dimensoes.py	Criação das tabelas de dimensões
etl/carregar.py	Tratamento, agregação e carga dos dados
etl/pipeline_meses.py	Automação do processamento de vários meses
etl/testar_conexao.py	Teste de conexão com o PostgreSQL
app/app.py	Aplicação do dashboard Streamlit
4. Modelagem do banco de dados

A estrutura utiliza tabelas fato para armazenar as movimentações agregadas e tabelas dimensão para traduzir os códigos dos microdados em descrições compreensíveis.

Tabelas fato

fato_movimentacao: dados agregados por competência, seção econômica, sexo, raça/cor, faixa etária e grau de instrução.

Coluna	Tipo	Descrição
competencia	texto	Mês da movimentação no formato AAAAMM
secao	texto	Seção da CNAE 2.0
sexo	texto	Código do sexo
raca_cor	texto	Código de raça/cor
faixa_etaria	texto	Faixa etária do trabalhador
grau_instrucao	texto	Código do grau de instrução
admissoes	inteiro	Quantidade de admissões
desligamentos	inteiro	Quantidade de desligamentos
sal_adm_soma	decimal	Soma dos salários declarados nas admissões (R$)
sal_desl_soma	decimal	Soma dos salários declarados nos desligamentos (R$)
saldo	inteiro	Diferença entre admissões e desligamentos

fato_tipo_mov: quantidade de movimentações por competência, sexo, raça/cor e tipo de movimentação.

Coluna	Tipo	Descrição
competencia	texto	Mês da movimentação no formato AAAAMM
sexo	texto	Código do sexo
raca_cor	texto	Código de raça/cor
tipo_mov	texto	Código do tipo de movimentação
qtd	inteiro	Quantidade de movimentações
Tabelas dimensão

As dimensões são geradas a partir do layout oficial do Ministério do Trabalho e Emprego.

Tabela	Conteúdo
dim_sexo	Código e descrição do sexo
dim_raca_cor	Código e descrição de raça/cor
dim_secao	Código e descrição da seção econômica
dim_grau_instrucao	Código e descrição do grau de instrução
dim_tipo_mov	Código, descrição, natureza (admissão, desligamento ou outro) e indicador de transferência
5. Dicionário de variáveis

Fonte: Layout dos Microdados Não Identificados do Novo CAGED, Base de Movimentações, disponibilizado pelo PDET/MTE. O arquivo mensal CAGEDMOV tem as 28 colunas abaixo. As variáveis competênciaexc e indicadordeexclusão constam no layout, mas pertencem ao arquivo de exclusões (CAGEDEXC) e não foram usadas.

Variável original	Descrição	Formato	Utilização no projeto
competênciamov	Competência da movimentação	AAAAMM	Coluna competencia
região	Região geográfica (IBGE)	99	Não usada
uf	Unidade da federação (IBGE)	99	Filtro da Bahia (código 29); não armazenada
município	Código do município	999999	Não usada
seção	Seção da CNAE 2.0	letra	Coluna secao
subclasse	Subclasse da CNAE 2.0	9999999	Não usada
saldomovimentação	Saldo (+1 admissão, -1 desligamento)	99	Define admissoes e desligamentos
cbo2002ocupação	Ocupação (CBO 2002)	999999	Não usada
categoria	Categoria do trabalhador	999	Não usada
graudeinstrução	Grau de instrução	99	Coluna grau_instrucao
idade	Idade do trabalhador	999	Cálculo da faixa_etaria
horascontratuais	Horas contratuais semanais	99	Não usada
raçacor	Raça ou cor	9	Coluna raca_cor
sexo	Sexo do trabalhador	9	Coluna sexo
tipoempregador	Tipo de empregador	9	Não usada
tipoestabelecimento	Tipo de estabelecimento	9	Não usada
tipomovimentação	Tipo de movimentação	99	Coluna tipo_mov; exclusão dos códigos 70 e 80
tipodedeficiência	Tipo de deficiência	9	Não usada
indtrabintermitente	Indicador de trabalhador intermitente	9	Não usada
indtrabparcial	Indicador de trabalhador parcial	9	Não usada
salário	Salário mensal declarado (vírgula decimal)	999999999,99	Soma dos salários por tipo de movimentação
tamestabjan	Faixa de emprego do estabelecimento em janeiro	99	Não usada
indicadoraprendiz	Indicador de aprendiz	9	Não usada
origemdainformação	Origem da informação	9	Não usada
competênciadec	Competência da declaração	AAAAMM	Não usada
indicadordeforadoprazo	Informação declarada fora do prazo	9	Não usada
unidadesaláriocódigo	Unidade de pagamento da parte fixa	99	Não usada
valorsaláriofixo	Salário base (parte fixa)	999999999,99	Não usada
Códigos das variáveis principais

Sexo: 1 = Homem, 3 = Mulher, 9 = Não identificado.

Raça/cor: 1 = Branca, 2 = Preta, 3 = Parda, 4 = Amarela, 5 = Indígena, 6 = Não informada, 9 = Não identificado.

Faixas etárias utilizadas: menor de 18 anos, 18 a 24, 25 a 29, 30 a 39, 40 a 49, 50 a 59, 60 anos ou mais e não identificada.

Grau de instrução: 1 = Analfabeto, 2 = Até 5ª incompleto, 3 = 5ª completo fundamental, 4 = 6ª a 9ª fundamental, 5 = Fundamental completo, 6 = Médio incompleto, 7 = Médio completo, 8 = Superior incompleto, 9 = Superior completo, 10 = Mestrado, 11 = Doutorado, 80 = Pós-graduação completa, 99 = Não identificado.

Tipo de movimentação:

Natureza	Códigos
Admissão	10 (primeiro emprego), 20 (reemprego), 25 (prazo determinado), 35 (reintegração), 97 (tipo ignorado)
Desligamento	31 (sem justa causa), 32 (com justa causa), 33 (culpa recíproca), 40 (a pedido), 43 (término de contrato a prazo), 45 (término de contrato), 50 (aposentadoria), 60 (morte), 90 (acordo entre as partes), 98 (tipo ignorado)
Transferência (excluída da análise)	70 (admissão por transferência), 80 (desligamento por transferência)
Outro	99 (não identificado)

Seção econômica: a classificação segue as seções da CNAE 2.0, identificadas pelas letras de A a U e pela categoria Z para registros não identificados.

6. Decisões metodológicas e tratamento dos dados
Admissões e desligamentos: identificados a partir do campo saldomovimentação. O valor +1 representa admissão e -1 representa desligamento.
Transferências: os tipos de movimentação 70 e 80 são excluídos da análise, pois representam transferências entre estabelecimentos e não entradas ou saídas reais do mercado de trabalho.
Razão desligamentos/admissões: calculada pela divisão da quantidade de desligamentos pela quantidade de admissões. Valores acima de 1 indicam que, no grupo analisado, ocorreram mais desligamentos do que admissões no período.
Salário médio por movimentação: soma dos salários declarados dividida pela quantidade de movimentações correspondente. Não representa a remuneração média de trabalhadores únicos.
Faixas etárias: criadas a partir da idade informada no microdado.
Tratamento de dados: valores não numéricos em saldo, idade e salário são tratados como nulos; registros sem saldo são descartados; valores monetários são convertidos para formato numérico.
Processamento em blocos: os arquivos são processados em chunks de 500 mil linhas, reduzindo o consumo de memória.
Agregação antes da carga: os dados são consolidados antes de serem enviados ao PostgreSQL, reduzindo o espaço necessário para armazenamento.
Carga idempotente: a competência é removida antes de uma nova inserção, permitindo repetir a carga sem duplicar os registros daquela competência.
Interpretação do indicador

A razão entre desligamentos e admissões é utilizada como indicador descritivo da dinâmica das movimentações. Ela não corresponde à taxa clássica de rotatividade, pois não utiliza o estoque médio de trabalhadores como denominador.

7. Indicadores do dashboard

O dashboard permite explorar os dados por meio de filtros de mês, sexo, raça/cor e setor econômico. Os indicadores são:

Desligamentos por admissão, com recortes por sexo e raça/cor.
Saldo de empregos por setor econômico e sexo.
Salário médio declarado nas admissões e nos desligamentos, por sexo e raça/cor.
Evolução mensal de admissões e desligamentos.
Tipos de desligamento por sexo.
Totais de admissões, desligamentos e saldo de movimentações.

Os resultados devem ser interpretados considerando o recorte temporal, geográfico e as limitações dos microdados.

8. Como executar o projeto
Pré-requisitos
Python 3.10 ou superior
Git
Terraform
Conta na Aiven, com um token pessoal (User information > Tokens > Generate token)
Conta no GitHub
Conta no Streamlit Community Cloud

Os comandos a seguir utilizam o Windows PowerShell.

8.1. Clonar o repositório e preparar o ambiente
powershell
git clone https://github.com/luanbarreto-back/cagedpipeline-ods.git
cd cagedpipeline-ods

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
8.2. Provisionar o banco com Terraform

Configure as variáveis de ambiente no PowerShell. Substitua os valores de exemplo pelos dados da sua conta Aiven. Elas valem apenas para o terminal aberto.

powershell
$env:TF_VAR_aiven_api_token = "SEU_TOKEN_DA_AIVEN"
$env:TF_VAR_project_name = "NOME_DO_PROJETO_NA_AIVEN"

cd terraform

terraform init
terraform plan
terraform apply

cd ..

O Terraform provisiona o serviço pg-caged-ods (PostgreSQL, plano gratuito free-1-1gb) conforme os arquivos da pasta terraform.

Variável	Padrão	Descrição
aiven_api_token	obrigatória (sensitive)	Token pessoal da Aiven
project_name	obrigatória	Nome do projeto no console da Aiven
cloud_name	do-sfo	Nuvem e região do plano gratuito
plan	free-1-1gb	Plano gratuito do PostgreSQL

Atenção: o plano gratuito permite apenas um serviço PostgreSQL por organização; se já existir outro, remova-o antes. Verifique também as condições atuais do plano na Aiven e não compartilhe seu token.

8.3. Configurar e testar a conexão

A URI de conexão contém credenciais e não deve ser exibida nem publicada no repositório.

powershell
$env:DATABASE_URL = terraform -chdir=terraform output -raw service_uri

python etl/testar_conexao.py
8.4. Preparar e carregar os dados

1. Criar as dimensões

powershell
python etl/baixar_layout.py
python etl/criar_dimensoes.py

2. Processar janeiro de 2025

powershell
python etl/baixar.py
python etl/inspecionar.py
python etl/carregar.py

3. Processar os demais meses

powershell
python etl/pipeline_meses.py

O pipeline automatiza o download e a carga de fevereiro a dezembro de 2025 e apaga os arquivos brutos depois de cada carga. Os arquivos brutos ficam localmente em data/raw/ e não devem ser enviados ao GitHub. A fonte é o FTP do PDET/MTE (ftp.mtps.gov.br, pasta /pdet/microdados/NOVO CAGED/), cujos nomes de arquivo usam codificação Latin-1.

8.5. Executar o dashboard localmente
powershell
streamlit run app/app.py

A aplicação fica disponível em http://localhost:8501. A primeira abertura pode levar alguns segundos, e o resultado fica em cache por 1 hora.

8.6. Publicar no Streamlit Community Cloud
Acesse o Streamlit Community Cloud e entre com sua conta GitHub.
Crie uma nova aplicação.
Selecione o repositório cagedpipeline-ods.
Escolha a branch main.
Informe app/app.py como arquivo principal.
Em Advanced settings > Secrets, configure a variável de conexão:
toml
DATABASE_URL = "SUA_URI_DE_CONEXAO"
Confirme que o requirements.txt lista streamlit, plotly, pandas, sqlalchemy e psycopg2-binary, salve as configurações e faça o deploy.

A URI deve ser inserida nos Secrets da aplicação, nunca diretamente no código-fonte.

9. Segurança
Tokens e senhas não são versionados no GitHub.
O token da Aiven é fornecido por variável de ambiente ao Terraform, e a variável aiven_api_token é declarada como sensível.
A URI de conexão do dashboard permanece nos Secrets do Streamlit.
Arquivos .env, ambientes virtuais, dados brutos e arquivos de estado do Terraform ficam fora do controle de versão (.gitignore).
O arquivo terraform.tfstate pode conter informações sensíveis e não deve ser publicado.
Tokens expostos devem ser revogados e substituídos.
10. Limitações do projeto
Permanência individual: não é possível calcular o tempo de permanência de cada trabalhador, pois a base não disponibiliza identificador individual nem histórico individual de vínculos.
Recorte geográfico: a análise considera somente a Bahia.
Recorte temporal: a análise considera janeiro a dezembro de 2025.
Dados não identificados: registros sem informação de sexo ou raça/cor limitam alguns cruzamentos.
Indicador de movimentação: a razão desligamentos/admissões não deve ser interpretada como taxa clássica de rotatividade.
Infraestrutura gratuita: a disponibilidade, os limites e as condições dos serviços dependem dos planos gratuitos vigentes. O banco pode ficar desligado por inatividade e precisa ser ligado no console da Aiven, e o aplicativo do Streamlit pode hibernar e levar alguns instantes para reativar.
11. Fonte dos dados
Microdados do Novo CAGED, Base de Movimentações, não identificados: Programa de Disseminação das Estatísticas do Trabalho (PDET), Ministério do Trabalho e Emprego. https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged
Layout oficial: Layout Não-identificado Novo Caged Movimentação.xlsx, disponibilizado pelo PDET/MTE junto aos arquivos da base.
12. Acesse o projeto
Dashboard online: https://luanbarreto-back-cagedpipeline-ods-appapp-qxqo7u.streamlit.app/
Repositório GitHub: https://github.com/luanbarreto-back/cagedpipeline-ods
13. Autoria

Projeto acadêmico desenvolvido por Luan Barreto e Robert Santos, na disciplina de Computação em Nuvem / Engenharia de Software.

GitHub: https://github.com/luanbarreto-back
Repositório do projeto: https://github.com/luanbarreto-back/cagedpipeline-ods
