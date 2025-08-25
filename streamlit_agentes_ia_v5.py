# -*- coding: utf-8 -*-
"""
Sistema de Agentes IA para Criação de Posts no Instagram
Interface Streamlit

Para executar: streamlit run nome_do_arquivo.py
"""

import os
import asyncio
import textwrap
import warnings
from datetime import date
import streamlit as st
from google import genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
import time
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import base64
from typing import Optional

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configurações
warnings.filterwarnings("ignore")
MODEL_ID = "gemini-2.0-flash"

# Configuração da página Streamlit
st.set_page_config(
    page_title="🤖 Sistema de Agentes IA - Posts Instagram",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def setup_api():
    """Configura a API Key do Google Gemini"""
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False

    if not st.session_state.api_configured:
        api_key = ""
        if not api_key:
            with st.sidebar:
                api_key = st.text_input(
                    "Digite sua API Key do Google Gemini:",
                    type="password",
                    help="Obtenha sua chave em: https://makersuite.google.com/app/apikey"
                )

        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            try:
                client = genai.Client()
                client.models.list()

                st.session_state.client = client
                st.session_state.api_configured = True
                st.session_state.session_service = InMemorySessionService()
                return client
            except Exception as e:

                st.sidebar.error(
                    f"❌ Erro ao validar a API\n\n ⚠️ Verifique se sua API Key do Google Gemini está correta")
                st.session_state.api_configured = False
                return None
    else:
        return st.session_state.get('client')


async def call_agent(agent: Agent, message_text: str) -> str:
    """Função auxiliar para chamada dos agentes"""
    session_service = st.session_state.session_service

    session = await session_service.create_session(
        app_name=agent.name,
        user_id="user1",
        session_id="session1"
    )

    runner = Runner(
        agent=agent,
        app_name=agent.name,
        session_service=session_service
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=message_text)]
    )
    final_response = ""
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=content
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text is not None:
                    final_response += part.text
                    final_response += "\n"
    return final_response


async def agente_buscador(topico, data_de_hoje, progress_callback=None):
    """Agente 1: Buscador de Notícias"""
    if progress_callback:
        progress_callback("🔍 Buscando notícias relevantes...")

    buscador = Agent(
        name="agente_buscador",
        model="gemini-2.0-flash",
        instruction="""
        Você é um assistente de pesquisa. A sua tarefa é usar a ferramenta de busca do Google (google_search)
        para recuperar as últimas notícias de lançamento muito relevantes sobre o tópico abaixo.
        Foque em no máximo 5 lançamentos relevantes, com base na quantidade e entusiasmo das notícias sobre ele.
        Se um tema tiver poucas notícias ou pouca relevância, é possível que ele não tão seja relevante assim e
        pode ser substituído por outro que tenha mais relevância .
        Esses lançamento relevantes devem ser atuais, de no máximo um mês antes da data de hoje
        """,
        description="Agente que busca notícias no Google sobre o assunto indicado",
        tools=[google_search],
    )

    entrada_do_agente_buscador = f"Tópico: {topico}\nData de hoje: {data_de_hoje}"
    lancamentos = await call_agent(buscador, entrada_do_agente_buscador)
    return lancamentos


async def agente_planejador(topico, lancamentos_buscados, progress_callback=None):
    """Agente 2: Planejador de posts"""
    if progress_callback:
        progress_callback("📋 Analisando e planejando o melhor conteúdo...")

    planejador = Agent(
        name="agente_planejador",
        model="gemini-2.0-flash",
        instruction="""
        Você é um planejador de conteúdo, especialista em redes sociais. Com base na lista
        de lançamentos mais recentes e relevantes do buscador, você deve:
        usar a ferramenta de busca do Google (google_search) para criar um plano sobre
        quais são os pontos mais relevantes que poderiamos abordar em um post sobre
        cada um deles. Você também pode usar o (google_search) para encontrar mais
        informações sobre os temas e aprofundar.
        Ao final, você irá escolher o tema mais relevante entre eles com base nas suas pesquisas
        e retornar esse tema, os pontos mais relevantes, e um plano com os assuntos
        a serem abordados no post que será escrito posteriormente.
        """,
        description="Agente que planeja posts",
        tools=[google_search]
    )

    entrada_do_agente_planejador = f"Tópico:{topico}\nLançamentos buscados: {lancamentos_buscados}"
    plano_do_post = await call_agent(planejador, entrada_do_agente_planejador)
    return plano_do_post


