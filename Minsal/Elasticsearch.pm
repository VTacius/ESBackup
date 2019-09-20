package Minsal::Elasticsearch;

use v5.10;
use strict;
use warnings;
use Exporter;
use vars qw($VERSION @ISA @EXPORT @EXPORT_OK %EXPORT_TAGS);

$VERSION     = 0.20;
@ISA         = qw(Exporter);
@EXPORT      = qw(&peticiona &respondedor &procesamiento &valida_respuesta &modo_escritura);
@EXPORT_OK   = qw(&peticiona &respondedor &procesamiento &valida_respuesta &modo_escritura);
%EXPORT_TAGS = (DEFAULT => [qw(&peticiona &respondedor &procesamiento &valida_respuesta &modo_escritura)]);

require LWP::UserAgent;
use Encode qw(encode_utf8);
use JSON::XS qw(encode_json decode_json);
use Data::Dumper;

my $endpoint = 'http://127.0.0.1:9200';
my $header = ['Content-Type' => 'application/json; charset=UTF-8'];
my $user_agent = 'MINSAL/0.2';
my $timeout = 2 * 60 * 60; 

my $verbosidad = "quiet";

my %datos_modo_escritura = (
    "index" => {
        "blocks" => {
            "read_only" => \0,
            "read_only_allow_delete" => \0
        },
    }
);

my %datos_index_block_write = ( 
    settings => {
        index => {
            blocks => {
                write => 'true'
            }
        }
    }
);

my %datos_shrink = (
  settings => {
      'index' => {
          number_of_replicas => 0,
          number_of_shards => 1,
          codec => 'best_compression'
      }
  } 
);

sub peticiona {
    my ($method, $uri, %data) = @_;

    my $url = $endpoint . $uri;
    
    my %pre_data = %data ? %data : ();
    
    my $data_encoded = encode_utf8(encode_json(\%pre_data));
    my $pet = HTTP::Request->new($method, $url, $header, $data_encoded);

    return $pet
}

sub respondedor {
    my $request = shift;

    my $ua = LWP::UserAgent->new();
    $ua->timeout( $timeout );
    $ua->agent($user_agent);

    my $response = $ua->request($request);

    if ($response->is_success){
        return $response->content; 
    } else {
        printf ("ERROR: %s al procesar %s\n", $response->status_line, $request->uri );
        exit 0;
    }

}

sub valida_respuesta {
    my $contenido = shift;
    my $data = decode_json($contenido);
    if (defined $data->{'acknowledged'}){
        print "Operación exitosa\n";
        return 1;
    }elsif($data->{'_shards'} && $data->{'_shards'}->{'successful'}){
        print "Operación exitosa\n";
        return 1;
    } else {
        exit 0;
    }
}

sub shrinkear {

    my $indice = shift;
    my $indice_backup = shift;

    ## Primero lo volvemos de solo lectura
    print "$indice: Le volvemos de solo lectura\n";
    my $peticion = peticiona('PUT', "/$indice/_settings", %datos_index_block_write);
    valida_respuesta(respondedor($peticion));
    
    ## Después, le reducimos
    print "$indice: Le reducimos\n";
    $peticion = peticiona('POST', "/$indice/_shrink/$indice_backup", %datos_shrink);
    valida_respuesta(respondedor($peticion));
};

sub mergear {

    my $indice_backup = shift;
    
    ## Antes de forzar el merge, volvemos de sólo lectura
    print "$indice_backup: Configuramos como sólo lectura antes de su merge\n";
    my $peticion = peticiona('PUT', "/$indice_backup/_settings", %datos_index_block_write);
    valida_respuesta(respondedor($peticion));
    
    ## Forzamos el merge
    print "$indice_backup: Forzamos el merge\n";
    $peticion = peticiona('POST', "/$indice_backup/_forcemerge?max_num_segments=1"); 
    valida_respuesta(respondedor($peticion));
    
}

sub modo_escritura {
    my $peticion = peticiona('PUT', "/_all/_settings", %datos_modo_escritura);
    valida_respuesta(respondedor($peticion));
}

sub procesamiento {
    my $indice = shift;
    my $indice_backup = $indice =~ s/activo/backup/r;
    my $mergear = shift;
    $mergear = $mergear ? $mergear : 0;

    # Reducimos el número de shrinks disponibles para el índice. 
    shrinkear($indice, $indice_backup);    
  
    # Forzamos un merge, con lo que realmente volvemos más pequeño al indice 
    if ($mergear){
        mergear($indice_backup); 
    }

    ## Borramos el original
    print "$indice: Borramos el original\n";
    my $peticion = peticiona('DELETE', "/$indice"); 
    valida_respuesta(respondedor($peticion));
}

