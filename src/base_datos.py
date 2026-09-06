import sqlite3
import os

def inicializar_bd():
    ruta_bd = os.path.join(os.path.dirname(__file__), '..', 'datos', 'facturacion.db')
    conexion = sqlite3.connect(ruta_bd)
    cursor = conexion.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            num_contrato TEXT PRIMARY KEY,
            titular TEXT,
            nif TEXT,
            direccion TEXT,
            poblacion TEXT,
            num_contador TEXT,
            diametro_contador TEXT,
            tipo_tarifa TEXT DEFAULT 'DOMESTICO'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
            num_factura TEXT,
            num_contrato TEXT,
            periodo TEXT,
            fecha_emision DATE,
            lectura_anterior REAL,
            lectura_actual REAL,
            consumo_real REAL,
            consumo_facturado REAL,
            total_pagar REAL,
            FOREIGN KEY (num_contrato) REFERENCES clientes (num_contrato)
        )
    ''')

    conexion.commit()
    conexion.close()
    print(f"Base de datos de facturación limpia e inicializada.")

if __name__ == "__main__":
    inicializar_bd()