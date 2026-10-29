# Etapa 3 — ingestão reproduzível

O comando `scripts/ingest.py` lê o manifesto versionado, confere o SHA-256 dos dois PDFs, extrai apenas as páginas e seções selecionadas e grava trechos locais com origem verificável.

## Executar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts\ingest.py --download
```

`--download` busca apenas PDFs ausentes. Um arquivo existente com hash divergente causa erro e não é substituído. Assim, uma revisão de publicação exige atualizar conscientemente o manifesto e a avaliação. Os PDFs e a saída gerada ficam fora do Git; URLs e hashes permanecem no manifesto.

Para executar os testes:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Saída

- `data/processed/chunks.jsonl`: um objeto JSON por trecho. Cada objeto traz `id` estável, texto, fonte, URL, página física do PDF e página impressa.
- `data/processed/build_report.json`: quantidade de fontes, páginas e trechos, parâmetros de divisão e SHA-256 da saída. Uma nova execução com os mesmos arquivos e parâmetros deve produzir o mesmo hash.

Os trechos têm até 180 palavras e sobreposição de 35 palavras, sem cruzar páginas. A página impressa é a que deve aparecer ao usuário; a página física serve para navegação no PDF. A primeira fonte começa em “Notas técnicas” e termina antes de “Tratamento dos dados”. A nota de revisão inclui as páginas 6–12 e exclui o apêndice.

## Limitação conhecida

A extração com `pypdf` contém, em alguns pontos, espaços inseridos dentro de palavras no PDF original. O pipeline remove cabeçalhos repetidos, números de página isolados e quebras de linha; não une palavras arbitrariamente, pois isso poderia alterar nomes ou números. A [Etapa 4](retrieval.md) mediu a busca sobre esses trechos; a extração ainda pode ser aperfeiçoada após revisar falhas específicas.
