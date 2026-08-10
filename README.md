# aleu-site

Sitio público de [aleu.ai](https://aleu.ai). Marketing puro.

Hoy este repositorio contiene **solo su guard**: la regla llegó antes que el código que podría
violarla.

## La regla

**El sitio no tiene identidad.** No lee cookies, no persiste estado de usuario, no envía
credenciales, no consume la API de producto. Su única acción vecina a la autenticación es un enlace
a `app.aleu.ai/signup`.

Es el **Artículo XV** de la [constitución de aleu](https://github.com/maxparra-architecture/aleu/blob/main/.specify/memory/constitution.md),
que rige los dos repositorios del proyecto. Aquí se cita, no se copia.

Y se hace cumplir por CI:

```bash
python3 scripts/ci/check_isolation.py   # revisar la frontera
python3 -m pytest tests/ -q             # probar que el guard funciona
```

Ver [CLAUDE.md](CLAUDE.md) para la guía de trabajo.
