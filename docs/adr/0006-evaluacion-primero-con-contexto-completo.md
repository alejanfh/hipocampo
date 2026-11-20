# Se evalúa antes de optimizar, y el Contexto completo es la línea base

Antes de construir búsqueda semántica existe un Set de evaluación y una cifra de BM25, y en la Evaluación de respuestas siempre se compara contra meter el vault entero en el prompt y contra la búsqueda agéntica con grep. Es lo que separa un RAG serio de un tutorial, y la pregunta honesta para el vault real (42 Notas) es si un RAG aporta algo. Si la respuesta es "no", es un resultado válido y se cuenta en el README.

## Consequences

- Ninguna mejora entra sin su fila en la tabla de resultados.
- El vault real solo pasa a usarse con Hipocampo si mide mejor que lo que ya hay.
