#!/usr/bin/perl

use v5.10;
use Minsal::Fecha;
use Minsal::Elasticsearch;
use Data::Dumper;

if (not $#ARGV >= 1){
    say ("Falta el indice muestra: {nombre-indice}-*");
    exit;
}

my $patron_indice_activo = $ARGV[0];
my $patron_indice_backup = $patron_indice_activo =~ s/activo/backup/r;
my $limite_indices = $ARGV[1];
my $dias_anteriores = 1;

my $ahora = obtiene_fecha(time());
my $hoy = obtiene_timestamp($ahora);

say "################################################################################";
say "Iniciamos operaciones en $hoy para $patron_indice_activo";

## Buscamos TODOS aquellos indices ACTIVOS que tengan dos días de antiguedad
my $peticion = peticiona('GET', "/_cat/indices/$patron_indice_activo?s=index"); 
my $respuesta = respondedor($peticion);

sub info_indice {
    my $linea = shift;
    
    my ($health, $status, $index, $uuid, $shards, $copias, $documentos, $doc_borrados, $size, $size_primario) = split(/\s/, $linea);
    my ($tipo, $estado, $fecha) = split(/\-/, $index);

    return ($index, $fecha, $size);
};

foreach my $linea (split(/\n/, $respuesta)){
    my ($index, $fecha, $size) = info_indice($linea);

    my $antes = obtiene_timestamp($fecha);
    my $delta = diferencia_dias($hoy, $antes);
    
    if ($delta >= $dias_anteriores){
        procesamiento($index, 1);
        modo_escritura();
    } 
}

## Buscamos los índice a borrar 
my $peticion = peticiona('GET', "/_cat/indices/$patron_indice_backup?s=index:desc"); 
my $respuesta = respondedor($peticion);
my @indices;
foreach my $linea (split(/\n/, $respuesta)){
    my ($index, $fecha, $size) = info_indice($linea);
    push (@indices, $index);
}

my @borrables = splice (@indices, $limite_indices);
foreach $indice (@borrables){
    my $peticion = peticiona('DELETE', "/$indice"); 
    say "$indice: Borrando el indice";
    valida_respuesta(respondedor($peticion));
};

say "Terminamos operaciones en $hoy para $patron_indice_activo";
say "################################################################################";