async def agente_redator(topico, plano_de_post, progress_callback=None):
    """Agente 3: Redator do Post"""
    if progress_callback:
        progress_callback("✍️ Escrevendo o post engajador...")

    redator = Agent(
        name="agente_redator",
        model="gemini-2.0-flash",
        instruction="""
            Você é um Redator Criativo especializado em criar posts virais para redes sociais.
            Você escreve posts para a empresa Alura, a maior escola online de tecnologia do Brasil.
            Utilize o tema fornecido no plano de post e os pontos mais relevantes fornecidos e, com base nisso,
            escreva um rascunho de post para Instagram sobre o tema indicado.
            O post deve ser engajador, informativo, com linguagem simples e incluir 2 a 4 hashtags no final.
            """,
        description="Agente redator de posts engajadores para Instagram"
    )

    entrada_do_agente_redator = f"Tópico: {topico}\nPlano de post: {plano_de_post}"
    rascunho = await call_agent(redator, entrada_do_agente_redator)
    return rascunho


async def agente_revisor(topico, rascunho_gerado, progress_callback=None):
    """Agente 4: Revisor de Qualidade"""
    if progress_callback:
        progress_callback("🔍 Revisando e finalizando o post...")

    revisor = Agent(
        name="agente_revisor",
        model="gemini-2.0-flash",
        instruction="""
            Você é um Editor e Revisor de Conteúdo meticuloso, especializado em posts para redes sociais, com foco no Instagram.
            Por ter um público jovem, entre 18 e 30 anos, use um tom de escrita adequado.
            Revise o rascunho de post de Instagram abaixo sobre o tópico indicado, verificando clareza, concisão, correção e tom.
            Se o rascunho estiver bom, responda apenas 'O rascunho está ótimo e pronto para publicar!'.
            Caso haja problemas, aponte-os e sugira melhorias. 
            Reescreva o rascunho corrigindo os problemas, se houver problemas, adicionando as sugestões para melhorar a qualidade do post.
            """,
        description="Agente revisor de post para redes sociais."
    )

    entrada_do_agente_revisor = f"Tópico: {topico}\nRascunho: {rascunho_gerado}"
    texto_revisado = await call_agent(revisor, entrada_do_agente_revisor)
    return texto_revisado


async def agente_gerador_prompt_imagem(texto_revisado, progress_callback=None):
    """Agente 5: Gerador de descrição de imagem para o post"""
    if progress_callback:
        progress_callback("🎨 Gerando descrição para a imagem do post...")

    gerador_prompt_imagem = Agent(
        name="agente_gerador_prompt_imagem",
        model="gemini-2.0-flash",
        instruction="""
        Você é um assistente criativo especializado em visual para redes sociais.
        Com base no post revisado, descreva uma imagem ideal que complemente
        este post no Instagram. Sua descrição deve ser clara e inspiradora, focando
        nos elementos visuais que melhor representam o tema e os pontos chave do post.
        A descrição deve ser concisa e focada em como a imagem se relaciona com o conteúdo.
        """,
        description="Agente que gera uma descrição de imagem baseada no post revisado",
        tools=[]
    )

    entrada_do_agente_gerador_prompt_image = f"Post Revisado: {texto_revisado}"
    descricao_imagem = await call_agent(gerador_prompt_imagem, entrada_do_agente_gerador_prompt_image)
    return descricao_imagem


