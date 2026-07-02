# Climate Satellite

Servicio modular de imágenes satelitales para ClimateProyectar.

## Estrategia de almacenamiento

Este repositorio **no descarga ni almacena imágenes**.

El workflow consulta el catálogo oficial del Servicio Meteorológico Nacional y
publica únicamente:

```text
docs/manifiesto.json
```

Cada cuadro contiene una URL remota bajo:

```text
https://estaticos.smn.gob.ar/vmsr/satelite/
```

Por eso el historial de Git conserva solo un JSON pequeño.

## Producto inicial

```text
TOP_C13_ARG_ALTA
Topes Nubosos
Región Argentina
```

## Ejecución

```text
Actions
→ Actualizar satélite SMN
→ Run workflow
```

El workflow solo admite `workflow_dispatch`; la frecuencia se administra desde
cron-job.org.

Endpoint externo:

```text
https://api.github.com/repos/mtgproyect/climate-satellite/actions/workflows/actualizar-satelite.yml/dispatches
```

Cuerpo:

```json
{
  "ref": "main"
}
```

Una frecuencia prudente inicial es cada 20 minutos.

## Publicación

GitHub Pages:

```text
main
/docs
```

Archivos públicos:

```text
https://mtgproyect.github.io/climate-satellite/
https://mtgproyect.github.io/climate-satellite/manifiesto.json
```
