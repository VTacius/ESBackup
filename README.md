# ESBackup
Backup de indices en Elasticsearch 6.x

El script tiene como misión dejar el servidor siempre disponible; para lo cual procura mucho la cuestión del espacio

Para usar este script como la herramienta de backup, basta con instalar y verificar que el nombre de los indices activos debe ser {nombre\_indice}-activo-yyy.mm.dd; y el de los backup, pues {nombre\_indice}-backup-yyy.mm.dd

## Instalacion
Por ahora, la distribución destino es Debian 9. (Ni siquiera 10) Así que es el único paquete creado. Para otros destinos, tendré que hacerse a mano
Aunque parece que viene ya instalado en muchas distribuciones, el único paquete necesario para que esto funcione es `Request`

```bash
dnf install python3-requests
```

## Desarrollo.
Ya que el destino final de esta aplicación es Debian, he cuidado que las versiones a usar sean compatibles con las disponibles en 9.x
```bash
pipenv --python 3.5
pipenv shell
pipenv install
pipenv install --dev
```

En Fedora, un par de paquetes son necesarios

```bash
dnf install python3-pytest python3-devel python3-mock python3-requests-mock 
```

## Test
Hay dos grupos de test (Por lo pronto, un poco redundantes) que deben correrse desde la raíz del repositorio:

Para el código python, usamos `pytest`; en forma de módulo, lo que permite ahorrar muchos dolores de cabeza. Antes de correrlos, debemos aseguranos de tener el módulo hecho en Rust
```bash
rustup run nightly maturin develop --release
python -m pytest esbackup/test/
```

Para el código en Rust, usamos su sistema integrado. Es necesario correrlo señalando el toolchain `nightly` y usar la opción `--no-default-features`
```bash
rustup run nightly cargo test --no-default-features --
```

## Empaquetado
Por ahora vamos a probar [wheels](https://pythonwheels.com/)
```bash
rustup run nightly maturin build --release -i python3.5
```
