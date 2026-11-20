# El vault demo es la wiki de una empresa ficticia, no una persona

El repo público funciona con la base de conocimiento interna de Tramalia, una SaaS B2B inventada (~420 Notas en formato Obsidian), en lugar de un clon ficticio del vault personal. Así el proyecto cuenta el caso que importa en una entrevista de FDE (un RAG para la documentación de un cliente, como el ChatGPT interno de IAG) y el corpus es lo bastante grande para que las estrategias de búsqueda se diferencien: el vault real tiene 42 Notas (~12k tokens) y cabe entero en el contexto de cualquier modelo.

## Consequences

- El código no puede asumir las carpetas ni los campos del vault real: cada vault tiene su Configuración de vault (`configs/*.yaml`).
- Hace falta una biblia de la empresa y un script de comprobación (ver DEMO-VAULT.md).
