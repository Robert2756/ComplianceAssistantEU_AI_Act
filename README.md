# EU AI Act Compliance Assistant

Antworten zu relevanten AI Fragen sollen mit Referenz zum AI Act mithilfe einer Retrieval-Augmented-Generation-Pipeline (RAG) ausgegeben werden. Sie Pieline läuft lokal: `multilingual-e5-base` für die Suche und `llama3.1:8b` (über Ollama) für die Antwortgenerierung.

## Pipeline: mit RAG

![Überblick über die RAG-Pipeline](pipeline/RAG.png)

*Der AI Act wird bereinigt und in Chunks zerlegt, die eingebettet werden und nur als Suchindex dienen. Der Artikel mit dem höchsten Score wird immer vollständig an das LLM übergeben. Weitere Artikel kommen nur dazu, wenn ihr Score nah am besten Artikel liegt und das Wortbudget es zulässt.*

## Baseline: ohne RAG

![Baseline ohne RAG](pipeline/NORAG.png)

*Zum Vergleich wird der gesamte bereinigte AI Act (etwa 85.000 Tokens) ohne Retrieval direkt in den Prompt gelegt.*

## Ergebnisse
Die Antworten der Assistenten zu den zehn Fragen (./eval/questions.jsonl) wurden per Hand gegen den offiziellen AI Act bewertet. Die detaillierten Antworten und Metriken können in ./eval/results.jsonl oder results.txt eingesehen werden. Händische Notizen dazu befinden sich am Ende dieser README.

Folgende Grafik zeigt die Performance der drei Assistenten. Die drei Evaluationen basieren dabei auf subjektiven Kriterien:

- correct: keine Halluzinationen, Antwort bezieht sich auf die Frage, es werden keine essentiellen Punkte vorenthalten
- partly: falsche Quellen angegeben zu richtigen Aussagen, keine grundlegend essentiellen Artikel oder Paragraphen wurden nicht ausgegeben
- incorrect: Halluzinationen, falsche Quellen mit falschen Informationen, Essentielle Informationen enthalten

![Baseline ohne RAG](eval/Accuracies.png)

Folgende Grafik zeigt essentielle Metriken der Pipelines (gesamte Verarbeitungsdauer und Tokenanzahl):

![Baseline ohne RAG](eval/Metrics.png)

## Interpretation

# No RAG
- schnellste Verarbeitungsdauer
- Halluzinationen, falsche Quellenangaben und Enthaltung von Informationen die höchstwahrscheinlich auf eine veraltete Version des AI Acts zurückzuführen sind

# RAG
- Verarbeitungsdauer minimal langsamer als No RAG, vereinzelt schneller
- meist korrekte Angabe der Quelle im AI Act (Artikels und Paragraph)
- keine Halluzinationen, ehrliche Antwort auf unlösbare Frage Nummer 10
- Problem: wenn Artikel in mehrere Chunks geteilt wird im Embeddingmodell kein Kontext verwendet -> spätere Chunks verlieren bezug zu vorherigen; das führt dazu dass essentielle Chunks nicht an das LLM weitergegeben werden; LLM antwortet basierend auf falschen oder unvollständigen Informationen (Frage 6 und 7)

# FULL
- sehr lange Verarbeitungsdauer, deutlich länger als die beiden anderen Pipelines
- keine Halluziinationen, ehrliche Antwort auf unlösbare Frage Nummer 10
- meistens keine Quellenangaben zum AI Act! Es fehlen die Paragraphen oder Unterpunkte der Paragraphen auch wenn die Informationen meist korrekt sind (z.b. Frage 4)


# Händische Notizen zur subjektiven Evaluation
Question 1: Which AI practices are prohibited under the AI Act?
--- NONE | 26s | prompt 55 tok | out 315 tok | ctx 4096 ---
Article -> correct (5)
Paragraph -> incomplete ( (1) cited but only (a))
Hallucinations -> 5(2) - 5(5)

--- RAG | 38s | prompt 3991 tok | out 277 tok | ctx 10240 | retrieved: art5, art50, art2 ---
Article -> correct
Paragraph -> correct but compressed
Hallucinations -> no

