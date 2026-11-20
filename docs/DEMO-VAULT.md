# Vault demo: la base de conocimiento de Tramalia

El Vault demo simula lo que un FDE se encuentra en un cliente: la wiki interna de una empresa, con documentos de varios departamentos, versiones que se contradicen y datos sueltos. Todo es inventado.

> Antes de generar nada, comprobar en un buscador que "Tramalia" no es una empresa real del sector. A 19 nov 2026 no aparece ninguna.

## 1. La empresa (biblia)

Este apartado es la **fuente de verdad**: las Notas se generan a partir de aquí, y las Preguntas de evaluación se comprueban contra aquí.

- **Tramalia** es una SaaS B2B española fundada en 2019 en Barcelona. Software de reservas, turnos y control de acceso para **centros deportivos** (gimnasios, rocódromos, clubs de pádel).
- ~85 empleados en 2026. Oficina en Barcelona (Poblenou, ficticia) y trabajo híbrido.
- **Productos:**
  - **Tramalia Reservas**: reservas de clases y pistas, app móvil para socios.
  - **Tramalia Acceso**: control de acceso con QR y tornos; integración con hardware de terceros.
  - **Tramalia Insights**: dashboards de ocupación y bajas (lanzado en 2025).
- **Planes y precios** (por centro y mes): Básico, Pro, Enterprise.
- **Departamentos**: Producto, Ingeniería, RRHH, Ventas y Customer Success, Dirección.
- **Personas**: unas 25 inventadas con nombre, rol y equipo (CEO, CTO, Head of People, 3 tech leads, PMs, comerciales, CSMs). Se listan en `Personas/` o dentro de las notas de equipo.

### Hechos que cambian en el tiempo (para preguntas temporales)

Cada uno existe en **dos o más Notas con fechas distintas**. La más reciente es la vigente.

| # | Hecho | Antes | Ahora |
|---|---|---|---|
| 1 | Días de teletrabajo por semana | 2 (política 2025) | 3 (política marzo 2026) |
| 2 | Precio del plan Pro | 89 €/centro/mes (2024) | 109 €/centro/mes (ene 2026) |
| 3 | Días de vacaciones | 23 | 25 (desde 2026) |
| 4 | Proveedor de pagos | Proveedor A | Proveedor B (migración Q2 2026) |
| 5 | Base de datos principal | MySQL | Postgres (ADR de 2025) |
| 6 | SLA del plan Enterprise | 99,5 % | 99,9 % (2026) |
| 7 | Límite de gastos de comida en viaje | 30 €/día | 40 €/día |
| 8 | Responsable de Customer Success | Persona X | Persona Y (desde sept 2026) |
| 9 | Frecuencia de releases | quincenal | semanal |
| 10 | Duración de la prueba gratuita | 30 días | 14 días |
| 11 | Ciclo de evaluación de desempeño | anual | semestral |
| 12 | Versión mínima de la app móvil soportada | 3.x | 4.2 |

### Temas que NO existen (para preguntas sin respuesta)

Plan de pensiones, sede en otro país, política de mascotas en la oficina, integración con Strava, precio del plan Enterprise (es "a consultar"), nombre del proveedor de limpieza.

## 2. Carpetas y tipos de Nota

| Carpeta | Tipos | Cantidad aprox. |
|---|---|---|
| `Producto/` | Fichas de producto, release notes, roadmap trimestral, specs de funcionalidad | 90 |
| `Ingenieria/` | ADRs, runbooks, postmortems, guías de onboarding técnico | 90 |
| `RRHH/` | Políticas (teletrabajo, vacaciones, gastos, formación), FAQs, onboarding | 50 |
| `Clientes/` | Fichas de clientes (gimnasios inventados), FAQs de soporte, casos de éxito | 90 |
| `Reuniones/` | Actas de all-hands, comités, retros | 60 |
| `Noticias/` | Comunicados internos, newsletters | 40 |
| raíz | `Inicio.md` y una nota índice por carpeta (como el vault real) | 7 |

Total: ~420 Notas, con longitudes variadas (de 80 a 1.500 palabras).

## 3. Formato de cada Nota

```markdown
---
fecha: 2026-03-02
departamento: rrhh            # producto | ingenieria | rrhh | clientes | direccion | ventas
tipo: politica                # politica | release-notes | adr | runbook | postmortem | acta | ficha | faq | comunicado | ...
etiquetas: [teletrabajo, hibrido]
autor: Marta Soler
---

# Política de teletrabajo 2026

...cuerpo con ## secciones...

Relacionado: [[RRHH]], [[Política de teletrabajo 2025]]
```

Nombre de archivo: el título, como en Obsidian (`Política de teletrabajo 2026.md`).

## 4. Reglas para que el vault sea útil para evaluar

- **Variedad de estilo.** Actas con viñetas y abreviaturas, ADRs formales, FAQs en pregunta-respuesta, release notes con tablas, comunicados en tono cercano. Si todo está escrito igual, la búsqueda semántica parece mejor de lo que es.
- **Cifras, nombres propios y códigos** (IDs de incidencias como `INC-2291`, versiones `v4.2.1`, nombres de clientes). Es donde BM25 gana a los vectores.
- **Sinónimos y paráfrasis**: "trabajo en remoto", "teletrabajo", "home office" en distintas Notas. Es donde los vectores ganan a BM25.
- **Información repartida**: algunas respuestas necesitan juntar 2-3 Notas (p. ej. qué clientes Enterprise tuvieron incidencias en el Q3).
- **Enlaces `[[...]]`** coherentes: cada Nota enlaza a su índice y a 1-3 Notas relacionadas.
- **Ruido realista**: Notas casi duplicadas (borrador y versión final), alguna Nota vacía o con "TODO".

## 5. Cómo se genera (con Claude Code, sin coste)

1. Escribir la biblia completa en `scripts/demo/biblia.md` (este documento ampliado con las 25 personas, 15 clientes y el calendario 2024-2026).
2. Para cada carpeta, pedir a Claude Code un **lote de 15-20 Notas** siguiendo la biblia, el formato y las reglas. Lotes pequeños para poder revisarlos.
3. Después de cada lote, `uv run python scripts/check_vault.py`:
   - frontmatter válido y campos obligatorios;
   - cada `[[enlace]]` apunta a una Nota existente (o se lista como roto);
   - los 12 hechos versionados aparecen con sus fechas correctas;
   - los temas "sin respuesta" no aparecen.
4. Commit por lote (`vault-demo: add RRHH batch 1`).
5. Al final, generar las ~60 Preguntas de evaluación **en una sesión nueva de Claude Code**, leyendo las Notas (no la biblia), para que las preguntas no copien las frases del generador. Alejandro revisa 15.
