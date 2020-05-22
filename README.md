# ESBackup
Backup de indices en Elasticsearch

Para usar este script como la herramienta de backup, basta con instalar y verificar que el nombre de los indices debe ser {nombre-indice}-activo-yyy.mm.dd

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