--- FULL | 1319s | prompt 67241 tok | out 295 tok | ctx 88064 ---
Article -> correct
Paragraph -> correct but compressed, wrong numeration
Hallucination -> no


Question 2: How does the AI Act define an 'AI system'?
--- NONE | 19s | prompt 57 tok | out 140 tok | ctx 4096 ---
Article -> correct (3)
Paragraph -> correct (3(1))
Hallucinations -> yes

--- RAG | 52s | prompt 4759 tok | out 91 tok | ctx 10240 | retrieved: art3, art50, art75 ---
Article -> correct (3)
Paragraph -> correct (3(1))
Hallucinations -> no

--- FULL | 1524s | prompt 67243 tok | out 85 tok | ctx 88064 ---
Article -> not cited (uses correct Article 3)
Paragraph -> not cited (uses correct Article 3(1))
Hallucinations -> no 


Question 3: What is the maximum administrative fine for using a prohibited AI practice, and how does it differ for SMEs?
--- NONE | 23s | prompt 67 tok | out 189 tok | ctx 4096 ---
Article -> wrong (cites "Article 58(1)/(2)"; fines are in Art. 99.)
Paragraph -> wrong (99(3) and 99(6) are the right ones)
Hallucinations -> yes: EUR 20M / 4% (should be 35M / 7%), SME figure "10M / 2%" (the Act has no
separate SME amounts), the cited document "2021/C 281/01", and the claim that the regulation
"is still in the proposal phase"

--- RAG | 33s | prompt 2213 tok | out 102 tok | ctx 6144 | retrieved: art99, art100, art101 ---
Article -> correct (Art. 99)
Paragraph -> correct (99(3) for the fine, 99(6) for SMEs)
Hallucinations -> no

--- FULL | 1719s | prompt 67253 tok | out 97 tok | ctx 88064 ---
Article -> correct (Art. 99)
Paragraph -> partly: no paragraph cited at all; the content matches 99(3) and 99(6)
Hallucinations -> no


Question 4: When is an AI system classified as high-risk, and when can an Annex III system be exempt?
--- NONE | 32s | prompt 65 tok | out 256 tok | ctx 4096 ---
Article -> wrong (relevant article is Art. 6)
Paragraph -> wrong (no cited paragraph says what it claims)
Hallucinations -> yes

--- RAG | 77s | prompt 2983 tok | out 433 tok | ctx 8192 | retrieved: art6, annexIII, art7 ---
Article -> correct (Art. 6, plus Art. 7 as a side note)
Paragraph -> correct
Hallucinations -> no

--- FULL | 1807s | prompt 67251 tok | out 311 tok | ctx 88064 ---
Article -> correct (Art. 6), but no paragraph numbers
Paragraph -> content matches 6(1)-(4), none is cited
Hallucinations -> no


Question 5: What are the obligations of deployers of high-risk AI systems?

--- NONE | 35s | prompt 58 tok | out 252 tok | ctx 4096 ---
Article -> wrong (the article is Art. 26)
Paragraph -> wrong
Hallucinations -> yes

--- RAG | 95s | prompt 2626 tok | out 551 tok | ctx 8192 | retrieved: art26, art25, art16 ---
Article -> correct (Art. 26)
Paragraph -> correct: every cited paragraph
Hallucinations -> no

--- FULL | 1481s | prompt 67244 tok | out 102 tok | ctx 88064 ---
Article -> correct (Art. 26)
Paragraph -> no paragraph cited; content matches
Hallucinations -> no


Question 6: From which date does the AI Act apply in general, and which provisions apply
earlier or later?

--- NONE | 18s | prompt 64 tok | out 123 tok | ctx 4096 ---
Article -> wrong (answer is in Art. 113)
Paragraph -> wrong (no paragraph cited, and the cited articles are about other things)
Hallucinations -> yes: all four dates

--- RAG | 43s | prompt 2284 tok | out 216 tok | ctx 6144 | retrieved: art111, art56, art79 ---
Article -> wrong for the main question (Art. 111 is the transitional article, the answer is
in Art. 113, which was not retrieved!!)
Paragraph -> partly
Hallucinations -> yes, applies from 2 August 2027" is wrong
(general date is 2 August 2026!!) 
PROBLEM: If wrong article provided from the embedding the model simply does not receive useful information to begin with

