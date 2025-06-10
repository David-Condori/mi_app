from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mysql.connector
from datetime import datetime
from geopy.geocoders import Nominatim
import heapq

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesario para gestionar sesiones


host = 'Davidcondori.mysql.pythonanywhere-services.com'
user = 'Davidcondori'
password = 'zapatito123'
database = 'Davidcondori$coboce_sys'

def get_db_connection():
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        clave = request.form['password']

        if not username or not clave:
            return render_template('login.html', error="Por favor ingrese tanto el nombre como la cédula.")

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # 1. Intentar login como administrador o supervisor desde la tabla Usuarios
            cursor.execute("""
                SELECT * FROM Usuarios WHERE username = %s AND clave = %s
            """, (username, clave))
            usuario = cursor.fetchone()

            if usuario:
                session['rol'] = usuario['rol']
                session['usuario'] = usuario['username']

                if usuario['rol'] == 'administrador':
                    return redirect(url_for('dashboard'))
                elif usuario['rol'] == 'supervisor':
                    return redirect(url_for('panel_supervisor'))

            # 2. Si no fue usuario, intentar login como conductor
            cursor.execute("""
                SELECT * FROM Conductores WHERE nombre = %s AND cedula = %s
            """, (username, clave))
            conductor = cursor.fetchone()

            if conductor:
                session['rol'] = 'conductor'
                session['conductor_id'] = conductor['id_conductor']
                session['conductor_nombre'] = conductor['nombre']
                return redirect(url_for('panel_conductor'))

            # Si no encontró nada
            return render_template('login.html', error="Credenciales incorrectas.")

        except mysql.connector.Error as err:
            print(f"Error de base de datos: {err}")
            return f"Error de base de datos: {err}"

        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session or session.get('rol') != 'administrador':
        return redirect(url_for('login'))
    return render_template('dashboard.html')



# ============================ VEHÍCULOS ============================

@app.route('/vehiculos')
def vehiculos():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Vehiculos")
        vehiculos_data = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('vehiculos.html', vehiculos=vehiculos_data)
    except mysql.connector.Error as err:
        return f"Error al obtener vehículos: {err}"

