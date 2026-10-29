# Censo em Contexto: assistente RAG sobre o Censo 2022

Projeto de portfólio para Engenharia de IA. A proposta é ajudar pessoas a entender conceitos e métodos do Censo Demográfico 2022 do IBGE, mostrar os trechos usados como evidência e medir a qualidade das respostas.

> **Estado:** Etapas 1–3 concluídas: corpus selecionado, avaliação criada e ingestão reproduzível implementada. Busca e geração ainda não iniciadas. Projeto independente, sem vínculo com o IBGE.

## Problema e resultado esperado

Uma pessoa faz uma pergunta em linguagem natural sobre o Censo 2022, como "O que significa população residente?" ou "Qual é a data de referência do Censo?". O sistema encontra trechos relevantes na documentação oficial e produz uma resposta com links para as fontes. Quando as fontes não sustentam uma resposta, ele informa que não encontrou evidência suficiente.

O projeto deve permitir comparar uma busca inicial simples com uma versão RAG e explicar, com exemplos, onde cada uma falha. Perguntas sobre valores numéricos de municípios ficam fora da primeira versão: elas exigem consulta estruturada a dados oficiais, com ano, unidade e tabela explícitos.

## Corpus inicial

- [Censo Demográfico 2022: População e domicílios — Primeiros resultados](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102011.pdf): notas técnicas e conceitos nas páginas 11–19 do PDF.
- [Nota de atualização dos primeiros resultados](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102037.pdf): revisão dos resultados nas páginas 6–12 do PDF.

O [manifesto de fontes](data/source_manifest.json) registra URLs, páginas e hashes dos arquivos baixados. A [seleção do corpus](docs/corpus_selection.md) explica o recorte, a conferência manual e as exclusões. A [página geral do Censo](https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html), a [API de Localidades](https://servicodados.ibge.gov.br/api/docs/localidades) e a [tabela 4709 do SIDRA](https://sidra.ibge.gov.br/tabela/4709/) são referências para futuras expansões; não entram no índice inicial.

O [conjunto inicial de avaliação](eval/README.md) contém perguntas respondíveis, fora do escopo e ambíguas, com páginas de referência para conferir a recuperação e as respostas.

## Primeira versão

1. Usar as seções já selecionadas no manifesto para compor o corpus.
2. Criar ingestão reproduzível: ler as fontes, extrair texto, dividir em trechos e registrar metadados da fonte.
3. Implementar uma busca lexical como referência e uma busca semântica para comparação.
4. Expor perguntas e respostas por uma API; cada resposta deve incluir os trechos e links usados.
5. Montar um conjunto de avaliação com perguntas respondíveis e perguntas sem resposta no corpus.
6. Registrar resultados, erros observados, latência e custo por consulta, quando houver uso de API paga.

## Como avaliar

- **Recuperação:** proporção de perguntas cuja fonte correta aparece entre os primeiros resultados (`recall@k`).
- **Resposta:** revisão de uma amostra com critérios explícitos de correção, suporte nas fontes e clareza.
- **Abstenção:** proporção de perguntas sem evidência para as quais o sistema evita inventar uma resposta.
- **Operação:** tempo de resposta e custo estimado por consulta.

O conjunto de avaliação deve conter pelo menos 30 perguntas, incluindo casos ambíguos, perguntas fora do escopo e perguntas que o corpus não responde. Os resultados serão apresentados por categoria e acompanhados de exemplos de falha, não apenas de uma nota geral. Perguntas como "Qual era a população de Campinas em 2022?" devem ser encaminhadas para a futura consulta estruturada ou receber uma resposta que explique a limitação da primeira versão.

## Tecnologias previstas

O projeto será feito em Python. O núcleo RAG poderá ser usado por uma API FastAPI e por uma interface Streamlit, também escrita em Python. Para a busca, haverá uma referência lexical e uma versão com embeddings e índice local. Testes com pytest e execução por Docker entram após o primeiro fluxo completo funcionar localmente. A escolha do provedor de LLM dependerá dos limites de custo.

Veja o [plano de arquitetura](docs/architecture.md) para o fluxo de uma pergunta, a estrutura de pastas e a medição de latência e tokens.

## Ingestão local

Com Python 3.11 ou superior, execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts\ingest.py --download
```

O comando verifica os hashes das fontes e grava trechos com páginas e URLs em `data/processed/chunks.jsonl`. Consulte a [documentação da ingestão](docs/ingestion.md) para formato, testes e limitações.

## Entregáveis para o portfólio

- Código de ingestão, recuperação, geração e API.
- Dados de avaliação versionados e comando para reproduzir as métricas.
- README com arquitetura, decisões técnicas, resultados, limitações e exemplos de uso.
- Demonstração curta do fluxo e de um caso em que o sistema se abstém corretamente.

## Próximas etapas

1. Implementar a busca lexical e medir `recall@k`.
2. Adicionar recuperação semântica, respostas fundamentadas e comparação de resultados.
3. Integrar uma tabela do SIDRA apenas depois que as respostas conceituais estiverem avaliadas.