--- FULL | 1329s | prompt 67250 tok | out 110 tok | ctx 88064 ---
Article -> correct (Art. 113)
Paragraph -> content correct: general date and items (a)-(c); no lettering
Hallucinations -> no


Question 7: A company uses an AI system to filter job applications and rank candidates.
How is this system classified under the AI Act?

--- NONE | 30s | prompt 69 tok | out 269 tok | ctx 4096 ---
Article -> wrong (the answer is Annex III point 4(a) via Art. 6(2))
Paragraph -> wrong
Hallucinations -> yes

--- RAG | 34s | prompt 2373 tok | out 129 tok | ctx 6144 | retrieved: art80, art2, art6 ---
Article -> partly (cites Art. 6(1), which is not the relevant paragraph; 6(2) points to Annex III)
Paragraph -> partly (6(1) is described correctly, but it does not apply to recruitment systems)
Hallucinations -> no. It abstains ("I do not know") and the abstention is faithful to its
prompt: Annex III, where the answer is, was not retrieved. But it is a false negative: the
Act does answer the question
PROBLEM: Probably not enough context length to link Annex III 4(a) to "high risk" in the embedding stage (not enough context length)

--- FULL | 1547s | prompt 67255 tok | out 116 tok | ctx 88064 ---
Article -> partly (cites Art. 6(2); the quoted content is from Annex III point 4(a))
Paragraph -> content correct, location wrong (it is Annex III point 4(a), not Art. 6(2))
Hallucinations -> no. Conclusion correct


Question 8: When is a general-purpose AI model considered to have systemic risk, and what
additional obligations then apply to its provider?

--- NONE | 44s | prompt 68 tok | out 364 tok | ctx 4096 ---
Article -> wrong (the articles are 51, 52 and 55)
Paragraph -> wrong
Hallucinations -> yes
PROBLEM: Trained on older AI act data

--- RAG | 40s | prompt 1201 tok | out 270 tok | ctx 6144 | retrieved: art55, art52, art93 ---
Article -> partly (Art 51 was not retrieved)
Paragraph -> partly (Art. 55 correct, Art. 51 missing)
Hallucinations -> partly (never states what 51(1)(a) is, and does not flag that this part is unanswerable from its sources)

--- FULL | 1996s | prompt 67254 tok | out 1500 tok | ctx 88064 ---
Article -> correct (51, 52, 55 are the right articles)
Paragraph -> partly: the Art. 51 and 55 paragraphs are right; paragraph 52(5) belongs to 52(4) and five 56
paragraphs are mis-numbered and do not suit the question
Hallucinations -> no invented content. Problems: output hit 1500 tokens and is cut off mid-sentence


Question 9: Welche Transparenzpflichten gelten für Chatbots und Deepfakes?

--- NONE | 24s | prompt 63 tok | out 158 tok | ctx 4096 ---
Article -> wrong (answer is Art. 50)
Paragraph -> wrong (none cited)
Hallucinations -> yes

--- RAG | 60s | prompt 1876 tok | out 409 tok | ctx 6144 | retrieved: art50, art13, art55 ---
Article -> yes (Art. 50 correct; Art. 13 is added and does not belong -> optional no harm)
Paragraph -> correct
Hallucinations -> no

--- FULL | 1662s | prompt 67249 tok | out 554 tok | ctx 88064 ---
Article -> correct (Art. 50, and the regulation number 2024/1689 is correct)
Paragraph -> no paragraph numbers; content covers 50(1)-(4) but no citations
Hallucinations -> no


Question 10: Does the AI Act give victims a right to financial compensation for damage
caused by an AI system?

--- NONE | 39s | prompt 64 tok | out 310 tok | ctx 4096 ---
Article -> wrong
Paragraph -> wrong (none cited)
Hallucinations -> yes

--- RAG | 21s | prompt 1845 tok | out 24 tok | ctx 6144 | retrieved: art7, art50, art86 ---
Article -> none cited, CORRECT
Paragraph -> none cited, CORRECT
Hallucinations -> no, CORRECT

--- FULL | 1633s | prompt 67250 tok | out 194 tok | ctx 88064 ---
Article -> none cited CORRECT
Paragraph -> none cited CORRECT
Hallucinations -> no
