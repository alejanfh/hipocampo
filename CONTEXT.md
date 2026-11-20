# Hipocampo

Motor de búsqueda sobre vaults de Obsidian que encuentra las notas relevantes para una pregunta y se las da a un agente (Claude) para que responda citándolas.

## Language

### Contenido

**Vault**:
Carpeta de notas Markdown de Obsidian con frontmatter, carpetas por área y `[[wikilinks]]`.
_Avoid_: base de conocimiento, corpus, dataset

**Vault real**:
El segundo cerebro privado de Alejandro. Solo se usa en local y nunca se sube al repo.
_Avoid_: vault personal, datos reales

**Vault demo**:
Base de conocimiento interna de la **Empresa ficticia** (300-500 notas) en formato Obsidian, pública y versionada en el repo. Simula lo que un FDE montaría para un cliente.
_Avoid_: mock, vault de ejemplo

**Empresa ficticia**:
La empresa inventada dueña del **Vault demo**. No imita a ninguna empresa real.
_Avoid_: cliente, empresa demo

**Nota**:
Un archivo Markdown de un **Vault**. Es la unidad que se cita al responder.
_Avoid_: documento, página, archivo

**Chunk**:
Trozo de una **Nota** que se indexa y se recupera. Siempre pertenece a una sola **Nota**.
_Avoid_: fragmento, pasaje, trozo

**Configuración de vault**:
Descripción de un **Vault** que dice qué campo del frontmatter es la fecha, cuál el área y cuáles se pueden usar como **Filtro**.
_Avoid_: schema, settings

### Búsqueda

**Consulta**:
El texto que llega para buscar, con sus **Filtros** opcionales. La escribe un agente o una persona.
_Avoid_: query (en los docs en español), prompt, pregunta (ver **Pregunta de evaluación**)

**Filtro**:
Restricción sobre los metadatos de una **Nota** (área, rango de fechas, carpeta) que se aplica durante la búsqueda.
_Avoid_: facet

**Estrategia de recuperación**:
Forma de elegir qué contenido del **Vault** llega al modelo. Las que se comparan: **Contexto completo**, léxica (BM25), semántica (vectores), híbrida, híbrida + rerank y **Búsqueda agéntica**.
_Avoid_: retriever, método, pipeline

**Contexto completo**:
**Estrategia de recuperación** de referencia que mete el **Vault** entero en el prompt, sin buscar nada.
_Avoid_: long context, sin RAG

**Búsqueda agéntica**:
**Estrategia de recuperación** en la que el agente decide qué buscar y cuántas veces, usando herramientas (las de Hipocampo, o leer archivos y hacer grep).
_Avoid_: agentic RAG (en los docs en español)

**Resultado**:
Un **Chunk** devuelto por una búsqueda, con su puntuación final y el desglose de cada señal (léxica, semántica, rerank).
_Avoid_: hit, match

**Cita**:
Referencia a la **Nota** de la que sale una afirmación de la respuesta, escrita como `[[Nombre de la nota]]`.
_Avoid_: fuente, referencia

**Traza**:
Registro de una búsqueda: **Consulta**, **Estrategia de recuperación**, **Resultados**, tiempos y quién la pidió (MCP, web, evaluación).
_Avoid_: log

### Evaluación

**Pregunta de evaluación**:
Pregunta con su respuesta esperada y la **Nota** o **Notas** que la responden. Tiene un tipo: dato concreto, temporal, varias notas o sin respuesta.
_Avoid_: test case, golden

**Set de evaluación**:
Conjunto de **Preguntas de evaluación** de un **Vault**. El del **Vault demo** es público; el del **Vault real** es privado y nunca se sube.
_Avoid_: dataset, benchmark

**Evaluación de búsqueda**:
Medir si una **Estrategia de recuperación** trae las **Notas** correctas (recall@5, MRR). No usa ningún LLM.
_Avoid_: eval de retrieval

**Evaluación de respuestas**:
Medir si la respuesta final es fiel a las **Notas** y cita bien. Necesita un LLM que responda y otro que juzgue.
_Avoid_: eval de generación

## Relationships

- Un **Vault** tiene una **Configuración de vault** y muchas **Notas**; una **Nota** se divide en uno o más **Chunks**.
- El **Vault real** (personal) y el **Vault demo** (de empresa) comparten formato, no carpetas ni contenido. El mismo código sirve para los dos.
- Una **Consulta** se resuelve con una **Estrategia de recuperación** y produce **Resultados** y una **Traza**.
- Un **Set de evaluación** pertenece a un **Vault** y se pasa contra varias **Estrategias de recuperación** para compararlas.
- Una **Cita** apunta siempre a una **Nota**, nunca a un **Chunk**.

## Example dialogue

> **Dev:** "Si pregunto cuántos días de teletrabajo hay, ¿qué **Nota** debería salir?"
> **Experto:** "La política de 2026, no la de 2025. Es una **Pregunta de evaluación** temporal: la búsqueda híbrida trae las dos, y solo con el **Filtro** de fecha o el rerank sale la buena primero."

## Flagged ambiguities

- "RAG" se usa para el proyecto entero y para una técnica. Para comparar técnicas, usar **Estrategia de recuperación**.
- "Pregunta" se usaba para lo que escribe el usuario y para las del set. Resuelto: **Consulta** para lo primero, **Pregunta de evaluación** para lo segundo.
