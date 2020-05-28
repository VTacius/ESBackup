# ESBackup
Backup de indices en Elasticsearch 6.x

El script tiene como misión dejar el servidor siempre disponible; para lo cual procura mucho la cuestión del espacio

Para usar este script como la herramienta de backup, basta con instalar y verificar que el nombre de los indices activos debe ser {nombre\_indice}-activo-yyy.mm.dd; y el de los backup, pues {nombre\_indice}-backup-yyy.mm.dd

## Instalacion
Por ahora, la distribución destino es Debian 9. (Ni siquiera 10) Así que es el único paquete creado. Para otros destinos, tendré que hacerse a mano
Aunque parece que viene ya instalado en muchas distribuciones, el único paquete necesario para que esto funcione es `Request`

```bash
# Para Fedora
dnf install python3-requests

# Para Debian
apt install python3-requests

# El paquete propiamente se instala asi:
tar xzvf dist/esbackup-1.0.linux-x86_64.tar.gz --strip-components=7 -C /usr/local/
```

## Desarrollo.
Ya que el destino final de esta aplicación es Debian, he cuidado que las versiones a usar sean compatibles con las disponibles en 9.x, que tiene instalada la versión 3.5 de python. 

```bash
pipenv --python python35 shell
pipenv install
pipenv install --dev
```

En Fedora, un par de paquetes son necesarios (TODO: ¿En verdad lo son?)

```bash
dnf install python3-devel 
```

## Linting
Este es un trabajo en proceso. El código funciona a este momento, pero aspiro a que este realmente bien escrito

```bash
flake8 --ignore E501,E266 esbackup/
pylint esbackup/
```

## Test
Hay dos grupos de test (Por lo pronto, un poco redundantes) que deben correrse desde la raíz del repositorio:

Para el código python, usamos `pytest`; en forma de módulo, lo que permite ahorrar muchos dolores de cabeza. Antes de correrlos, debemos aseguranos de tener el módulo hecho en Rust
```bash
# maturin es genial pero queda fuera por el momento
# rustup run nightly maturin develop --release 
rustup run nightly python setup.py develop
python -m pytest esbackup/test/
```

Para el código en Rust, usamos su sistema integrado. Es necesario correrlo señalando el toolchain `nightly` y usar la opción `--no-default-features`
```bash
rustup run nightly cargo test --no-default-features --
```

## Empaquetado
El paquete lo creamos con [setuptools-rust](https://pypi.org/project/setuptools-rust/), que es más feo que maturin, pero permite ser un poco versatil
```bash
rustup run nightly python setup.py bdist
```
