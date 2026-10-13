@app.route('/')
def index():
    busqueda = request.args.get('busqueda', '').strip()
    ordenar_por = request.args.get('ordenar', 'numeroIdentificacion')
    direccion = request.args.get('dir', 'asc')
    
    try:
        estudiantes_ref = db.collection(COLECCION)
        # Limitar opcionalmente para proteger la memoria en el plan gratuito (ej. máximo 500 registros)
        docs = estudiantes_ref.limit(500).stream()
        lista_estudiantes = []
        
        for doc in docs:
            data = doc.to_dict()
            if data:
                data['id_doc'] = doc.id
                lista_estudiantes.append(data)
    except Exception as e:
        lista_estudiantes = []
        flash(f'Error al conectar con la base de datos: {str(e)}', 'danger')
        
    # Filtrar localmente si el usuario ingresó un término de búsqueda
    if busqueda:
        lista_estudiantes = [
            e for e in lista_estudiantes 
            if busqueda.lower() in str(e.get('numeroIdentificacion', '')).lower() or
               busqueda.lower() in e.get('nombres', '').lower() or
               busqueda.lower() in e.get('apellidos', '').lower() or
               busqueda.lower() in e.get('email', '').lower() or
               busqueda.lower() in e.get('carrera', '').lower()
        ]
        
    # Ordenar la lista de estudiantes según la columna seleccionada
    reverse_order = (direccion == 'desc')
    try:
        lista_estudiantes = sorted(
            lista_estudiantes, 
            key=lambda x: (x.get(ordenar_por) is None, x.get(ordenar_por) if x.get(ordenar_por) is not None else ''), 
            reverse=reverse_order
        )
    except Exception:
        pass
        
    return render_template(
        'index.html', 
        estudiantes=lista_estudiantes, 
        busqueda=busqueda, 
        ordenar_actual=ordenar_por, 
        dir_actual=direccion
    )