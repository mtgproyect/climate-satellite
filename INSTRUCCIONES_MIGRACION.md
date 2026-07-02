# Migración del esqueleto a Climate Satellite funcional

## Reemplazar el contenido del repositorio

En la copia local de:

```text
mtgproyect/climate-satellite
```

copiar todo el contenido de este paquete y permitir que reemplace:

```text
README.md
.gitignore
docs/
.github/
```

También se agregarán:

```text
scripts/
tests/
requirements.txt
```

Después, en GitHub Desktop:

```text
Summary:
Activar catálogo satelital remoto del SMN

Commit to main
Push origin
```

## Ejecutar la primera prueba

```text
Actions
→ Actualizar satélite SMN
→ Run workflow
```

Resultado esperado:

```text
Actualizar catálogo satelital  ✓
Validar contrato               ✓
Guardar manifiesto             ✓
```

Luego esperar `pages build and deployment` y abrir:

```text
https://mtgproyect.github.io/climate-satellite/
```

El manifiesto debe indicar:

```json
{
  "enabled": true,
  "status": "ok",
  "storage": {
    "mode": "remote_urls_only",
    "stored_image_count": 0
  }
}
```

## Todavía no modificar ClimateProyectar V2

Primero verificar dos o tres ejecuciones manuales del repositorio satelital.
Después se activa la fuente en:

```text
climateproyectar-v2/docs/config/data-sources.json
```