@app.route('/vehiculos/agregar', methods=['GET', 'POST'])
def agregar_vehiculo():
    if request.method == 'POST':
        placa = request.form['placa']
        modelo = request.form['modelo']
        tipo_vehiculo = request.form['tipo_vehiculo']
        capacidad = request.form['capacidad']
        estado = request.form['estado']
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO Vehiculos (placa, modelo, tipo_vehiculo, capacidad, estado)
                VALUES (%s, %s, %s, %s, %s)
            """, (placa, modelo, tipo_vehiculo, capacidad, estado))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('vehiculos'))
        except mysql.connector.Error as err:
            return f"Error al agregar vehículo: {err}"
    return render_template('agregar_vehiculo.html')

@app.route('/vehiculos/editar/<int:id_vehiculo>', methods=['GET', 'POST'])
def editar_vehiculo(id_vehiculo):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Vehiculos WHERE id_vehiculo = %s", (id_vehiculo,))
        vehiculo = cursor.fetchone()
        if request.method == 'POST':
            placa = request.form['placa']
            modelo = request.form['modelo']
            tipo_vehiculo = request.form['tipo_vehiculo']
            capacidad = request.form['capacidad']
            estado = request.form['estado']
            cursor.execute("""
                UPDATE Vehiculos
                SET placa = %s, modelo = %s, tipo_vehiculo = %s, capacidad = %s, estado = %s
                WHERE id_vehiculo = %s
            """, (placa, modelo, tipo_vehiculo, capacidad, estado, id_vehiculo))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('vehiculos'))
        cursor.close()
        connection.close()
        return render_template('editar_vehiculo.html', vehiculo=vehiculo)
    except mysql.connector.Error as err:
        return f"Error al editar vehículo: {err}"

@app.route('/vehiculos/eliminar/<int:id_vehiculo>', methods=['POST'])
def eliminar_vehiculo(id_vehiculo):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Vehiculos WHERE id_vehiculo = %s", (id_vehiculo,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('vehiculos'))
    except mysql.connector.Error as err:
        return f"Error al eliminar vehículo: {err}"

# ============================ CONDUCTORES ============================

@app.route('/conductores')
def conductores():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Conductores")
        conductores_data = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('conductores.html', conductores=conductores_data)
    except mysql.connector.Error as err:
        return f"Error al obtener conductores: {err}"

@app.route('/conductores/agregar', methods=['GET', 'POST'])
def agregar_conductor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        cedula = request.form['cedula']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        licencia = request.form['licencia']
        estado = request.form['estado']
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO Conductores (nombre, apellido_paterno, apellido_materno, cedula, telefono, direccion, licencia, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nombre, apellido_paterno, apellido_materno, cedula, telefono, direccion, licencia, estado))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('conductores'))
        except mysql.connector.Error as err:
            return f"Error al agregar conductor: {err}"
    return render_template('agregar_conductor.html')

@app.route('/conductores/editar/<int:id_conductor>', methods=['GET', 'POST'])
def editar_conductor(id_conductor):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Conductores WHERE id_conductor = %s", (id_conductor,))
        conductor = cursor.fetchone()
        if request.method == 'POST':
            nombre = request.form['nombre']
            apellido_paterno = request.form['apellido_paterno']
            apellido_materno = request.form['apellido_materno']
            cedula = request.form['cedula']
            telefono = request.form['telefono']
            direccion = request.form['direccion']
            licencia = request.form['licencia']
            estado = request.form['estado']
            cursor.execute("""
                UPDATE Conductores
                SET nombre = %s, apellido_paterno = %s, apellido_materno = %s, cedula = %s, telefono = %s, direccion = %s, licencia = %s, estado = %s
                WHERE id_conductor = %s
            """, (nombre, apellido_paterno, apellido_materno, cedula, telefono, direccion, licencia, estado, id_conductor))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('conductores'))
        cursor.close()
        connection.close()
        return render_template('editar_conductor.html', conductor=conductor)
    except mysql.connector.Error as err:
        return f"Error al editar conductor: {err}"

@app.route('/conductores/eliminar/<int:id_conductor>', methods=['POST'])
def eliminar_conductor(id_conductor):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Conductores WHERE id_conductor = %s", (id_conductor,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('conductores'))
    except mysql.connector.Error as err:
        return f"Error al eliminar conductor: {err}"

# ============================ RUTAS ============================

@app.route('/rutas')
def rutas():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Rutas")
        rutas_data = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('rutas.html', rutas=rutas_data)
    except mysql.connector.Error as err:
        return f"Error al obtener rutas: {err}"

@app.route('/rutas/agregar', methods=['GET', 'POST'])
def agregar_ruta():
    if request.method == 'POST':
        origen = request.form['origen']
        destino = request.form['destino']
        distancia = request.form['distancia']
        tiempo_estimado = request.form.get('tiempo_estimado')
        zona = request.form.get('zona')
        latitud_destino = request.form.get('latitud_destino')
        longitud_destino = request.form.get('longitud_destino')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO Rutas (origen, destino, distancia, tiempo_estimado, zona, latitud_destino, longitud_destino)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (origen, destino, distancia, tiempo_estimado, zona, latitud_destino, longitud_destino))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('rutas'))
        except mysql.connector.Error as err:
            return f"Error al agregar ruta: {err}"

    return render_template('agregar_ruta.html')

@app.route('/rutas/editar/<int:id_ruta>', methods=['GET', 'POST'])
def editar_ruta(id_ruta):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Rutas WHERE id_ruta = %s", (id_ruta,))
        ruta = cursor.fetchone()
        if request.method == 'POST':
            origen = request.form['origen']
            destino = request.form['destino']
            distancia = request.form['distancia']
            cursor.execute("""
                UPDATE Rutas
                SET origen = %s, destino = %s, distancia = %s
                WHERE id_ruta = %s
            """, (origen, destino, distancia, id_ruta))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('rutas'))
        cursor.close()
        connection.close()
        return render_template('editar_ruta.html', ruta=ruta)
    except mysql.connector.Error as err:
        return f"Error al editar ruta: {err}"

@app.route('/rutas/eliminar/<int:id_ruta>', methods=['POST'])
def eliminar_ruta(id_ruta):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Rutas WHERE id_ruta = %s", (id_ruta,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('rutas'))
    except mysql.connector.Error as err:
        return f"Error al eliminar ruta: {err}"

@app.route('/seguimiento')
def seguimiento():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Traer entregas activas (JOIN con las tablas necesarias)
        cursor.execute("""
            SELECT
                c.id_conductor,
                c.nombre AS nombre_conductor,
                v.placa,
                r.origen,
                r.destino
            FROM Entregas e
            INNER JOIN Asignaciones_Rutas ar ON e.id_asignacion = ar.id_asignacion
            INNER JOIN Conductores c ON ar.id_conductor = c.id_conductor
            INNER JOIN Vehiculos v ON ar.id_vehiculo = v.id_vehiculo
            INNER JOIN Rutas r ON ar.id_ruta = r.id_ruta
            WHERE e.estado_entrega != 'completado'
        """)

        entregas = cursor.fetchall()

        return render_template('seguimiento.html', entregas=entregas)

    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")
        return f"Error de base de datos: {err}"

    finally:
        cursor.close()
        connection.close()


@app.route('/api/ubicaciones')
def ubicaciones():
    try:
        # Conectar a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obtener todas las ubicaciones de los vehículos (latitud, longitud, placa, id_vehiculo)
        cursor.execute("SELECT id_vehiculo, latitud_actual, longitud_actual, placa FROM Vehiculos WHERE latitud_actual IS NOT NULL AND longitud_actual IS NOT NULL")
        vehiculos = cursor.fetchall()

        # Cerrar la conexión a la base de datos
        cursor.close()
        connection.close()

        # Devolver los datos en formato JSON
        return jsonify(vehiculos)
    except mysql.connector.Error as err:
        return jsonify({"error": f"Error al obtener ubicaciones: {err}"}), 500

@app.route('/api/vehiculos')
def api_vehiculos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_vehiculo, placa FROM Vehiculos WHERE estado = 'Habilitado'")
        vehiculos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(vehiculos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conductores')
def api_conductores():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_conductor, nombre, apellido_paterno FROM Conductores WHERE estado = 'Habilitado'")
        conductores = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(conductores)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rutas')
def api_rutas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_ruta, origen, destino FROM Rutas")
        rutas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rutas)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/panel_supervisor')
def panel_supervisor():
    # Verificamos si el usuario está autenticado y tiene rol de supervisor
    if 'usuario' not in session or session.get('rol') != 'supervisor':
        return redirect(url_for('login'))

    # Mostrar la vista del panel del supervisor
    return render_template('panel_supervisor.html')


@app.route('/panel_conductor')
def panel_conductor():
    if 'rol' not in session or session['rol'] != 'conductor':
        return redirect(url_for('panel_conductor', mensaje='reporte_enviado'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        conductor_id = session['conductor_id']

        # Obtener entregas asignadas al conductor
        cursor.execute("""
            SELECT e.id_entrega, e.fecha_entrega, e.estado_entrega,
                   c.id_conductor,
                   c.nombre AS nombre_conductor,
                   v.placa,
                   r.origen, r.destino,
                   r.latitud_origen, r.longitud_origen,
                   r.latitud_destino, r.longitud_destino
            FROM Entregas e
            JOIN Asignaciones_Rutas a ON e.id_asignacion = a.id_asignacion
            JOIN Conductores c ON a.id_conductor = c.id_conductor
            JOIN Vehiculos v ON a.id_vehiculo = v.id_vehiculo
            JOIN Rutas r ON a.id_ruta = r.id_ruta
            WHERE a.id_conductor = %s
            ORDER BY e.fecha_entrega DESC
        """, (conductor_id,))
        entregas = cursor.fetchall()

        # Rutas para el mapa -> SOLO las rutas con entrega activa
        cursor.execute("""
            SELECT DISTINCT r.*
            FROM Asignaciones_Rutas a
            JOIN Rutas r ON a.id_ruta = r.id_ruta
            JOIN Entregas e ON a.id_asignacion = e.id_asignacion
            WHERE a.id_conductor = %s
            AND e.estado_entrega != 'completado'
        """, (conductor_id,))
        rutas = cursor.fetchall()

        # Obtener respuestas del supervisor
        cursor.execute("""
             SELECT ns.mensaje_respuesta AS mensaje_respuesta, ns.fecha_respuesta
             FROM RespuestasSupervisor ns
             JOIN Notificaciones n ON ns.id_notificacion = n.id_notificacion
             WHERE n.id_conductor = %s
             ORDER BY ns.fecha_respuesta DESC
        """, (conductor_id,))
        respuestas = cursor.fetchall()

        return render_template('panel_conductor.html', entregas=entregas, rutas=rutas, respuestas=respuestas)

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return f"Error en la base de datos: {err}"

    finally:
        cursor.close()
        connection.close()


@app.route('/reportar_incidente/<int:id_entrega>', methods=['POST'])
def reportar_incidente(id_entrega):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE Entregas
            SET estado_entrega = 'Incidente Reportado'
            WHERE id_entrega = %s
        """, (id_entrega,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('panel_conductor'))
    except mysql.connector.Error as err:
        return f"Error al reportar incidente: {err}"


