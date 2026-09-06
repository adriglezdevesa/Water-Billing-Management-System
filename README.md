# 💧 Water Billing Management System

Aplicación de escritorio Full-Stack desarrollada a medida para la gestión automatizada y facturación oficial del servicio de aguas de una administración local.

El software sustituye los procesos manuales por un entorno digital unificado, gestionando bases de datos de clientes, configuraciones de tarifas dinámicas y generación de documentos oficiales con análisis de datos en tiempo real.

*Nota: Por motivos de protección de datos (RGPD), los teléfonos, correos y CIFs institucionales presentes en el código fuente han sido anonimizados.*

## 🚀 Características Principales (Features)

*   **Interfaz de Configuración Dinámica (JSON):** Toda la lógica de precios (tramos de consumo, cuotas fijas, impuestos y cánones autonómicos) está abstraída en un archivo `config_tarifas.json`. La UI incluye un panel avanzado (`CustomTkinter`) que permite al personal administrativo modificar los precios visualmente sin interactuar con el código fuente.
*   **Base de Datos Inteligente (`SQLite`):** Sistema de guardado automático (Upsert). Al registrar una factura, el cliente persiste en la base de datos. Para la siguiente iteración, el sistema autocompleta los datos (Nombre, Dirección, Tarifa) simplemente buscando el DNI o Nº de Contrato.
*   **Cálculo Automatizado de Tiempos (`datetime`):** El algoritmo lee el reloj del sistema para deducir matemáticamente el cuadrimestre de facturación en curso y sumar el margen legal de días para establecer la fecha límite de pago de forma desatendida.
*   **Motor Paramétrico de PDFs (`FPDF` & `Matplotlib`):** Renderizado milimétrico de la factura oficial, incluyendo el desglose económico por responsabilidades (Separation of Concerns entre tarifa local y autonómica). Incrusta de forma asíncrona un gráfico de barras con el histórico de consumo y un gráfico sectorial (*Pie Chart*) con la distribución del gasto.

## 📸 Interfaz y Resultados (Screenshots)

### 1. Interfaz Gráfica y Gestión de Tarifas
![Interfaz1](img/interfaz1.png)
![Interfaz2](img/interfaz2.png)

### 2. Factura Oficial Generada
![Factura](img/factura.png)

## 🛠️ Tecnologías y Arquitectura
*   **Lenguaje:** Python
*   **Base de Datos:** SQLite3 
*   **Frontend (GUI):** CustomTkinter
*   **Procesamiento y Renderizado:** FPDF, Matplotlib, NumPy

## ⚙️ Instalación y Uso (How to run)

1. Clona este repositorio en tu máquina local:
   ```bash
   git clone https://github.com/adriglezdevesa/Water-Billing-Management-System.git

2. Instala las dependencias necesarias:
    pip install -r requirements.txt

3. Genera la base de datos simulada (crea las tablas e inserta 1.000 clientes con patrones de consumo aleatorios):
    python src/generador_datos.py

4. Ejecuta el Panel de Control:
    python src/interfaz.py