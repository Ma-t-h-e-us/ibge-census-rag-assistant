# Etapa 2 — conjunto inicial de avaliação

`questions.jsonl` contém 34 perguntas em português: 24 respondíveis, 6 fora do escopo e 4 ambíguas. Cada linha é um objeto JSON independente.

## Campos

- `id`: identificador estável da pergunta.
- `split`: `dev` para desenvolver e ajustar o sistema; `test` para comparação final entre versões.
- `category`: conceito ou tipo de falha testada.
- `expected_behavior`: `answer`, `abstain` ou `clarify`.
- `reference_summary`: resposta de referência resumida, escrita em outras palavras. Só aparece quando a pergunta é respondível.
- `evidence`: documento e páginas que devem aparecer na recuperação para as perguntas respondíveis. `pdf_page` é a página física do arquivo; `printed_page` é a numeração publicada pelo IBGE.
- `reason`: por que a pergunta deve receber abstenção ou pedido de esclarecimento.

## Como usar na avaliação

1. Para `answer`, medir se ao menos uma página de `evidence` aparece entre os cinco primeiros trechos (`any-page hit@5`). Medir separadamente a fração de páginas esperadas (`mean page recall@5`) e se todas elas apareceram. Se a pergunta exigir duas páginas, revisar também se a resposta usou as duas informações necessárias.
2. Revisar a resposta segundo três critérios separados: correção factual, sustentação nas fontes citadas e clareza. Uma citação presente não prova, sozinha, que a afirmação está sustentada.
3. Para `abstain`, verificar que o sistema declara a limitação e não inventa um número, procedimento ou projeção.
4. Para `clarify`, verificar que o sistema pede a informação faltante antes de dar um valor específico.
5. Reportar resultados de `dev` e `test` separadamente. As perguntas de `test` são versionadas para reprodutibilidade, mas não devem orientar ajustes finos durante o desenvolvimento; portanto, não constituem uma avaliação cega.

O conjunto foi preparado antes da implementação da busca. As respostas de referência devem ser revisadas quando o corpus mudar. Não enviar `reference_summary` ou `reason` ao modelo durante uma consulta: esses campos servem apenas para avaliar a saída.

A Etapa 4 avalia somente recuperação, com o comando `scripts/evaluate.py`. As perguntas `abstain` e `clarify` são executadas para inspeção, mas não recebem uma nota de abstenção, porque ainda não existe um componente que decida a resposta. O [relatório da execução](results/retrieval_report.json) separa `dev` e `test`. Uma alternativa de modelo também foi examinada em `test` durante esta etapa; por isso, os números atuais de `test` são exploratórios, e será necessário criar novas perguntas reservadas para uma estimativa final de generalização.
