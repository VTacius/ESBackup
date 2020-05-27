use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use std::collections::HashMap;

/// Suma el promedio de cada tipo de índices para obtener una estimación del espacio libre necesario para crear uno nuevo
#[pyfunction]
#[text_signature = "(tabla, muestra)"]
fn espacio_usado_indices(tabla: HashMap<&str, Vec<(&str, u128)>>, muestra: usize) -> PyResult<u128> {
    let resultado = tabla
        .values()
        .flat_map(|x| x[..muestra].to_vec())
        .fold(0, |a, x| a + x.1);

    Ok(resultado / muestra as u128)
}

/// Selecciona algunos indices de cada tipo, dejando un minimo_requerido
#[pyfunction]
#[text_signature = "(minimo_requerido, indices)"]
fn seleccionar_indices_a_respaldar<'a>(minimo_requerido: usize, indices: HashMap<&'a str, Vec<(&'a str, u128)>>) -> PyResult<Vec<&'a str>> {
    let respuesta: Vec<&str> = indices
        .values()
        .map(|x|{
            x.iter().skip(minimo_requerido).map(|x| x.0)
        })
        .flatten()
        .collect();
    Ok(respuesta)
}

/// Lista los índices que deben borrarse para dejar el espacio necesario en disco
#[pyfunction]
#[text_signature = "(minimo_requerido_indices, espacio_libre_requerido, indices)"]
fn seleccionar_indices_a_borrar<'a>(minimo_requerido_indices: usize, espacio_libre_requerido: u128, indices: HashMap<&'a str, Vec<(&'a str, u128)>>) -> Vec<&'a str>{
    let numero_tipos = indices.keys().len();

    let mut resultado: Vec<&str> = vec!();

    let mut iterante: usize = 0;
    let mut seleccion: usize = 0;

    let mut espacio_liberado: u128 = 0;
    let mut temp: u128;

    for (_, v) in indices.iter().cycle() {
        temp = espacio_liberado;

        // cada indice puede tener diferente tamaño
        let requerido = v.len() - minimo_requerido_indices;
        // Tengo que aceptar que tengo un problema: Salimos inmediatamente, no podemos agregar otro,
        // aunque fuera posible esperar a que otra lista aún tuviera
        if requerido > seleccion {
            resultado.push(v[seleccion].0);
            espacio_liberado += v[seleccion].1;
        }

        if espacio_liberado == temp || espacio_liberado >= espacio_libre_requerido{
            break;
        }

        iterante += 1;
        seleccion = if (iterante % numero_tipos) == 0 { seleccion + 1 } else { seleccion };
    }

    resultado
}

/// Encuentra un directorio montado de entre un diccionario que representa los montajes en el sistema
#[pyfunction]
#[text_signature = "(directorio, esquema_montaje, /)"]
fn buscar_punto_montaje(directorio: &str, esquema_montaje: HashMap<String, String>) -> PyResult<String> {
    let posibles_puntos_montajes: Vec<String> = directorio
        .split("/")
        .filter(|x| *x != "")
        .scan(String::new(), |estado, componente| {
            *estado = format!("{}/{}", estado, componente);
            Some(estado.clone())
        })
        .collect::<Vec<String>>();

    let punto_de_montaje: String = posibles_puntos_montajes
        .iter()
        .filter(|x|{
            return match esquema_montaje.get(&**x) {
                Some(_) => true,
                None => false
            }
        })
        .fold(String::from("/"), |a, x|{
            if x.len() > a.len() { x.clone() } else { a }
        });

    Ok(punto_de_montaje.clone())
}

fn parsear_linea(linea: &str) -> Option<(&str, &str, u128)> {
    let separador = linea.find(" ").unwrap_or(0);
    let (nombre, tamanio) = linea.split_at(separador);
    let itenizador = nombre.find("-").unwrap_or(0);
    let etiqueta = nombre.get(..itenizador).unwrap_or("");
    match tamanio.trim().parse::<u128>() {
        Ok(t) => Some((&etiqueta, nombre, t)),
        Err(_) => None
    }

}

/// Dada una lista de índices, las agrupa en un diccionario de tipos según la primera parte del nombre
#[pyfunction]
#[text_signature = "(contenido)"]
fn clasificar_indices(contenido: Vec<&str>) -> PyResult<HashMap<&str, Vec<(&str, u128)>>> {
    let resultado: Vec<(&str, &str, u128)> = contenido
        .into_iter()
        .filter_map(parsear_linea).collect();

    let mut contenido: HashMap<&str, Vec<(&str, u128)>> = HashMap::new();

    for (clave, nombre, tamanio) in resultado.into_iter() {
        if let Some(entrada) = contenido.get_mut(clave) {
            entrada.push((nombre, tamanio));
        } else {
            contenido.insert(clave, vec!((nombre, tamanio)));
        }
    }

    Ok(contenido)
}

/// Recopila varias funciones que consumían muchos recursos del sistema, y que tardaban mucho para un sistema como este
#[pymodule]
fn esbackup(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(clasificar_indices))?;
    m.add_wrapped(wrap_pyfunction!(buscar_punto_montaje))?;
    m.add_wrapped(wrap_pyfunction!(seleccionar_indices_a_borrar))?;
    m.add_wrapped(wrap_pyfunction!(espacio_usado_indices))?;
    m.add_wrapped(wrap_pyfunction!(seleccionar_indices_a_respaldar))?;
    Ok(())
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_espacio_usado_indices(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        assert_eq!(2000, espacio_usado_indices(indices, 2).unwrap())
    }

    #[test]
    fn test_espacio_usado_indices_caso(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        assert_eq!(2000, espacio_usado_indices(indices, 2).unwrap())
    }

    #[test]
    fn test_parser_linea(){
        let linea = "auditbeat-activo-2019.06.15     4226";
        assert_eq!(parsear_linea(linea), Some(("auditbeat", "auditbeat-activo-2019.06.15", 4226)));
    }

    #[test]
    fn test_parseador_none() {
        let linea = "auditbeatactivo201906.154226";
        assert_eq!(parsear_linea(linea), None);
    }

    #[test]
    fn test_parser_contenido(){
        let contenido =vec!(
            "auditbeat-activo-2019.06.09     9736",
            "auditbeat-activo-2019.06.10     4026",
            "auditbeat-activo-2019.06.12     5570",
            "squid-activo-2019.06.29        10117",
            "squid-activo-2019.06.30         7761",
            "squid-activo-2019.07.01        46727",
            "squidguard-activo-2019.05.08    7549",
            "squidguard-activo-2019.05.09    6406",
            "squidguard-activo-2019.05.10     916");

        let mut esperado = HashMap::new();
        esperado.insert("squid", vec!(("squid-activo-2019.06.29", 10117), ("squid-activo-2019.06.30", 7761), ("squid-activo-2019.07.01", 46727)));
        esperado.insert("auditbeat", vec!(("auditbeat-activo-2019.06.09", 9736), ("auditbeat-activo-2019.06.10", 4026), ("auditbeat-activo-2019.06.12", 5570)));
        esperado.insert("squidguard", vec!(("squidguard-activo-2019.05.08", 7549), ("squidguard-activo-2019.05.09", 6406), ("squidguard-activo-2019.05.10", 916)));
        let resultado = clasificar_indices(contenido).unwrap();
        assert_eq!(esperado, resultado);
    }

    #[test]
    fn test_buscar_punto_montaje() {
        let directorio = "/var/lib/elasticsearch";

        let mut montajes = HashMap::new();
        montajes.insert(String::from("/"), String::from("/dev/xvda2"));
        montajes.insert( String::from("/home"), String::from("/dev/xvda3"));
        montajes.insert( String::from("/var"), String::from("/dev/xvda4"));

        assert_eq!(buscar_punto_montaje(directorio, montajes).unwrap(), "/var")
    }

    #[test]
    fn test_buscar_punto_montaje_mas_cercano() {
        let directorio = "/var/lib/elasticsearch";

        let mut montajes = HashMap::new();
        montajes.insert(String::from("/"), String::from("/dev/xvda2"));
        montajes.insert( String::from("/home"), String::from("/dev/xvda3"));
        montajes.insert( String::from("/var"), String::from("/dev/xvda4"));
        montajes.insert( String::from("/var/lib/"), String::from("/dev/xvda5"));
        montajes.insert( String::from("/var/lib/elasticsearch"), String::from("/dev/xvda6"));

        assert_eq!(buscar_punto_montaje(directorio, montajes).unwrap(), "/var/lib/elasticsearch")
    }

    #[test]
    fn test_buscar_punto_montaje_predeterminado(){
        let directorio = "/var/lib/elasticsearch/";

        let mut montajes = HashMap::new();
        montajes.insert(String::from("/"), String::from("/dev/xvda2"));
        montajes.insert( String::from("/home"), String::from("/dev/xvda3"));

        assert_eq!(buscar_punto_montaje(directorio, montajes).unwrap(), "/")
    }

    #[test]
    fn test_seleccionar_indices_a_respaldar(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        let esperado = vec!["auditbeat-06.12", "auditbeat-06.13", "squid-07.01", "squid-07.02", "squidguard-05.10", "squidguard-05.11"];
        let mut resultado = seleccionar_indices_a_respaldar(2, indices).unwrap();
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_respaldar_variabilidad(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600), ("squid-07.03", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600)));

        let esperado = vec!["auditbeat-06.13", "squid-07.02", "squid-07.03"];
        let mut resultado = seleccionar_indices_a_respaldar(3, indices).unwrap();
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_borrar(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        let esperado = vec!["auditbeat-06.09", "squid-06.29", "squidguard-05.08"];
        let mut resultado = seleccionar_indices_a_borrar(2, 2000, indices);
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_borrar_4000(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        let esperado = vec!["auditbeat-06.09", "auditbeat-06.10", "squid-06.29", "squid-06.30", "squidguard-05.08", "squidguard-05.09"];
        let mut resultado = seleccionar_indices_a_borrar(2, 4000, indices);
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_borrar_6000_fallido(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        let esperado = vec!["auditbeat-06.09", "auditbeat-06.10", "squid-06.29", "squid-06.30", "squidguard-05.08", "squidguard-05.09"];
        let mut resultado = seleccionar_indices_a_borrar(2, 6000, indices);
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_borrar_6000(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800), ("squid-07.01", 700), ("squid-07.02", 600)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600), ("auditbeat-06.12", 500), ("auditbeat-06.13", 800)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600), ("squidguard-05.10", 800), ("squidguard-05.11", 700)));

        let esperado = vec!["auditbeat-06.09", "auditbeat-06.10", "auditbeat-06.12", "squid-06.29", "squid-06.30", "squid-07.01", "squidguard-05.08", "squidguard-05.09", "squidguard-05.10"];
        let mut resultado = seleccionar_indices_a_borrar(1, 6000, indices);
        resultado.sort();
        assert_eq!(resultado, esperado);

    }

    #[test]
    fn test_seleccionar_indices_a_borrar_insuficientes(){
        let mut indices = HashMap::new();
        indices.insert("squid", vec!(("squid-06.29", 500), ("squid-06.30", 800)));
        indices.insert("auditbeat", vec!(("auditbeat-06.09", 900), ("auditbeat-06.10", 600)));
        indices.insert("squidguard", vec!(("squidguard-05.08", 600), ("squidguard-05.09", 600)));

        let esperado: Vec<&str> = vec!();
        let mut resultado = seleccionar_indices_a_borrar(2, 6000, indices);
        resultado.sort();
        assert_eq!(resultado, esperado);

    }
}
