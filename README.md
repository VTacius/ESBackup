# ESBackup
Backup de indices en Elasticsearch 6.x

El script tiene como misión dejar el servidor siempre disponible; para lo cual procura mucho la cuestión del espacio

Para usar este script como la herramienta de backup, basta con instalar y verificar que el nombre de los indices activos debe ser {nombre\_indice}-activo-yyy.mm.dd; y el de los backup, pues {nombre\_indice}-backup-yyy.mm.dd

# Instalacion
Es manual

Aunque parece que viene ya instalado en muchas distribuciones, el único paquete necesario para que esto funcione es

```bash
dnf install python3-requests-mock python3-requests
```

# Desarrollo.
En Fedora, un par de paquetes son necesarios

```bash
dnf install python3-pytest python3-devel python3-mock python3-requests-mock 
```

# Test
Usar a `pytest` como módulo nos evita muchos dolores de cabeza

```bash
python3 -m pytest test/
```
