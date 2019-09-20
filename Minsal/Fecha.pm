package Minsal::Fecha;

use v5.10;
use strict;
use warnings;
use Exporter;
use vars qw($VERSION @ISA @EXPORT @EXPORT_OK %EXPORT_TAGS);

$VERSION     = 0.20;
@ISA         = qw(Exporter);
@EXPORT      = qw(&obtiene_timestamp &obtiene_fecha &diferencia_dias);
@EXPORT_OK   = qw(&obtiene_timestamp &obtiene_fecha &diferencia_dias);
%EXPORT_TAGS = (DEFAULT => [qw(&obtiene_timestamp &obtiene_fecha &diferencia_dias)]);

use POSIX;

sub obtiene_timestamp {
    my $fecha = shift;
    my ($anio, $mes, $dia) = split(/\./, $fecha);
    $anio = $anio- 1900;
    $mes = $mes - 1;
    return mktime(0, 0, 0, $dia, $mes, $anio);
}

sub obtiene_fecha {
    my $ts = shift;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($ts);
    $year = $year + 1900;
    $mon = $mon + 1; 
    return "$year.$mon.$mday"; 
}

sub diferencia_dias {
    my ($hoy, $antes) = @_;
    my $delta = $hoy - $antes;
    my $minimo = 24 * 60 * 60;
    return $delta / $minimo;
}

