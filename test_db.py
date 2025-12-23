import psycopg2

try:
    # Datos de conexión: ajusta según tu servidor
    conn = psycopg2.connect(
        host="10.25.16.14",   # IP del servidor remoto
        database="secgrehu_novatec",     # nombre de tu base de datos
        user="postgres",      # tu usuario
        password="postgres" # tu contraseña
    )

    # Crear cursor
    cur = conn.cursor()

    # Ejecutar una consulta simple
    cur.execute("SELECT version();")

    # Obtener resultado
    version = cur.fetchone()
    print("Conexión exitosa a PostgreSQL")
    print("Versión del servidor:", version[0])

    # Cerrar cursor y conexión
    cur.close()
    conn.close()

except Exception as e:
    print("Error de conexión:", e)