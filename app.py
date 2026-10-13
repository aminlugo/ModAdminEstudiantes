import os
import json
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from werkzeug.utils import secure_filename

# INICIALIZACIÓN DE LA APLICACIÓN FLASK
app = Flask(__name__)
app.secret_key = '5hT7mK9qP4zX8nL2vF1aS6dJ3rW0yC'

# Inicializar Firebase Admin SDK de forma robusta
if not firebase_admin._apps:
    firebase_json_env = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    if firebase_json_env:
        # Carga desde variable de entorno (para producción / Render)
        cred_dict = json.loads(firebase_json_env)
        cred = credentials.Certificate(cred_dict)
    else:
        # Carga desde archivo local físico (para desarrollo en tu PC)
        PATH_CREDENCIALES = 'param_bd.json'
        cred = credentials.Certificate(PATH_CREDENCIALES)
    
    firebase_admin.initialize_app(cred)

# Definición global de la base de datos Firestore y la colección
db = firestore.client()
COLECCION = 'estudiantes'

@app.route('/')
def index():
    busqueda = request.args.get('busqueda', '').strip()
    ordenar_por = request.args.get('ordenar', 'numeroIdentificacion')
    direccion = request.args.get('dir', 'asc')
    
    # Parámetros de paginación
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    try:
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        per_page = 10

    lista_estudiantes = []
    try:
        estudiantes_ref = db.collection(COLECCION)
        docs = estudiantes_ref.get()
        for doc in docs:
            data = doc.to_dict()
            if data:
                data['id_doc'] = doc.id
                lista_estudiantes.append(data)
    except Exception as e:
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

    # Calcular total de registros y páginas para la paginación
    total_registros = len(lista_estudiantes)
    total_paginas = max(1, (total_registros + per_page - 1) // per_page)
    
    if page > total_paginas:
        page = total_paginas
    if page < 1:
        page = 1

    # Aplicar corte de paginación
    start = (page - 1) * per_page
    end = start + per_page
    estudiantes_paginados = lista_estudiantes[start:end]

    return render_template(
        'index.html',
        estudiantes=estudiantes_paginados,
        busqueda=busqueda,
        ordenar_actual=ordenar_por,
        dir_actual=direccion,
        page=page,
        per_page=per_page,
        total_paginas=total_paginas,
        total_registros=total_registros
    )

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            num_id = request.form['numeroIdentificacion'].strip()
            if not num_id:
                flash('El número de identificación es obligatorio.', 'danger')
                return redirect(url_for('agregar'))
            
            doc_ref = db.collection(COLECCION).document(num_id)
            if doc_ref.get().exists:
                flash(f'Ya existe un registro registrado con el número de identificación {num_id}.', 'warning')
                return redirect(url_for('agregar'))
            
            nuevo_registro = {
                'numeroIdentificacion': int(num_id),
                'nombres': request.form['nombres'].strip(),
                'apellidos': request.form['apellidos'].strip(),
                'email': request.form['email'].strip(),
                'genero': request.form.get('genero', '').strip(),
                'edad': int(request.form['edad']) if request.form['edad'] else 0,
                'carrera': request.form.get('carrera', '').strip(),
                'semestre': int(request.form['semestre']) if request.form['semestre'] else 0,
                'modalidad': request.form.get('modalidad', '').strip(),
                'universidad': request.form.get('universidad', '').strip()
            }
            doc_ref.set(nuevo_registro)
            flash('Estudiante agregado exitosamente a Cloud Firestore.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error al registrar el estudiante: {str(e)}', 'danger')
            return redirect(url_for('agregar'))
            
    return render_template('agregar.html')

@app.route('/cargar_csv', methods=['POST'])
def cargar_csv():
    if 'archivo_csv' not in request.files:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('index'))
    
    archivo = request.files['archivo_csv']
    if archivo.filename == '':
        flash('El archivo no tiene un nombre válido.', 'danger')
        return redirect(url_for('index'))
        
    if archivo and archivo.filename.endswith('.csv'):
        filename = secure_filename(archivo.filename)
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        archivo.save(filepath)
        try:
            df = pd.read_csv(filepath, sep=';')
            CAMPOS_OBLIGATORIOS = ['numeroIdentificacion', 'email', 'nombres', 'apellidos']
            df = df.dropna(subset=CAMPOS_OBLIGATORIOS)
            cargados = 0
            omitidos = 0
            
            for _, row in df.iterrows():
                num_id = str(int(row['numeroIdentificacion']))
                val_carrera = row.get('carrera', row.get('maestria', ''))
                registro = {
                    'numeroIdentificacion': int(row['numeroIdentificacion']),
                    'nombres': str(row['nombres']).strip(),
                    'apellidos': str(row['apellidos']).strip(),
                    'email': str(row['email']).strip(),
                    'genero': str(row.get('genero', '')).strip(),
                    'edad': int(row.get('edad', 0)) if pd.notna(row.get('edad')) else 0,
                    'carrera': str(val_carrera).strip(),
                    'semestre': int(row.get('semestre', 0)) if pd.notna(row.get('semestre')) else 0,
                    'modalidad': str(row.get('modalidad', '')).strip(),
                    'universidad': str(row.get('universidad', '')).strip()
                }
                doc_ref = db.collection(COLECCION).document(num_id)
                if doc_ref.get().exists:
                    omitidos += 1
                else:
                    doc_ref.set(registro)
                    cargados += 1
                    
            flash(f'Carga exitosa: {cargados} registros guardados. {omitidos} omitidos por duplicidad.', 'success')
        except Exception as e:
            flash(f'Error al procesar el archivo CSV: {str(e)}', 'danger')
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
        return redirect(url_for('index'))
        
    flash('Por favor, cargue un archivo con formato CSV válido.', 'warning')
    return redirect(url_for('index'))

@app.route('/editar/<string:id_doc>', methods=['GET', 'POST'])
def editar(id_doc):
    doc_ref = db.collection(COLECCION).document(id_doc)
    if request.method == 'POST':
        datos_actualizados = {
            'nombres': request.form['nombres'],
            'apellidos': request.form['apellidos'],
            'email': request.form['email'],
            'genero': request.form['genero'],
            'edad': int(request.form['edad']),
            'carrera': request.form['carrera'],
            'semestre': int(request.form['semestre']),
            'modalidad': request.form['modalidad'],
            'universidad': request.form['universidad']
        }
        doc_ref.update(datos_actualizados)
        flash('Registro actualizado correctamente.', 'success')
        return redirect(url_for('index'))
        
    doc = doc_ref.get()
    if not doc.exists:
        flash('El registro no existe.', 'danger')
        return redirect(url_for('index'))
        
    estudiante = doc.to_dict()
    estudiante['id_doc'] = doc.id
    return render_template('editar.html', estudiante=estudiante)

@app.route('/eliminar/<string:id_doc>', methods=['POST'])
def eliminar(id_doc):
    db.collection(COLECCION).document(id_doc).delete()
    flash('Registro eliminado correctamente.', 'info')
    return redirect(url_for('index'))

@app.route('/eliminar_todos', methods=['POST'])
def eliminar_todos():
    try:
        estudiantes_ref = db.collection(COLECCION)
        docs = list(estudiantes_ref.stream())
        eliminados = 0
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            eliminados += 1
            if eliminados % 400 == 0:
                batch.commit()
                batch = db.batch()
        if eliminados % 400 != 0:
            batch.commit()
        flash(f'Se han eliminado {eliminados} registros exitosamente de la base de datos.', 'warning')
    except Exception as e:
        flash(f'Error al eliminar los registros: {str(e)}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)