# Hipocampo solo busca; Claude redacta las respuestas vía MCP

Hipocampo no llama a ningún LLM para responder: expone la búsqueda como servidor MCP y es Claude (Desktop o Code, con la suscripción de Alejandro) quien busca, lee y redacta citando. Lo decidimos porque el proyecto tiene que ser gratis, la suscripción no se puede usar desde código propio como si fuera la API, y este es además el patrón que se usa en IAG (MCPs de la compañía conectados a un chat). Alternativas descartadas: API de Anthropic (coste), Ollama local (lento en un Ryzen 5 1600 y peor calidad en español), capas gratuitas de Gemini o Groq (dependencia de límites que cambian).

## Consequences

- No hay endpoint `/ask` propio ni chat en la web: la web es un buscador explicable.
- La Evaluación de respuestas se hace con un comando de Claude Code que lanza Alejandro, no en CI.
- Si algún día hay presupuesto, añadir generación propia es una capa más sobre el mismo servicio de búsqueda.
