# Etapa 1 — seleção do corpus

**Data da conferência:** 20/10/2026. **Estado:** fontes e páginas selecionadas; a ingestão automatizada pertence à Etapa 3.

## Recorte escolhido

O assistente responderá perguntas sobre conceitos, metodologia de coleta e revisão dos primeiros resultados do Censo Demográfico 2022. O índice inicial terá duas publicações oficiais do IBGE, registradas com URLs, páginas, tamanhos e hashes SHA-256 em [`data/source_manifest.json`](../data/source_manifest.json).

| Fonte | Páginas do PDF | Páginas impressas | Conteúdo incluído |
| --- | ---: | ---: | --- |
| *População e domicílios — Primeiros resultados* (`liv102011.pdf`) | 11–19 | 6–14 | Notas técnicas e conceitos, até antes de “Tratamento dos dados” |
| *Nota metodológica n. 01* (`liv102037.pdf`) | 6–12 | 6–12 | Introdução, política de revisão, revisão de campo e tratamento dos dados; sem o apêndice |

As páginas do PDF e as páginas impressas não coincidem na primeira publicação. Toda referência exibida ao usuário deverá usar **título da fonte, página impressa e URL**; o número da página do PDF também ficará nos metadados para auditoria.

## Conferência manual de amostras

As seguintes informações foram localizadas no texto extraído e conferidas nas páginas indicadas. Elas são exemplos de perguntas que o corpus poderá sustentar, não respostas já geradas pelo assistente.

| Pergunta de exemplo | Onde verificar | Resultado da conferência |
| --- | --- | --- |
| Qual é a data de referência do Censo 2022? | Primeiros resultados, p. impressa 11 / PDF 16 | A seção “Data de referência” informa a passagem de 31/07 para 01/08/2022. |
| O que é população residente? | Primeiros resultados, p. impressa 11 / PDF 16 | A seção de conceitos a define a partir dos moradores dos domicílios na data de referência. |
| Quais meios de coleta foram usados? | Primeiros resultados, p. impressa 8 / PDF 13 | A seção “Metodologia de coleta” descreve entrevista presencial, telefone e autopreenchimento pela internet. |
| Como o IBGE definiu a taxa média de crescimento anual? | Primeiros resultados, p. impressa 14 / PDF 19 | Há fórmula e explicação da compatibilização da população de 2010 com a base territorial de 2022. |
| Por que os primeiros resultados foram atualizados? | Nota metodológica, p. 6 / PDF 6 e p. 8 / PDF 8 | A nota descreve a segunda apuração e os ajustes de campo; informa que a data de referência original foi mantida. |

Os PDFs são legíveis por extração de texto, mas apresentam artefatos como espaços no meio de palavras e cabeçalhos repetidos. A Etapa 3 deve limpar esses problemas sem alterar números, negações, fórmulas ou referências de página. Uma amostra dos trechos limpos precisará ser comparada visualmente com os PDFs.

## Limites da primeira versão

- Perguntas sobre **valores municipais**, rankings, projeções atuais ou séries temporais não serão respondidas pelo RAG documental. Para isso, planejamos uma consulta estruturada ao SIDRA em etapa posterior, com tabela, ano e unidade explícitos.
- A página geral do Censo no site do IBGE servirá para localizar novas publicações, mas não será indexada inicialmente: é extensa e pode mudar. O manifesto registra seu link como referência.
- O apêndice da nota metodológica e as tabelas da publicação principal ficam fora do índice inicial. A ingestão de tabelas exigirá tratamento próprio.
- O corpus não serve para orientar procedimentos de atendimento ao cidadão nem para responder sobre outros serviços públicos.

## Próximo passo

Na Etapa 2, criar perguntas de avaliação com referência às fontes e páginas acima. Algumas perguntas devem exigir abstenção para testar se o sistema respeita o escopo. Depois, a Etapa 3 transformará o manifesto em um pipeline de ingestão reproduzível.