@app.route('/asignar_entrega', methods=['GET', 'POST'])
def asignar_entrega():
    success_message = None
    error_message = None

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    geolocator = Nominatim(user_agent="coboce_tesis_rutas/1.0 (david.condori@estudiante.unifranz.edu.bo)")

    if request.method == 'POST':
        if 'accion' in request.form:
            entrega_id = request.form['entrega_id']
            accion = request.form['accion']

            if accion == 'eliminar':
                try:
                    cursor.execute("DELETE FROM Entregas WHERE id_entrega = %s", (entrega_id,))
                    connection.commit()
                    success_message = "Entrega eliminada correctamente."
                except Exception as e:
                    error_message = f"Error al eliminar entrega: {e}"

            elif accion == 'modificar':
                cursor.close()
                connection.close()
                return redirect(url_for('modificar_entrega', id_entrega=entrega_id))

        else:
            conductor_id = request.form['conductor_id']
            vehiculo_id = request.form['vehiculo_id']
            ruta_id = request.form['ruta_id']

            if not conductor_id or not vehiculo_id or not ruta_id:
                error_message = "Todos los campos son obligatorios."
            else:
                try:
                    # Verificar si la ruta ya tiene coordenadas
                    cursor.execute("SELECT * FROM Rutas WHERE id_ruta = %s", (ruta_id,))
                    ruta = cursor.fetchone()

                    if ruta:
                        lat_o, lon_o = ruta['latitud_origen'], ruta['longitud_origen']
                        lat_d, lon_d = ruta['latitud_destino'], ruta['longitud_destino']

                        # Si faltan coordenadas, tratamos de obtenerlas automáticamente
                        if not all([lat_o, lon_o]):
                            location = geolocator.geocode(ruta['origen'])
                            if location:
                                lat_o = location.latitude
                                lon_o = location.longitude
                                cursor.execute("""
                                    UPDATE Rutas SET latitud_origen = %s, longitud_origen = %s
                                    WHERE id_ruta = %s
                                """, (lat_o, lon_o, ruta_id))

                        if not all([lat_d, lon_d]):
                            location = geolocator.geocode(ruta['destino'])
                            if location:
                                lat_d = location.latitude
                                lon_d = location.longitude
                                cursor.execute("""
                                    UPDATE Rutas SET latitud_destino = %s, longitud_destino = %s
                                    WHERE id_ruta = %s
                                """, (lat_d, lon_d, ruta_id))

                    # Insertar asignación
                    cursor.execute("""
                        INSERT INTO Asignaciones_Rutas (id_conductor, id_vehiculo, id_ruta, fecha_asignacion, estado_asignacion)
                        VALUES (%s, %s, %s, CURDATE(), 'pendiente')
                    """, (conductor_id, vehiculo_id, ruta_id))
                    id_asignacion = cursor.lastrowid

                    # Insertar entrega
                    cursor.execute("""
                        INSERT INTO Entregas (id_asignacion, fecha_entrega, estado_entrega)
                        VALUES (%s, CURDATE(), 'pendiente')
                    """, (id_asignacion,))
                    connection.commit()
                    success_message = "Entrega asignada exitosamente."
                except Exception as e:
                    connection.rollback()
                    error_message = f"Error al asignar entrega: {e}"

    # Datos para el formulario
    cursor.execute("SELECT id_conductor, nombre, apellido_paterno, apellido_materno FROM Conductores")
    conductores = cursor.fetchall()

    cursor.execute("SELECT id_vehiculo, placa, tipo_vehiculo FROM Vehiculos")
    vehiculos = cursor.fetchall()

    cursor.execute("SELECT id_ruta, origen, destino FROM Rutas")
    rutas = cursor.fetchall()

    # Entregas existentes
    cursor.execute("""
        SELECT
            e.id_entrega, e.fecha_entrega, e.estado_entrega,
            c.nombre, c.apellido_paterno, c.apellido_materno,
            v.placa, v.tipo_vehiculo,
            r.origen, r.destino
        FROM Entregas e
        INNER JOIN Asignaciones_Rutas ar ON e.id_asignacion = ar.id_asignacion
        INNER JOIN Conductores c ON ar.id_conductor = c.id_conductor
        INNER JOIN Vehiculos v ON ar.id_vehiculo = v.id_vehiculo
        INNER JOIN Rutas r ON ar.id_ruta = r.id_ruta
        ORDER BY e.fecha_entrega DESC
    """)
    entregas_asignadas = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('asignar_entrega.html',
                           conductores=conductores,
                           vehiculos=vehiculos,
                           rutas=rutas,
                           entregas_asignadas=entregas_asignadas,
                           success_message=success_message,
                           error_message=error_message)


