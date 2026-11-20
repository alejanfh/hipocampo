# Embeddings en local con multilingual-e5-small

Los embeddings se calculan en local con `intfloat/multilingual-e5-small` (384 dimensiones, unos 470 MB), que corre bien en la CPU de un Ryzen 5 1600 y entiende español. Local porque es gratis y el vault real (salud, finanzas, personas) no sale del ordenador. Se compara una vez con `BAAI/bge-m3` (1024 dimensiones, ~2 GB) y se documenta el resultado.

## Consequences

- e5 necesita los prefijos `passage: ` y `query: `; sin ellos el recall baja sin dar error. Hay un test que lo comprueba.
- Cambiar de modelo cambia la dimensión del vector: hay que regenerar la tabla `chunks` y reindexar.
