# Sistema de Agentes IA para Criação de Posts no Instagram

Este projeto é um sistema de agentes de IA que cria posts para o Instagram. A interface é construída com Streamlit.

## Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Framework da Interface:** Streamlit
- **IA Generativa:** Google Gemini
- **Gerenciador de Pacotes:** uv

## Como Usar

### 1. Baixar o Repositório

Para baixar o repositório, use o seguinte comando:

```bash
git clone https://github.com/eduardodarocha/multiagents-streamlit-instagram-gemini.git
```

### 2. Inicializar o Ambiente Virtual

Este projeto usa `uv` para gerenciar o ambiente virtual e as dependências. Para inicializar o ambiente virtual, execute os seguintes comandos:

```bash
# Crie o ambiente virtual
uv venv

# Ative o ambiente virtual
# No Windows
.venv\Scripts\activate
# No macOS/Linux
source .venv/bin/activate

# Instale as dependências
uv pip install -r requirements.txt
```

### 3. Rodar a Aplicação

Para rodar a aplicação, execute o seguinte comando:

```bash
streamlit run streamlit_agentes_ia_v5.py
```

A aplicação estará disponível no seu navegador no endereço `http://localhost:8501`.
