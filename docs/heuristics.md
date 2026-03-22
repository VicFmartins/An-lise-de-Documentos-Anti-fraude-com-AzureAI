# Heuristicas de risco

O projeto usa uma triagem heuristica para transformar resultados de OCR ou do Azure AI Document Intelligence em um score de risco inicial.

## Sinais cobertos

- campos obrigatorios ausentes por tipo de documento
- baixa confianca de OCR
- documento reutilizado varias vezes
- metadado de edicao apos o scan
- palavras suspeitas no texto
- CPF ou CNPJ invalidos
- datas futuras ou expiradas
- inconsistencia de valores totais

## Leitura do score

- `0 a 14`: risco baixo
- `15 a 39`: risco medio
- `40 a 69`: risco alto
- `70 a 100`: risco critico

## Observacao

Esta abordagem nao substitui modelos antifraude treinados com historico real. Ela funciona bem como camada inicial de triagem, explicabilidade e demonstracao de produto.
