name: Actualizar satélite SMN

run-name: Satélite SMN · disparo externo

on:
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: climate-satellite
  cancel-in-progress: true

jobs:
  actualizar:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Descargar repositorio
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Instalar dependencias
        run: python -m pip install -r requirements.txt

      - name: Actualizar catálogo satelital
        run: python scripts/actualizar_satelite_smn.py

      - name: Validar contrato
        run: |
          python -m json.tool docs/manifiesto.json > /dev/null
          python -m unittest discover -s tests -v

      - name: Guardar manifiesto
        run: |
          git config user.name "github-actions[bot]"
          git config user.email \
            "41898282+github-actions[bot]@users.noreply.github.com"

          git add docs/manifiesto.json

          if git diff --cached --quiet; then
            echo "No hay un cuadro nuevo para publicar."
            exit 0
          fi

          git commit -m "Actualizar catálogo satelital SMN"

          for intento in 1 2 3; do
            echo "Intento de publicación ${intento}/3"
            git fetch origin main

            if ! git rebase origin/main; then
              git rebase --abort || true
              echo "Conflicto al integrar los cambios remotos."
              exit 1
            fi

            if git push origin HEAD:main; then
              echo "Catálogo satelital publicado."
              exit 0
            fi

            sleep 5
          done

          echo "No fue posible publicar después de 3 intentos."
          exit 1
