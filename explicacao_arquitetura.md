# Explicação da Arquitetura e Estrutura do Código: `streamlit_agentes_ia_v5.py`

### Visão Geral

Este é um aplicativo web construído com **Streamlit**, que serve como interface para um sistema de **Agentes de Inteligência Artificial**. O objetivo do sistema é automatizar a criação de posts para o Instagram sobre um determinado tópico.

A arquitetura é baseada em um padrão de **pipeline (ou esteira de produção)**, onde vários agentes especializados trabalham em sequência. Cada agente realiza uma tarefa específica, e o resultado do trabalho de um agente é passado como entrada para o próximo.

---

### Tecnologias Principais

*   **Streamlit:** Usado para criar a interface do usuário (UI) de forma rápida. É responsável por todos os elementos visuais, como textos, botões, abas e a barra lateral.
*   **Google Generative AI (Gemini):** É o cérebro por trás dos agentes. O modelo de linguagem (como `gemini-2.0-flash`) é usado para processar as instruções e gerar as respostas.
*   **Google Agent Development Kit (ADK):** A biblioteca `google.adk` é um framework que facilita a criação, execução e gerenciamento dos agentes. Ela abstrai a complexidade de interagir com o modelo de IA.
*   **Asyncio:** A programação assíncrona é usada para gerenciar as chamadas aos agentes, permitindo que o aplicativo permaneça responsivo enquanto espera as respostas da API do Google.

---

### Estrutura do Código e Componentes

O código pode ser dividido em 5 partes principais:

#### 1. Configuração e Interface (Função `main`)

*   **Responsabilidade:** Montar a página web, gerenciar a entrada do usuário e exibir os resultados.
*   **Como funciona:**
    *   `st.set_page_config()`: Define o título, ícone e layout da página.
    *   `st.markdown(...)`: Aplica CSS customizado para estilizar a aparência.
    *   A função `main()` organiza a interface:
        *   **Barra Lateral (`st.sidebar`):** Contém a logo, a configuração da API Key, uma explicação de como o sistema funciona e dicas de uso.
        *   **Área Principal:** Exibe o título, o campo de texto (`st.text_input`) para o usuário digitar o tópico e o botão (`st.button`) para iniciar o processo.
    *   **Gerenciamento de Estado (`st.session_state`):** O Streamlit recarrega o script a cada interação. `st.session_state` é usado para "lembrar" informações importantes, como se a API já foi configurada (`api_configured`) e os resultados gerados (`resultados`), para que não se percam.

#### 2. Configuração da API (Função `setup_api`)

*   **Responsabilidade:** Garantir que o aplicativo tenha uma chave de API válida para se comunicar com os serviços do Google Gemini.
*   **Como funciona:**
    *   Verifica no `st.session_state` se a API já foi configurada para não pedir a chave novamente.
    *   Pede ao usuário para inserir a `GOOGLE_API_KEY` na barra lateral através de um campo de senha (`st.text_input(type="password")`).
    *   Valida a chave tentando fazer uma chamada simples à API (`client.models.list()`). Se falhar, exibe um erro. Se funcionar, armazena o cliente da API e o status de configuração no `st.session_state`.

#### 3. Os Agentes (Funções `agente_*`)

Esta é a essência do sistema. Cada agente é uma função `async` que define um "trabalhador" especializado.

*   **`agente_buscador`:**
    *   **Função:** Pesquisador.
    *   **Instrução:** Usa a ferramenta de busca do Google (`google_search`) para encontrar as notícias e lançamentos mais recentes e relevantes sobre o tópico.
*   **`agente_planejador`:**
    *   **Função:** Estrategista de Conteúdo.
    *   **Instrução:** Recebe os lançamentos do buscador, pesquisa mais a fundo, escolhe o tema mais promissor e cria um plano de post, definindo os pontos a serem abordados.
*   **`agente_gerador_prompt_imagem`:**
    *   **Função:** Diretor de Arte.
    *   **Instrução:** Com base no plano do post, cria uma descrição textual detalhada para uma imagem que acompanharia o post.
*   **`agente_redator`:**
    *   **Função:** Redator (Copywriter).
    *   **Instrução:** Pega o plano do post e escreve o texto final, com linguagem engajadora e hashtags, no estilo da Alura.
*   **`agente_revisor`:**
    *   **Função:** Editor / Revisor de Qualidade.
    *   **Instrução:** Analisa o rascunho do redator, verifica clareza, tom de voz e erros. Se necessário, reescreve o post para garantir a qualidade final.

#### 4. Orquestração dos Agentes (Função `processar_agentes`)

*   **Responsabilidade:** Gerenciar o fluxo de trabalho, chamando cada agente na ordem correta e passando os dados de um para o outro.
*   **Como funciona:**
    *   É uma função `async` que define a sequência: `buscador` -> `planejador` -> `gerador_prompt_imagem` -> `redator` -> `revisor`.
    *   Usa `st.progress()` e `st.empty()` para mostrar uma barra de progresso e mensagens de status na interface, informando ao usuário qual agente está trabalhando no momento.
    *   Armazena o resultado de cada agente em um dicionário `resultados`.
    *   Possui um bloco `try...except` para capturar e exibir erros que possam ocorrer durante o processo.

#### 5. Comunicação com Agentes (Função `call_agent`)

*   **Responsabilidade:** É uma função auxiliar que lida com a comunicação de baixo nível com qualquer agente criado pelo ADK.
*   **Como funciona:**
    *   Recebe um objeto `Agent` e a mensagem de entrada.
    *   Usa o `Runner` do ADK para executar o agente de forma assíncrona.
    *   Captura a resposta final do agente e a retorna como uma string.

---

### Fluxo de Execução (Como tudo se conecta)

1.  O usuário abre o aplicativo no navegador.
2.  A função `main()` é executada, renderizando a interface.
3.  O usuário insere sua API Key na barra lateral. A função `setup_api()` valida e armazena a chave.
4.  O usuário digita um tópico (ex: "carros elétricos") e clica no botão "🚀 Gerar Post".
5.  Isso aciona a parte `if processar and topico:` dentro da função `main()`.
6.  A função `main()` chama `asyncio.run(processar_agentes(topico))`.
7.  `processar_agentes` assume o controle:
    *   Chama `agente_buscador`.
    *   Pega o resultado e chama `agente_planejador`.
    *   Pega o resultado e chama `agente_gerador_prompt_imagem`.
    *   Pega o resultado e chama `agente_redator`.
    *   Pega o resultado e chama `agente_revisor`.
    *   Durante cada etapa, a interface é atualizada com o progresso.
8.  Ao final, `processar_agentes` retorna um dicionário com todos os resultados (notícias, plano, rascunho, post final, etc.).
9.  Esse dicionário é salvo em `st.session_state.resultados`.
10. O Streamlit executa um `st.rerun()`, recarregando a página. Agora, como `resultados` existe no `session_state`, a interface exibe os resultados organizados em abas (`st.tabs`).