@app.route('/modificar_entrega/<int:id_entrega>', methods=['GET', 'POST'])
def modificar_entrega(id_entrega):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Obtener datos actuales de la entrega y asignación relacionada
    cursor.execute("""
        SELECT e.id_entrega, e.estado_entrega,
               ar.id_asignacion, ar.id_conductor, ar.id_vehiculo, ar.id_ruta
        FROM Entregas e
        INNER JOIN Asignaciones_Rutas ar ON e.id_asignacion = ar.id_asignacion
        WHERE e.id_entrega = %s
    """, (id_entrega,))
    entrega = cursor.fetchone()

    if not entrega:
        cursor.close()
        connection.close()
        return "Entrega no encontrada", 404

    if request.method == 'POST':
        nuevo_conductor = request.form['conductor_id']
        nuevo_vehiculo = request.form['vehiculo_id']
        nueva_ruta = request.form['ruta_id']
        nuevo_estado = request.form['estado_entrega']

        try:
            # Actualizar la tabla Asignaciones_Rutas
            cursor.execute("""
                UPDATE Asignaciones_Rutas
                SET id_conductor = %s, id_vehiculo = %s, id_ruta = %s
                WHERE id_asignacion = %s
            """, (nuevo_conductor, nuevo_vehiculo, nueva_ruta, entrega['id_asignacion']))

            # Actualizar la tabla Entregas
            cursor.execute("""
                UPDATE Entregas
                SET estado_entrega = %s
                WHERE id_entrega = %s
            """, (nuevo_estado, id_entrega))

            connection.commit()
            cursor.close()
            connection.close()

            return redirect(url_for('asignar_entrega'))

        except Exception as e:
            connection.rollback()
            cursor.close()
            connection.close()
            return f"Error al modificar entrega: {e}", 500

    # Obtener datos para los selects
    cursor.execute("SELECT id_conductor, nombre FROM Conductores")
    conductores = cursor.fetchall()

    cursor.execute("SELECT id_vehiculo, placa FROM Vehiculos")
    vehiculos = cursor.fetchall()

    cursor.execute("SELECT id_ruta, CONCAT(origen, ' → ', destino) AS ruta, id_ruta FROM Rutas")
    rutas = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('modificar_entrega.html',
                           entrega=entrega,
                           conductores=conductores,
                           vehiculos=vehiculos,
                           rutas=rutas)

