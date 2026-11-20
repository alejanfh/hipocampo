# Chunking, búsqueda híbrida y evaluación sin framework de RAG

Las piezas centrales (parseo, chunking, BM25, vectores, fusión RRF, rerank y métricas) se implementan con librerías pequeñas (bm25s, sentence-transformers, psycopg) y no con LangChain o LlamaIndex. El objetivo número uno es entender cómo funciona un RAG por dentro y poder defender cada decisión; un framework escondería justo eso. El código lo escribe Claude Code, así que el coste de no usar framework es bajo.

## Consequences

- Más código propio que revisar, pero cada pieza es corta y tiene tests.
- Si en el trabajo hace falta LangGraph o PydanticAI, se puede añadir un agente propio como fase extra; no es necesario porque el agente es Claude vía MCP (ADR 0001).
