import customtkinter as ctk
import logica
import platform
import os

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("dark-blue") 

def abrir_pdf(ruta_pdf):
    ruta_absoluta = os.path.abspath(ruta_pdf)
    if platform.system() == 'Windows':
        os.startfile(ruta_absoluta)
    else:
        import subprocess
        subprocess.Popen(['xdg-open', ruta_absoluta])

class GestorFacturacion(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gestor de Facturación - Servicio Municipal de Aguas")
        self.geometry("1150x780")
        self.minsize(900, 600)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Crear la estructura de la aplicación
        self.crear_menu_lateral()
        self.crear_vista_individual()
        self.crear_vista_configuracion()
        
        self.mostrar_vista("individual")

    def crear_menu_lateral(self):
        self.frame_menu = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray15"))
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(3, weight=1)
        
        lbl_titulo = ctk.CTkLabel(self.frame_menu, text="CONCELLO\nDE PRUEBA", font=("Arial", 18, "bold"))
        lbl_titulo.grid(row=0, column=0, padx=20, pady=(30, 10))
        
        lbl_sub = ctk.CTkLabel(self.frame_menu, text="Servicio de Aguas", font=("Arial", 12))
        lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        self.btn_nav_indiv = ctk.CTkButton(self.frame_menu, text="📄 Facturación", height=40, command=lambda: self.mostrar_vista("individual"))
        self.btn_nav_indiv.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_nav_config = ctk.CTkButton(self.frame_menu, text="⚙️ Config. de Tarifas", height=40, command=lambda: self.mostrar_vista("config"))
        self.btn_nav_config.grid(row=3, column=0, padx=20, pady=10, sticky="n")
        
        lbl_info = ctk.CTkLabel(self.frame_menu, text="Panel de Gestión v3.0", font=("Arial", 10), text_color="gray")
        lbl_info.grid(row=4, column=0, pady=20, sticky="s")

    def mostrar_vista(self, vista):
        if vista == "individual":
            self.frame_config.grid_forget()
            self.frame_individual.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.btn_nav_indiv.configure(fg_color=("gray75", "gray25"))
            self.btn_nav_config.configure(fg_color="transparent")
        elif vista == "config":
            self.frame_individual.grid_forget()
            self.frame_config.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.btn_nav_config.configure(fg_color=("gray75", "gray25"))
            self.btn_nav_indiv.configure(fg_color="transparent")

    # --- PESTAÑA: CONFIGURACIÓN DE TARIFAS ---
    def crear_vista_configuracion(self):
        self.frame_config = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_config.grid_columnconfigure(0, weight=1)
        self.frame_config.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.frame_config, text="Configuración de Tarifas y Tramos", font=("Arial", 24, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        self.scroll_config = ctk.CTkScrollableFrame(self.frame_config)
        self.scroll_config.grid(row=1, column=0, sticky="nsew")
        
        self.vars_config = {}
        config_actual = logica.cargar_configuracion()
        
        def crear_seccion_config(titulo, clave_padre, campos):
            marco = ctk.CTkFrame(self.scroll_config)
            marco.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(marco, text=titulo, font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10, padx=10, sticky="w")
            
            self.vars_config[clave_padre] = {}
            r, c = 1, 0
            for label_texto, clave_hija in campos:
                ctk.CTkLabel(marco, text=label_texto).grid(row=r, column=c, padx=10, pady=5, sticky="e")
                var_val = ctk.StringVar(value=str(config_actual[clave_padre][clave_hija]))
                self.vars_config[clave_padre][clave_hija] = var_val
                
                entry = ctk.CTkEntry(marco, textvariable=var_val, width=120)
                entry.grid(row=r, column=c+1, padx=10, pady=5, sticky="w")
                
                c += 2
                if c > 2:
                    c = 0
                    r += 1

        crear_seccion_config("💧 Servicio de Agua - DOMÉSTICO", "agua_domestico", [
            ("Cuota Fija (€):", "cuota_fija"), ("Mínimo Exento (m³):", "minimo_m3"),
            ("Precio Tramo 1 (€/m³):", "precio_t1"), ("Límite Tramo 2 (m³):", "limite_t2"),
            ("Precio Tramo 2 (€/m³):", "precio_t2"), ("Precio Tramo 3 (>T2) (€):", "precio_t3")
        ])
        
        crear_seccion_config("🏭 Servicio de Agua - INDUSTRIAL", "agua_industrial", [
            ("Cuota Fija (€):", "cuota_fija"), ("Mínimo Exento (m³):", "minimo_m3"),
            ("Precio Tramo 1 (€/m³):", "precio_t1"), ("Límite Tramo 2 (m³):", "limite_t2"),
            ("Precio Tramo 2 (€/m³):", "precio_t2"), ("Precio Tramo 3 (>T2) (€):", "precio_t3")
        ])
        
        crear_seccion_config("🌊 Canon da Auga (Xunta de Galicia)", "canon_auga", [
            ("Cuota Fija (€):", "cuota_fija"), ("Límite Tramo 1 (m³):", "limite_t1"),
            ("Precio Tramo 1 (€/m³):", "precio_t1"), ("Límite Tramo 2 (m³):", "limite_t2"),
            ("Precio Tramo 2 (€/m³):", "precio_t2"), ("Límite Tramo 3 (m³):", "limite_t3"),
            ("Precio Tramo 3 (€/m³):", "precio_t3"), ("Precio Tramo 4 (>T3) (€):", "precio_t4")
        ])
        
        crear_seccion_config("⚖️ Impuestos", "impuestos", [
            ("IVA Agua (0.10 = 10%):", "iva_agua")
        ])
        
        self.btn_guardar_config = ctk.CTkButton(self.frame_config, text="💾 Guardar Configuración", font=("Arial", 14, "bold"), height=45, command=self.accion_guardar_config)
        self.btn_guardar_config.grid(row=2, column=0, pady=10)
        
        self.lbl_estado_config = ctk.CTkLabel(self.frame_config, text="Modifique los parámetros y pulse Guardar.", font=("Arial", 13))
        self.lbl_estado_config.grid(row=3, column=0)

    def accion_guardar_config(self):
        try:
            nueva_config = {
                "agua_domestico": {},
                "agua_industrial": {},
                "canon_auga": {},
                "impuestos": {}
            }
            
            for padre in self.vars_config:
                for hijo, var in self.vars_config[padre].items():
                    texto_num = var.get().replace(',', '.') # Por si el usuario usa comas
                    val = float(texto_num)
                    # Si el campo es un límite de m3, lo forzamos a número entero
                    if "limite" in hijo or "minimo" in hijo:
                        val = int(val)
                    nueva_config[padre][hijo] = val
                    
            logica.guardar_configuracion(nueva_config)
            self.lbl_estado_config.configure(text="✅ Parámetros guardados con éxito. Las próximas facturas usarán estos precios.", text_color="#2ecc71")
        except ValueError:
            self.lbl_estado_config.configure(text="❌ Error: Introduzca solo números (utilice puntos para los decimales).", text_color="#e74c3c")

    # --- PESTAÑA: FACTURACIÓN INDIVIDUAL ---
    def crear_vista_individual(self):
        self.frame_individual = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_individual.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_individual, text="Generador de Facturas", font=("Arial", 24, "bold")).pack(anchor="w", pady=(0, 20))
        
        frame_busqueda = ctk.CTkFrame(self.frame_individual)
        frame_busqueda.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_busqueda, text="Buscar Cliente:").pack(side="left", padx=15, pady=15)
        self.entry_buscador = ctk.CTkEntry(frame_busqueda, width=200, placeholder_text="Nº Contrato, NIF o Nombre")
        self.entry_buscador.pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="Buscar y Autocompletar", command=self.accion_buscar_indiv).pack(side="left", padx=15)

        frame_cliente = ctk.CTkFrame(self.frame_individual)
        frame_cliente.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_cliente, text="Datos del Cliente", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10, padx=15, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="Nº Contrato:").grid(row=1, column=0, padx=15, pady=10, sticky="e")
        self.entry_contrato = ctk.CTkEntry(frame_cliente, width=150)
        self.entry_contrato.grid(row=1, column=1, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="Nº Contador:").grid(row=1, column=2, padx=15, pady=10, sticky="e")
        self.entry_contador = ctk.CTkEntry(frame_cliente, width=150)
        self.entry_contador.grid(row=1, column=3, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="Titular:").grid(row=2, column=0, padx=15, pady=10, sticky="e")
        self.entry_titular = ctk.CTkEntry(frame_cliente, width=300)
        self.entry_titular.grid(row=2, column=1, columnspan=3, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="NIF/DNI:").grid(row=3, column=0, padx=15, pady=10, sticky="e")
        self.entry_nif = ctk.CTkEntry(frame_cliente, width=150)
        self.entry_nif.grid(row=3, column=1, sticky="w")
        
        # --- AÑADIDO: TIPO DE TARIFA ---
        ctk.CTkLabel(frame_cliente, text="Tarifa Aplicada:").grid(row=3, column=2, padx=15, pady=10, sticky="e")
        self.combo_tarifa = ctk.CTkComboBox(frame_cliente, values=["DOMESTICO", "INDUSTRIAL"], width=150)
        self.combo_tarifa.grid(row=3, column=3, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="Dirección:").grid(row=4, column=0, padx=15, pady=10, sticky="e")
        self.entry_direccion = ctk.CTkEntry(frame_cliente, width=350)
        self.entry_direccion.grid(row=4, column=1, columnspan=3, sticky="w")
        
        ctk.CTkLabel(frame_cliente, text="Población / C.P.:").grid(row=5, column=0, padx=15, pady=10, sticky="e")
        self.entry_poblacion = ctk.CTkEntry(frame_cliente, width=350, placeholder_text="Ej: 32670 A Pousa")
        self.entry_poblacion.grid(row=5, column=1, columnspan=3, sticky="w", pady=(0, 15))

        frame_datos = ctk.CTkFrame(self.frame_individual)
        frame_datos.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_datos, text="Datos de Consumo", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10, padx=15, sticky="w")
        
        ctk.CTkLabel(frame_datos, text="Lec. Anterior:").grid(row=1, column=0, padx=15, pady=10, sticky="e")
        self.entry_lec_ant = ctk.CTkEntry(frame_datos, width=100)
        self.entry_lec_ant.grid(row=1, column=1, sticky="w")
        
        ctk.CTkLabel(frame_datos, text="Lec. Actual:").grid(row=1, column=2, padx=15, pady=10, sticky="e")
        self.entry_lec_act = ctk.CTkEntry(frame_datos, width=100)
        self.entry_lec_act.grid(row=1, column=3, sticky="w")
        
        ctk.CTkLabel(frame_datos, text="Periodo:").grid(row=2, column=0, padx=15, pady=10, sticky="e")
        self.entry_periodo = ctk.CTkEntry(frame_datos, width=150)
        self.entry_periodo.grid(row=2, column=1, columnspan=3, sticky="w", pady=(0, 15))
        
        self.entry_periodo.insert(0, logica.obtener_periodo_actual())

        self.btn_generar_indiv = ctk.CTkButton(self.frame_individual, text="Guardar y Generar Factura", font=("Arial", 14, "bold"), height=45, command=self.accion_generar_indiv)
        self.btn_generar_indiv.pack(pady=10)
        
        self.lbl_estado_indiv = ctk.CTkLabel(self.frame_individual, text="Listo.", font=("Arial", 13))
        self.lbl_estado_indiv.pack()

    def accion_buscar_indiv(self):
        texto = self.entry_buscador.get()
        if not texto: return
        cliente = logica.buscar_cliente(texto)
        if cliente:
            self.lbl_estado_indiv.configure(text="Cliente cargado correctamente.", text_color="#2ecc71")
            self.entry_contrato.delete(0, "end"); self.entry_contrato.insert(0, cliente[0])
            self.entry_titular.delete(0, "end"); self.entry_titular.insert(0, cliente[1])
            self.entry_nif.delete(0, "end"); self.entry_nif.insert(0, cliente[2])
            self.entry_direccion.delete(0, "end"); self.entry_direccion.insert(0, cliente[3])
            
            self.entry_poblacion.delete(0, "end")
            if cliente[4]: 
                self.entry_poblacion.insert(0, cliente[4])
                
            self.entry_contador.delete(0, "end"); self.entry_contador.insert(0, cliente[5])
            
            # Cargar tarifa del cliente
            if cliente[7]:
                self.combo_tarifa.set(cliente[7])
            else:
                self.combo_tarifa.set("DOMESTICO")
                
            self.entry_lec_ant.delete(0, "end"); self.entry_lec_ant.insert(0, cliente[8])
        else:
            self.lbl_estado_indiv.configure(text="Cliente no encontrado. Rellene a mano para registrarlo.", text_color="#e67e22")
            for e in [self.entry_contrato, self.entry_titular, self.entry_nif, self.entry_direccion, self.entry_poblacion, self.entry_contador, self.entry_lec_ant]:
                e.delete(0, "end")
            self.combo_tarifa.set("DOMESTICO")

    def accion_generar_indiv(self):
        try:
            datos_cliente = (
                self.entry_contrato.get().strip(),
                self.entry_titular.get().strip().upper(),
                self.entry_nif.get().strip().upper(),
                self.entry_direccion.get().strip().upper(),
                self.entry_poblacion.get().strip().upper(),
                self.entry_contador.get().strip(),
                self.combo_tarifa.get() # Pasamos la tarifa elegida (Doméstico o Industrial)
            )
            
            if "" in datos_cliente or self.entry_lec_ant.get() == "" or self.entry_lec_act.get() == "":
                self.lbl_estado_indiv.configure(text="Error: Faltan datos obligatorios.", text_color="#e74c3c")
                return
                
            lec_ant = float(self.entry_lec_ant.get())
            lec_act = float(self.entry_lec_act.get())
            periodo = self.entry_periodo.get().strip() 
            
            self.lbl_estado_indiv.configure(text="Procesando factura...", text_color="#f1c40f")
            self.update()
            
            periodo_val = periodo if periodo else None
            mensaje, ruta_pdf = logica.procesar_factura(datos_cliente, lec_ant, lec_act, periodo_val)
            
            if ruta_pdf:
                self.lbl_estado_indiv.configure(text=mensaje, text_color="#2ecc71")
                abrir_pdf(ruta_pdf)
            else:
                self.lbl_estado_indiv.configure(text=mensaje, text_color="#e74c3c")
        except ValueError:
            self.lbl_estado_indiv.configure(text="Error: Las lecturas deben ser números válidos.", text_color="#e74c3c")

if __name__ == "__main__":
    app = GestorFacturacion()
    app.mainloop()