@app.route('/ver_notificaciones')
def ver_notificaciones():
    # Quitar esta verificación si complica
    # if 'username' not in session or session['rol'] != 'supervisor':
    #     return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    consulta = """
        SELECT n.*, c.nombre, c.apellido_paterno, c.apellido_materno
        FROM Notificaciones n
        JOIN Conductores c ON n.id_conductor = c.id_conductor
        ORDER BY n.fecha_envio DESC
    """
    cursor.execute(consulta)
    notificaciones = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('ver_notificaciones.html', notificaciones=notificaciones)



@app.route('/reporte/<int:id_entrega>', methods=['GET', 'POST'])
def reporte(id_entrega):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            mensaje = request.form['mensaje']
            fecha_envio = datetime.now()

            # Obtener datos necesarios de la entrega
            cursor.execute("""
                SELECT e.id_conductor, e.origen, e.destino, e.placa, c.id_usuario
                FROM Entregas e
                JOIN Conductores c ON e.id_conductor = c.id_conductor
                WHERE e.id_entrega = %s
            """, (id_entrega,))
            entrega = cursor.fetchone()

            if not entrega:
                return "Entrega no encontrada"

            # Insertar en Notificaciones
            cursor.execute("""
                INSERT INTO Notificaciones (id_usuario, mensaje, fecha_envio, placa, origen, destino, id_conductor)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                entrega['id_usuario'],
                mensaje,
                fecha_envio,
                entrega['placa'],
                entrega['origen'],
                entrega['destino'],
                entrega['id_conductor']
            ))

            # Cambiar estado de entrega
            cursor.execute("""
                UPDATE Entregas SET estado_entrega = 'Incidente Reportado'
                WHERE id_entrega = %s
            """, (id_entrega,))

            connection.commit()
            return redirect(url_for('panel_conductor'))

        except Exception as e:
            print("ERROR:", e)
            return f"Error al enviar la notificación: {e}"

        finally:
            cursor.close()
            connection.close()

    return render_template('formulario_reporte.html', id_entrega=id_entrega)