async def agente_gerador_de_imagem(descricao_imagem: str, api_key: str, salvar_como: Optional[str] = None, progress_callback=None) -> Optional[Image.Image]:
    """Agente 6: Gerador de imagem para o post"""
    if progress_callback:
        progress_callback("🎨 Gerando imagem com Gemini...")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=descricao_imagem,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data)))
            if salvar_como:
                image.save(salvar_como)
            return image

    return None


async def processar_agentes(topico):
    """Processa todos os agentes sequencialmente"""
    data_de_hoje = date.today().strftime("%d/%m/%Y")

    progress_bar = st.progress(0)
    status_text = st.empty()

    resultados = {}

    try:
        status_text.text("🔍 Executando Agente 1 - Buscador de Notícias...")
        progress_bar.progress(5)
        resultados['lancamentos'] = await agente_buscador(
            topico,
            data_de_hoje,
            lambda msg: status_text.text(msg),
        )

        status_text.text("📋 Executando Agente 2 - Planejador de Posts...")
        progress_bar.progress(25)
        resultados['plano'] = await agente_planejador(
            topico,
            resultados['lancamentos'],
            lambda msg: status_text.text(msg)
        )

        status_text.text("✍️ Executando Agente 3 - Redator...")
        progress_bar.progress(45)
        resultados['rascunho'] = await agente_redator(
            topico,
            resultados['plano'],
            lambda msg: status_text.text(msg)
        )

        status_text.text("🔍 Executando Agente 4 - Revisor...")
        progress_bar.progress(65)
        resultados['texto_revisado'] = await agente_revisor(
            topico,
            resultados['rascunho'],
            lambda msg: status_text.text(msg)
        )

        status_text.text(
            "🎨 Executando Agente 5 - Gerador de descrição da Imagem...")
        progress_bar.progress(85)
        resultados['descricao_imagem'] = await agente_gerador_prompt_imagem(
            resultados['texto_revisado'],
            lambda msg: status_text.text(msg)
        )

        status_text.text("🎨 Executando Agente 6 - Gerador de Imagem...")
        progress_bar.progress(95)
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            resultados['imagem_gerada'] = await agente_gerador_de_imagem(
                descricao_imagem=resultados['descricao_imagem'],
                api_key=api_key,
                salvar_como="imagem_gerada.png",
                progress_callback=lambda msg: status_text.text(msg)
            )
        else:
            st.error("API Key não encontrada para gerar a imagem.")
            resultados['imagem_gerada'] = None

        status_text.text("✅ Processo concluído com sucesso!")
        progress_bar.progress(100)
        return resultados

    except Exception as e:
        st.error(f"❌ Erro durante o processamento: {e}")
        return None


