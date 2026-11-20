# Hipocampo

Motor de búsqueda local sobre vaults de Obsidian, expuesto a Claude vía MCP. Proyecto personal de Alejandro para **aprender** backend, Python e IA aplicada, y enseñarlo en GitHub.

Lee antes de trabajar:
- `CONTEXT.md`: glosario. Usa sus términos exactos en código, commits y explicaciones (Nota, Chunk, Consulta, Estrategia de recuperación...).
- `docs/SPEC.md`: qué se construye y cómo.
- `docs/PLAN.md`: fases y ciclo de trabajo. Trabaja solo en la fase actual.
- `docs/adr/`: decisiones tomadas. No las contradigas sin proponer un ADR nuevo.

## Cómo trabajamos

- **Alejandro no escribe código a mano: tú lo escribes, él lo entiende y lo revisa.** Viene de frontend (React/TypeScript); Python y backend son nuevos para él.
- **Concepto antes de código.** Al empezar una fase, explica los conceptos de esa fase con ejemplos del propio proyecto, en español, antes de escribir nada. Si Alejandro dice que algo no se entiende, usa la skill `explain-granular`.
- **Pasos pequeños.** Un cambio con sentido por commit. Después de cada paso, resume en 3-5 líneas qué has hecho y por qué, y señala la línea más importante para que la lea.
- **El porqué siempre.** Cada elección (librería, parámetro, estructura) lleva una frase de porqué. Si es difícil de revertir, sorprendente y fruto de un trade-off real, propón un ADR en `docs/adr/`.
- **Cierre de fase:** pasa la evaluación, haz 3-4 preguntas de comprensión (Alejandro responde sin mirar; corrige con cariño y precisión) y escribe `docs/aprendizajes/NN-fase.md` a partir de sus respuestas con la plantilla de esa carpeta.
- **Medir antes de optimizar.** Ninguna mejora de búsqueda se da por buena sin su cifra de `hipocampo eval search`.

## Reglas técnicas

- Python 3.12 con `uv`. Antes de dar algo por terminado: `uv run ruff check --fix`, `uv run ruff format`, `uv run pytest`.
- Capas: `retrieval/service.py` tiene la lógica; `mcp_server.py`, `api.py` y `cli.py` son finos y solo llaman al servicio; el acceso a SQLite está en `storage/`.
- SQL plano en `db/migrations/NNN_*.sql`. Nunca cambies una migración ya aplicada: añade otra.
- Código, nombres, comentarios, commits y README en **inglés**. CONTEXT.md, docs/ (SPEC, PLAN, ADRs, aprendizajes) en **español**.
- Nada de APIs de pago ni servicios en la nube. Modelos en local y en CPU.
- Entorno: Windows nativo (sin WSL2 ni Docker) en un Ryzen 5 1600 con 16 GB. Procesa embeddings por lotes y no cargues dos modelos grandes a la vez.

## Privacidad (no negociable)

- El **vault real** de Alejandro nunca se sube: ni su ruta, ni su contenido, ni sus Trazas, ni sus preguntas. Vive en `.env`, `configs/*.local.yaml` y `eval/*.local.yaml`, todos en `.gitignore`.
- No copies texto del vault real a issues, commits, tests, fixtures ni documentación. Para tests, usa el vault demo o Notas inventadas.
- Antes de cada commit, revisa que no entra nada de lo anterior.