@app.route('/enviar_notificacion', methods=['POST'])
def enviar_notificacion():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        id_entrega = request.form['id_entrega']
        mensaje = request.form['mensaje']
        fecha_envio = datetime.now()

        # Consultar datos necesarios de la entrega SIN USAR la tabla Usuarios
        cursor.execute("""
            SELECT
                e.id_entrega,
                ar.id_conductor,
                c.nombre,
                c.apellido_paterno,
                v.placa,
                r.origen,
                r.destino
            FROM Entregas e
            JOIN Asignaciones_Rutas ar ON e.id_asignacion = ar.id_asignacion
            JOIN Conductores c ON ar.id_conductor = c.id_conductor
            JOIN Vehiculos v ON ar.id_vehiculo = v.id_vehiculo
            JOIN Rutas r ON ar.id_ruta = r.id_ruta
            WHERE e.id_entrega = %s
        """, (id_entrega,))
        entrega = cursor.fetchone()

        if not entrega:
            return "Entrega no encontrada"

        # Insertar la notificación (usando id_conductor, sin id_usuario)
        cursor.execute("""
            INSERT INTO Notificaciones (mensaje, fecha_envio, placa, origen, destino, id_conductor)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            mensaje,
            fecha_envio,
            entrega['placa'],
            entrega['origen'],
            entrega['destino'],
            entrega['id_conductor']
        ))

        # Actualizar estado de la entrega
        cursor.execute("""
            UPDATE Entregas
            SET estado_entrega = 'Incidente Reportado'
            WHERE id_entrega = %s
        """, (id_entrega,))

        connection.commit()

        # Redirigir con mensaje de éxito en la URL
        return redirect(url_for('panel_conductor', mensaje='reporte_enviado'))

    except Exception as e:
        print("ERROR AL ENVIAR NOTIFICACIÓN:", e)
        return f"Error al enviar la notificación: {e}"

    finally:
        cursor.close()
        connection.close()

@app.route('/eliminar_notificacion/<int:id_notificacion>', methods=['POST'])
def eliminar_notificacion(id_notificacion):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM Notificaciones WHERE id_notificacion = %s", (id_notificacion,))
        connection.commit()
        return redirect(url_for('ver_notificaciones'))  # Ajusta esto al nombre real de tu ruta
    except Exception as e:
        print("Error al eliminar notificación:", e)
        return "Ocurrió un error al eliminar la notificación"
    finally:
        cursor.close()
        connection.close()



@app.route('/marcar_leido/<int:id_notificacion>', methods=['POST'])
def marcar_leido(id_notificacion):
    conexion = get_db_connection()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE Notificaciones SET leido = 1 WHERE id_notificacion = %s", (id_notificacion,))
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for('ver_notificaciones'))



@app.route('/admin_notificaciones')
def admin_notificaciones():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    consulta = """
        SELECT n.mensaje, n.fecha_envio AS fecha_hora, n.placa, n.origen, n.destino, n.leido,
               c.nombre, c.apellido_paterno, c.apellido_materno
        FROM Notificaciones n
        JOIN Conductores c ON n.id_conductor = c.id_conductor
        ORDER BY n.fecha_envio DESC
    """
    cursor.execute(consulta)
    notificaciones_raw = cursor.fetchall()

    notificaciones = []
    for fila in notificaciones_raw:
        nombre_completo = f"{fila['nombre']} {fila['apellido_paterno']} {fila['apellido_materno']}"
        notificaciones.append({
            'nombre_conductor': nombre_completo,
            'mensaje': fila['mensaje'],
            'fecha_hora': fila['fecha_hora'],
            'placa': fila['placa'],
            'origen': fila['origen'],
            'destino': fila['destino'],
            'leido': fila['leido']
        })

    cursor.close()
    conn.close()

    return render_template('admin_notificaciones.html', notificaciones=notificaciones)

@app.route('/actualizar_ubicacion', methods=['POST'])
def actualizar_ubicacion():
    if 'rol' not in session or session['rol'] != 'conductor':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json()
    latitud = data.get('latitud')
    longitud = data.get('longitud')
    conductor_id = session.get('conductor_id')

    if latitud is None or longitud is None or not conductor_id:
        return jsonify({'error': 'Datos incompletos'}), 400

    try:
        # Convertimos a float para compatibilidad con DECIMAL(10,6)
        latitud = float(latitud)
        longitud = float(longitud)

        # Imprimir para depuración
        print(f"Ubicación recibida del conductor {conductor_id}: ({latitud}, {longitud})")

        # Usamos tu función get_db_connection()
        connection = get_db_connection()
        cursor = connection.cursor()

        # Revisamos si ya existe ubicación para el conductor
        cursor.execute("SELECT id FROM UbicacionActual WHERE id_conductor = %s", (conductor_id,))
        existe = cursor.fetchone()

        if existe:
            # Actualizamos la ubicación existente
            cursor.execute("""
                UPDATE UbicacionActual
                SET latitud = %s, longitud = %s, timestamp = NOW()
                WHERE id_conductor = %s
            """, (latitud, longitud, conductor_id))
        else:
            # Insertamos nueva ubicación (con timestamp también)
            cursor.execute("""
                INSERT INTO UbicacionActual (id_conductor, latitud, longitud, timestamp)
                VALUES (%s, %s, %s, NOW())
            """, (conductor_id, latitud, longitud))

        connection.commit()

        return jsonify({'mensaje': 'Ubicación actualizada correctamente'})

    except Exception as e:
        print("Error al guardar ubicación:", e)
        return jsonify({'error': 'Error interno al guardar ubicación'}), 500

    finally:
        cursor.close()
        connection.close()


@app.route('/api/ubicacion_actual')
def ubicacion_actual():
    id_conductor = request.args.get('id_conductor')
    if not id_conductor:
        return jsonify({'error': 'Falta el parámetro id_conductor'}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Obtener ubicación actual del conductor
        cursor.execute("""
            SELECT ua.latitud, ua.longitud, ua.timestamp, c.nombre, c.apellido_paterno, c.apellido_materno
            FROM UbicacionActual ua
            JOIN Conductores c ON ua.id_conductor = c.id_conductor
            WHERE ua.id_conductor = %s
            ORDER BY ua.timestamp DESC
            LIMIT 1
        """, (id_conductor,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'error': 'Ubicación no encontrada'}), 404

        # Obtener información de la entrega actual (origen, destino, coordenadas)
        cursor.execute("""
            SELECT r.origen, r.destino, r.latitud_origen, r.longitud_origen, r.latitud_destino, r.longitud_destino
            FROM Entregas e
            JOIN Asignaciones_Rutas a ON e.id_asignacion = a.id_asignacion
            JOIN Rutas r ON a.id_ruta = r.id_ruta
            WHERE a.id_conductor = %s AND e.estado_entrega IN ('Asignada', 'pendiente', 'Incidente Reportado')
            LIMIT 1
        """, (id_conductor,))
        entrega = cursor.fetchone()

        # Armar respuesta
        respuesta = {
            'latitud': resultado['latitud'],
            'longitud': resultado['longitud'],
            'nombre_conductor': f"{resultado['nombre']} {resultado['apellido_paterno']} {resultado['apellido_materno']}",
            'timestamp': resultado['timestamp'].strftime('%Y-%m-%d %H:%M:%S')  # 🚀 solo esta línea nueva
        }

        if entrega:
            respuesta.update({
                'origen': entrega['origen'],
                'destino': entrega['destino'],
                'latitud_origen': entrega['latitud_origen'],
                'longitud_origen': entrega['longitud_origen'],
                'latitud_destino': entrega['latitud_destino'],
                'longitud_destino': entrega['longitud_destino']
            })

        return jsonify(respuesta)

    finally:
        cursor.close()
        connection.close()

@app.route('/api/conductores_asignados')
def api_conductores_asignados():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT c.id_conductor,
            CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) AS nombre_completo
        FROM Entregas e
        JOIN Asignaciones a ON e.id_asignacion = a.id_asignacion
        JOIN Conductores c ON a.id_conductor = c.id_conductor
    """)
    conductores = cursor.fetchall()
    cursor.close()
    return jsonify(conductores)

