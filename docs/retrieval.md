# Etapa 4 — recuperação e avaliação de evidências

O objetivo desta etapa é encontrar trechos do corpus para uma pergunta e verificar se as páginas oficiais esperadas aparecem nos resultados. Ela não gera respostas.

## Implementação

- **Busca lexical:** `TfidfVectorizer` do scikit-learn com palavras e pares de palavras, sem distinção de acentos. TF-IDF dá mais peso a termos úteis para distinguir trechos. A pontuação é a similaridade entre a pergunta e cada trecho; essa busca precisa de algum vocabulário em comum.
- **Busca semântica:** FastEmbed executa localmente o modelo [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small), com pesos ONNX O4 fixados na revisão `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Os trechos recebem o prefixo `passage:`, e as perguntas, `query:`, como orienta o cartão do modelo. Os vetores são comparados por similaridade de cosseno. O modelo aceita até 512 tokens; a verificação local encontrou no máximo 317 tokens em um trecho, sem truncamento nesta versão.
- **Cache:** os vetores dos 45 trechos ficam em `data/models/`. O índice é recriado se o conteúdo dos trechos ou a revisão do modelo mudar. O modelo é baixado na primeira execução e reutilizado localmente nas próximas. PDFs, modelos e vetores não entram no Git.
- **Saída:** as duas buscas devolvem trecho, pontuação, título, URL e página do PDF. O comando `scripts/search.py` mostra esses dados para inspeção humana.

O modelo semântico é executado no computador, sem chave de API e sem cobrança por consulta. Na primeira execução, o download dos pesos O4 exige conexão e cerca de 235 MB, além dos arquivos do tokenizador.

## Executar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[semantic]"
.\.venv\Scripts\python.exe scripts\ingest.py --download
.\.venv\Scripts\python.exe scripts\search.py "O que é população residente?" --method lexical
.\.venv\Scripts\python.exe scripts\search.py "O que é população residente?" --method semantic
.\.venv\Scripts\python.exe scripts\evaluate.py --method both
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

`scripts/evaluate.py` produz `eval/results/retrieval_report.json`, com versões das bibliotecas, identificador e revisão do modelo, hash do corpus, métricas por divisão e os primeiros resultados de cada pergunta. `dev` tem 20 perguntas (15 respondíveis); `test` tem 14 (9 respondíveis). Uma alternativa de modelo foi executada nas duas divisões antes de fixarmos o E5. Assim, os números de `test` são exploratórios; uma estimativa final de generalização exigirá novas perguntas reservadas.

## Resultados desta execução

| Busca | Divisão | Página esperada em 1º | Página esperada no top 5 | Todas as páginas no top 5 | Mediana da busca |
| --- | --- | ---: | ---: | ---: | ---: |
| TF-IDF | dev | 13/15 (86,7%) | 15/15 (100%) | 15/15 (100%) | cerca de 1 ms |
| TF-IDF | test | 7/9 (77,8%) | 9/9 (100%) | 9/9 (100%) | cerca de 1 ms |
| E5 small | dev | 13/15 (86,7%) | 15/15 (100%) | 15/15 (100%) | cerca de 10–15 ms |
| E5 small | test | 8/9 (88,9%) | 9/9 (100%) | 9/9 (100%) | cerca de 10–15 ms |

Os tempos medem apenas a consulta após aquecimento, em uma execução local; download e preparação do índice são medidos separadamente no JSON. Não são uma promessa de desempenho em outra máquina. Para a pergunta Q019, que espera duas páginas, `all_pages_hit` confere as duas; `any_page_hit` sozinho seria insuficiente.

## Leitura dos resultados e limites

As duas abordagens recuperaram alguma página esperada no top 5 de todas as 24 perguntas respondíveis nesta amostra. A busca semântica trouxe a página esperada em primeiro lugar em mais uma pergunta de `test`, mas não melhorou todos os casos; em `dev`, houve empate no primeiro lugar e TF-IDF foi melhor no top 3. O conjunto é pequeno, e pequenas diferenças de contagem não justificam declarar uma vencedora geral.

Esta métrica verifica **páginas**, não se o trecho contém todas as palavras necessárias à resposta. Trechos repetidos da mesma página podem ocupar várias posições, e as páginas foram escolhidas manualmente. Perguntas fora do escopo e ambíguas geram resultados de busca, mas esta etapa não decide se o sistema deve responder, pedir esclarecimento ou se abster. Pontuações de similaridade ainda não são limiares confiáveis para essa decisão. A qualidade final da resposta e as citações serão avaliadas na etapa de geração.