def main():
    """Interface principal do Streamlit"""

    st.markdown('<h1 class="main-header">🤖 Sistema de Agentes IA</h1>',
                unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Criação Automática de Posts para Instagram</h3>',
                unsafe_allow_html=True)

    with st.sidebar:
        col1, col2, col3 = st.columns([2, 2, 2])

        with col2:
            st.image("logo_image.png", width=135)

        st.markdown("### 🔧 Configuração")

        client = setup_api()

        if st.session_state.get('api_configured', False):
            st.success("✅ API configurada com sucesso!")

        st.markdown("---")
        st.markdown("### 📝 Como funciona?")
        st.markdown("""
        **6 Agentes trabalhando juntos:**
        1. 🔍 **Buscador** - Encontra notícias relevantes
        2. 📋 **Planejador** - Analisa e escolhe o melhor tema
        3. ✍️ **Redator** - Escreve o post engajador
        4. 🔍 **Revisor** - Revisa e finaliza o conteúdo
        5. 🎨 **Gerador de descrição da Imagem** - Gera uma descrição da imagem do post
        6. 🖼️ **Gerador de Imagem** - Cria a imagem para o post
        """,
                    )

        st.markdown("---")
        st.markdown("### 💡 Dicas")
        st.markdown("""
        - Use tópicos específicos (ex: "inteligência artificial", "smartphones 2024")
        - O processo pode levar alguns minutos
        - Todos os resultados ficam salvos na sessão
        """
                    )

    if not st.session_state.get('api_configured', False):
        st.warning(
            "⚠️ Configure sua API Key do Google Gemini na barra lateral para começar.")
        return

    st.markdown("### 🎯 Escolha o Tópico")
    col1, col2 = st.columns([3, 1])

    with col1:
        topico = st.text_input(
            "Digite o tópico sobre o qual você quer criar o post:",
            placeholder="Ex: inteligência artificial, carros elétricos, games...",
            help="Seja específico para melhores resultados!"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        processar = st.button("🚀 Gerar Post", use_container_width=True)

    if processar and topico:
        st.markdown("---")
        st.markdown("### 🔄 Processamento em Andamento")

        with st.spinner("Executando sistema de agentes..."):
            resultados = asyncio.run(processar_agentes(topico))

        if resultados:
            st.session_state.resultados = resultados
            st.session_state.topico_atual = topico

            st.success("🎉 Post gerado com sucesso!")
            st.rerun()

    elif processar and not topico:
        st.error("❌ Por favor, digite um tópico antes de processar!")

    if 'resultados' in st.session_state and st.session_state.resultados:
        st.markdown("---")
        st.markdown("### 📊 Resultados dos Agentes")

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📝 Post Final",
            "🔍 Notícias Encontradas",
            "📋 Planejamento",
            "✍️ Rascunho",
            "🔍 Revisão",
            "🎨 Descrição da Imagem",
            "🖼️ Imagem Gerada"
        ])

        resultados = st.session_state.resultados

        with tab1:
            st.markdown("### 🎯 Post Final para Instagram")
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(resultados['texto_revisado'])
            st.markdown('</div>', unsafe_allow_html=True)

            def markdown_para_texto_puro(markdown):
                texto_puro = markdown
                while "**" in texto_puro:
                    texto_puro = texto_puro.replace("**", "", 1)
                linhas = texto_puro.split("\n")
                for i in range(len(linhas)):
                    if linhas[i].strip().startswith("* "):
                        linhas[i] = "  -" + linhas[i].strip()[2:]
                return "\n".join(linhas)

            texto_puro = markdown_para_texto_puro(resultados['texto_revisado'])
            if st.button("📋 Copiar Post", key="copy_final"):
                st.markdown('<div class="success-box">',
                            unsafe_allow_html=True)
                st.text(texto_puro)
                st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown("### 🔍 Notícias e Lançamentos Encontrados")
            st.markdown(resultados['lancamentos'])

        with tab3:
            st.markdown("### 📋 Planejamento do Post")
            st.markdown(resultados['plano'])

        with tab4:
            st.markdown("### ✍️ Rascunho Inicial")
            st.markdown(resultados['rascunho'])

        with tab5:
            st.markdown("### 🔍 Análise da Revisão")
            st.markdown(resultados['texto_revisado'])

        with tab6:
            st.markdown("### 🎨 Descrição da Imagem")
            st.markdown(resultados['descricao_imagem'])

        with tab7:
            st.markdown("### 🖼️ Imagem Gerada")
            if 'imagem_gerada' in resultados and resultados['imagem_gerada']:
                st.image(
                    "imagem_gerada.png", caption="Imagem Gerada para o Post", use_container_width=True)
            else:
                st.warning("Nenhuma imagem foi gerada.")

        st.markdown("---")
        if st.button("🔄 Gerar Novo Post", use_container_width=True):
            if 'resultados' in st.session_state:
                del st.session_state.resultados
            if 'topico_atual' in st.session_state:
                del st.session_state.topico_atual
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">Desenvolvido por Eduardo Rocha com ❤️ usando Streamlit e Google Gemini</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
