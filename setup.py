from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name='ESbackup',
    version='1.0.0',
    description='Backup de indices en Elasticsearch 6.x',
    keywords='backup python rust',
    author='Alexander Ortíz',
    author_email='vtacius@gmail.com',
    license='GPLv3',

    packages=["esbackup"],
    rust_extensions=[RustExtension("esbackup.esbackup", binding=Binding.PyO3)],
    # rust extensions are not zip safe, just like C-extensions.
    zip_safe=False,

    install_requires=["requests"],

    test_suite="pytest",

    entry_points = {
        'console_scripts': ['esbackup=esbackup.cli:main']
        },

)