@app.route('/api/ultimas_ubicaciones')
def api_ultimas_ubicaciones():
    if 'rol' not in session or session['rol'] not in ('administrador', 'supervisor'):
        return jsonify({'error': 'No autorizado'}), 403

    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT ua.id_conductor, ua.latitud, ua.longitud, ua.timestamp,
            CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) AS nombre_conductor
        FROM UbicacionActual ua
        JOIN Conductores c ON ua.id_conductor = c.id_conductor
    """)
    ubicaciones = cursor.fetchall()
    cursor.close()

    return jsonify(ubicaciones)

@app.route('/api/ruta_asignada')
def api_ruta_asignada():
    id_entrega = request.args.get('id_entrega')

    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            r.origen, r.destino,
            r.latitud_origen, r.longitud_origen,
            r.latitud_destino, r.longitud_destino
        FROM Entregas e
        JOIN Rutas r ON e.id_ruta = r.id_ruta
        WHERE e.id_entrega = %s
    """, (id_entrega,))
    ruta = cursor.fetchone()
    cursor.close()

    if ruta:
        return jsonify(ruta)
    else:
        return jsonify({'error': 'Ruta no encontrada'})

@app.route('/responder_notificacion/<int:id_notificacion>', methods=['POST'])
def responder_notificacion(id_notificacion):
    mensaje = request.form['mensaje']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Obtener id_conductor de la notificación
        cursor.execute("SELECT id_conductor FROM Notificaciones WHERE id_notificacion = %s", (id_notificacion,))
        notificacion = cursor.fetchone()

        if notificacion:
            id_conductor = notificacion['id_conductor']

            # Insertar respuesta en la tabla correcta con los campos correctos
            cursor.execute("""
                INSERT INTO RespuestasSupervisor (id_notificacion, id_conductor, mensaje_respuesta)
                VALUES (%s, %s, %s)
            """, (id_notificacion, id_conductor, mensaje))

            connection.commit()

    except mysql.connector.Error as err:
        print(f"Error al responder notificación: {err}")
        return f"Error al responder notificación: {err}"

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('ver_notificaciones'))

