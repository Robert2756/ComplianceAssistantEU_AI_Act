# EU AI Act Compliance Assistant

Eine Retrieval-Augmented-Generation-Pipeline (RAG) für Fragen zum EU AI Act. Sie läuft lokal: `multilingual-e5-base` für die Suche und `llama3.1:8b` (über Ollama) für die Antwortgenerierung.

## Pipeline: mit RAG

![Überblick über die RAG-Pipeline](pipeline/RAG.png)

*Der AI Act wird bereinigt und in Chunks zerlegt, die eingebettet werden und nur als Suchindex dienen. Der Artikel mit dem höchsten Score wird immer vollständig an das LLM übergeben. Weitere Artikel kommen nur dazu, wenn ihr Score nah am besten Artikel liegt und das Wortbudget es zulässt.*

## Baseline: ohne RAG

![Baseline ohne RAG](pipeline/NORAG.png)

*Zum Vergleich wird der gesamte bereinigte AI Act (etwa 85.000 Tokens) ohne Retrieval direkt in den Prompt gelegt.*

## Ergebnisse
