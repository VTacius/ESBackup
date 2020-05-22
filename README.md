# ESBackup
Backup de indices en Elasticsearch 6.x

El script tiene como misión dejar el servidor siempre disponible; para lo cual procura mucho la cuestión del espacio

Para usar este script como la herramienta de backup, basta con instalar y verificar que el nombre de los indices activos debe ser {nombre\_indice}-activo-yyy.mm.dd; y el de los backup, pues {nombre\_indice}-backup-yyy.mm.dd

# Instalacion
Es manual

# Test
```sh
pytest -v test/
```