@app.route('/admin_entregas')
def admin_entregas():
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('login'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT e.id_entrega, e.fecha_entrega, e.estado_entrega,
                   c.nombre AS nombre_conductor,
                   v.placa,
                   r.origen, r.destino
            FROM Entregas e
            JOIN Asignaciones_Rutas a ON e.id_asignacion = a.id_asignacion
            JOIN Conductores c ON a.id_conductor = c.id_conductor
            JOIN Vehiculos v ON a.id_vehiculo = v.id_vehiculo
            JOIN Rutas r ON a.id_ruta = r.id_ruta
            ORDER BY e.fecha_entrega DESC
        """)

        entregas = cursor.fetchall()

        return render_template('admin_entregas.html', entregas=entregas)

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return f"Error en la base de datos: {err}"

    finally:
        cursor.close()
        connection.close()

@app.route('/marcar_entrega_entregada/<int:id_entrega>', methods=['POST'])
def marcar_entrega_entregada(id_entrega):
    if 'rol' not in session or session['rol'] != 'conductor':
        return redirect(url_for('login'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Cambiar el estado a 'entregado'
        cursor.execute("""
            UPDATE Entregas
            SET estado_entrega = 'entregado'
            WHERE id_entrega = %s
        """, (id_entrega,))
        connection.commit()

    except mysql.connector.Error as err:
        print(f"Error en la base de datos al marcar entregada: {err}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('panel_conductor'))

import requests
from flask import Response

@app.route('/api/trazar_ruta', methods=['POST'])
def trazar_ruta():
    data = request.get_json()
    origen = data.get('origen')
    destino = data.get('destino')

    if not origen or not destino:
        return jsonify({'error': 'Parámetros incompletos'}), 400

    headers = {
        'Authorization': '5b3ce3597851110001cf62484aaf928f43e70cf577d4dc175ce0e713aec1334d7b07af0a45ee57d2',
        'Content-Type': 'application/json'
    }

    body = {
        "coordinates": [origen, destino]
    }

    try:
        response = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/geojson',
                                 headers=headers, json=body)

        return Response(response.content, status=response.status_code, content_type='application/json')

    except Exception as e:
        print("Error al trazar ruta:", e)
        return jsonify({'error': 'Error al comunicarse con OpenRouteService'}), 500

@app.route('/seguimiento_entregas')
def seguimiento_entregas():
    cursor = mysql.connection.cursor(dictionary=True)

    # Obtener entregas
    cursor.execute("""
        SELECT e.id_entrega, e.id_conductor, c.nombre AS nombre_conductor,
               v.placa, r.origen, r.destino,
               r.latitud_origen, r.longitud_origen,
               r.latitud_destino, r.longitud_destino,
               e.estado_entrega, e.fecha_entrega
        FROM Entregas e
        JOIN Conductores c ON e.id_conductor = c.id_conductor
        JOIN Vehiculos v ON e.id_vehiculo = v.id_vehiculo
        JOIN Rutas r ON e.id_ruta = r.id_ruta
    """)
    entregas = cursor.fetchall()

    # Obtener rutas Dijkstra
    cursor.execute("SELECT * FROM Rutas_Grafo")
    rutas_db = cursor.fetchall()

    # Construir el grafo
    grafo = {}
    for ruta in rutas_db:
        origen = ruta['origen']
        destino = ruta['destino']
        distancia = ruta['distancia']
        bloqueada = ruta['bloqueada']

        if origen not in grafo:
            grafo[origen] = []
        if not bloqueada:
            grafo[origen].append((destino, distancia))

        if destino not in grafo:
            grafo[destino] = []
        if not bloqueada:
            grafo[destino].append((origen, distancia))  # si es bidireccional

    # Calcular rutas óptimas
    rutas_dijkstra = []
    for ruta in rutas_db:
        origen = ruta['origen']
        destino = ruta['destino']
        bloqueada = ruta['bloqueada']

        if bloqueada:
            camino_optimo = "No disponible"
            distancia_total = "-"
        else:
            distancia_total, camino_optimo = dijkstra(grafo, origen, destino)
            if distancia_total == float('inf'):
                camino_optimo = "No disponible"
                distancia_total = "-"

        rutas_dijkstra.append({
            'origen': origen,
            'destino': destino,
            'bloqueada': bloqueada,
            'camino_optimo': " → ".join(camino_optimo) if isinstance(camino_optimo, list) else camino_optimo,
            'distancia_total': distancia_total if distancia_total != float('inf') else "-"
        })

    cursor.close()

    return render_template('seguimiento_entregas.html', entregas=entregas, rutas_dijkstra=rutas_dijkstra)


# ===== Algoritmo Dijkstra =====
def cargar_grafo():
    conexion = get_db_connection() # Usa tu función para obtener la conexión a MySQL
    cursor = conexion.cursor(dictionary=True)

    # Solo rutas habilitadas
    cursor.execute("SELECT origen, destino, peso, habilitado FROM Grafo_Rutas WHERE habilitado = TRUE")
    rutas = cursor.fetchall()

    conexion.close()

    # Construir el grafo como un diccionario
    grafo = {}
    for ruta in rutas:
        origen = ruta['origen']
        destino = ruta['destino']
        peso = ruta['peso']

        # Si el nodo no existe en el diccionario, lo creamos
        if origen not in grafo:
            grafo[origen] = []
        if destino not in grafo:
            grafo[destino] = []

        # Agregamos la arista (asumimos que la carretera es bidireccional)
        grafo[origen].append((destino, peso))
        grafo[destino].append((origen, peso))

    return grafo


# ===== Algoritmo Dijkstra =====
def dijkstra(grafo, inicio, fin):

    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[inicio] = 0
    padre = {nodo: None for nodo in grafo}

    cola = []
    heapq.heappush(cola, (0, inicio))

    while cola:
        distancia_actual, nodo_actual = heapq.heappop(cola)

        if nodo_actual == fin:
            break

        for vecino, peso in grafo.get(nodo_actual, []):
            nueva_distancia = distancia_actual + peso
            if nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                padre[vecino] = nodo_actual
                heapq.heappush(cola, (nueva_distancia, vecino))

    # Reconstruir el camino
    camino = []
    nodo = fin
    while nodo is not None:
        camino.insert(0, nodo)
        nodo = padre[nodo]

    if distancias[fin] == float('inf'):
        return float('inf'), []

    return distancias[fin], camino

@app.route('/calcular_ruta_optima/<int:ruta_id>')
def calcular_ruta_optima(ruta_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Rutas_Grafo")
        rutas_db = cursor.fetchall()

        grafo = {}
        for ruta in rutas_db:
            origen = ruta['origen']
            destino = ruta['destino']
            distancia = ruta['distancia']
            bloqueada = ruta['bloqueada']

            if origen not in grafo:
                grafo[origen] = []
            if not bloqueada:
                grafo[origen].append((destino, distancia))

            if destino not in grafo:
                grafo[destino] = []
            if not bloqueada:
                grafo[destino].append((origen, distancia))

        # Obtener la ruta seleccionada
        cursor.execute("SELECT * FROM Rutas WHERE id_ruta = %s", (ruta_id,))
        ruta_db = cursor.fetchone()

        origen = ruta_db['origen']
        destino = ruta_db['destino']

        print(f"==> Calculando ruta Dijkstra de {origen} a {destino}")

        # Verificar si origen y destino están en el grafo
        if origen not in grafo or destino not in grafo:
            print("==> Origen o destino no en grafo")
            return jsonify({'error': 'Origen o destino no disponible en el grafo'}), 400

        # Calcular Dijkstra
        distancia_total, camino_optimo = dijkstra(grafo, origen, destino)

        print(f"==> Resultado Dijkstra: distancia={distancia_total}, camino={camino_optimo}")

        return jsonify({
            'camino_optimo': camino_optimo,
            'distancia_total': distancia_total
        })

    except Exception as e:
        print(f"Error al calcular ruta: {e}")
        return jsonify({'error': f'Error interno al calcular la ruta: {e}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/bloquear_ruta', methods=['POST'])
def bloquear_ruta():
    origen = request.form['origen']
    destino = request.form['destino']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE Rutas_Grafo
        SET bloqueada = TRUE
        WHERE origen = %s AND destino = %s
    """, (origen, destino))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('seguimiento_entregas'))

@app.route('/desbloquear_ruta', methods=['POST'])
def desbloquear_ruta():
    origen = request.form['origen']
    destino = request.form['destino']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE Rutas_Grafo
        SET bloqueada = FALSE
        WHERE origen = %s AND destino = %s
    """, (origen, destino))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('seguimiento_entregas'))


if __name__ == '__main__':
    app.run(debug=True)



