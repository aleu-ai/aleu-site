# aleu-site — guía de trabajo

El sitio público de **aleu.ai**. Marketing puro.

Hoy este repositorio contiene **solo su guard**: la regla llegó antes que el código que podría
violarla. No hay landing todavía.

---

## La regla que define este repositorio

> **El sitio no tiene identidad.**
>
> No lee cookies, no persiste estado de usuario, no envía credenciales, no construye cabeceras de
> autorización, no importa el cliente de API generado, no llama a la API de producto y no envía
> formularios a destinos propios.
>
> Su única acción vecina a la autenticación es un enlace a `app.aleu.ai/signup`.

Esto **no es una convención de este repositorio**: es el **Artículo XV** de la constitución de aleu,
que rige los dos repositorios del proyecto.

📖 **La ley, íntegra y en su único lugar:**
[`aleu/.specify/memory/constitution.md`](https://github.com/maxparra-architecture/aleu/blob/main/.specify/memory/constitution.md)

**No copies el texto del artículo aquí.** Si lo duplicas, diverge (Art. XVI). Cítalo por enlace.

### Por qué existe

Cuando un flujo de identidad se reparte entre dos superficies sin un dueño claro, los errores no
aparecen en el código de ninguna de las dos: aparecen en la costura. Es una clase de fallo que la
revisión normal no atrapa, porque cada lado parece correcto por separado.

La frontera está especificada, y **es un test**.

## El guard

```bash
python3 scripts/ci/check_isolation.py      # revisar la frontera
python3 -m pytest tests/ -q                # probar que el guard funciona
```

- `scripts/ci/check_isolation.py` — recorre el código del sitio y falla con archivo, línea, código
  de regla y motivo.
- `tests/test_isolation.py` — planta una violación real de cada regla y verifica que el guard la
  detecta. Art. VIII: un guard sin test es un guard que un día deja de detectar y nadie se entera.
- `.github/workflows/pr.yml` — corre ambos en cada PR y en cada push a `main`.

**Si el guard te bloquea, el camino no es saltarlo.** Es enmendar el Artículo XV con Max, en `aleu`.
Un check que se puede rodear no es un check.

## Qué artículos rigen este repositorio

Según la sección "Superficies y alcance" de la constitución: **I** (idioma), **VII** (secretos),
**IX** adaptado (sin ciclo completo de spec mientras sea marketing estático), **XI** (alcance
mínimo), **XV** (identidad), **XVI** (alcance por superficie), **XVII** (la documentación no
sobre-representa la madurez).

Los que no están en esa lista **no aplican aquí**. Este sitio no necesita RLS ni 85% de cobertura de
dominio.

## Antes del primer commit de landing

Dos cosas que hay que decidir **antes**, porque después son caras:

1. **Binarios pesados fuera del repositorio.** El video, los frames y los logos van a Object Storage
   o Git LFS, nunca al historial. Sacarlos después es una operación de un solo sentido.
2. **Tokens de marca.** Decidir si se publican como paquete desde `aleu` o se duplican con un check
   de sincronía. Hoy no hay landing, así que la decisión está diferida — pero es explícita, no
   olvidada.

## El otro repositorio

**[`maxparra-architecture/aleu`](https://github.com/maxparra-architecture/aleu)** — la plataforma:
backend, frontend de la app, infraestructura, contratos y specs. Ahí vive la constitución, el
glosario y el registro de decisiones.
