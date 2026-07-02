# Corrección de imágenes satelitales remotas

La captura demuestra que `manifiesto.json` se carga correctamente porque la
página muestra doce cuadros y sus fechas. El fallo está en la solicitud de cada
JPG al servidor externo del SMN.

## Archivo que debe reemplazarse

Copiar:

```text
docs/index.html
```

sobre el mismo archivo del repositorio:

```text
mtgproyect/climate-satellite
```

No reemplazar el manifiesto, el script Python ni el workflow.

## Cambio aplicado

La página ahora solicita las imágenes con:

```html
referrerpolicy="no-referrer"
```

También precarga cada cuadro antes de mostrarlo y evita dejar una imagen rota
visible. Si el servidor rechaza un cuadro, prueba el siguiente y muestra un
diagnóstico claro.

La estrategia de almacenamiento no cambia:

```text
GitHub: solo JSON y código
SMN: todas las imágenes
```

## Subida

En GitHub Desktop:

```text
Summary:
Corregir carga de imágenes satelitales remotas
```

Después:

```text
Commit to main
Push origin
```

Esperar el workflow de Pages y recargar con:

```text
Ctrl + F5
```

## Verificación

La página debe mostrar el cuadro satelital y animar los doce cuadros.

Si el servidor aún rechaza las imágenes, usar el botón:

```text
Abrir imagen oficial
```

Ese control permitirá distinguir entre:

```text
URL válida + bloqueo de incrustación
URL del SMN no disponible
```
