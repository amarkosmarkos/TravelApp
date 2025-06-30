import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path
import shutil
import threading
import re

def extract_osm_uid(osm_url: str) -> str:
    """Extrae el identificador OSM de una URL de OpenStreetMap"""
    match = re.search(r'openstreetmap\.org/(node|way|relation)/(\d+)', osm_url)
    if not match:
        raise ValueError("Invalid OSM URL")
    
    osm_type = match.group(1)
    osm_id = match.group(2)
    prefix = {"node": "N", "way": "W", "relation": "R"}[osm_type]
    
    return f"OSM:{prefix}{osm_id}"

class EntidadesEditor:
    def __init__(self, root, input_path, output_path):
        self.root = root
        self.root.title("Editor de Entidades - TravelApp")
        self.root.geometry("1200x800")
        
        # Rutas de archivos (pasadas como parámetros)
        self.archivo_original = Path(input_path)
        self.archivo_trabajo = Path(output_path)
        
        # Crear copia de trabajo si no existe
        self.crear_copia_trabajo()
        
        # Cargar datos
        self.entidades = self.cargar_entidades()
        self.indice_actual = 0
        
        self.crear_interfaz()
        self.mostrar_entidad_actual()
        
    def crear_copia_trabajo(self):
        """Crea una copia del archivo original para trabajar"""
        try:
            if not self.archivo_trabajo.exists():
                if self.archivo_original.exists():
                    shutil.copy2(self.archivo_original, self.archivo_trabajo)
                    print(f"✅ Copia creada: {self.archivo_trabajo}")
                else:
                    messagebox.showerror("Error", f"No existe el archivo original: {self.archivo_original}")
            else:
                print(f"✅ Usando archivo existente: {self.archivo_trabajo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la copia: {e}")
    
    def cargar_entidades(self):
        """Carga las entidades desde el archivo de trabajo"""
        entidades = []
        try:
            with open(self.archivo_trabajo, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entidades.append(json.loads(line))
            print(f"✅ Cargadas {len(entidades)} entidades desde {self.archivo_trabajo}")
            return entidades
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")
            return []
    
    def guardar_entidades(self):
        """Guarda las entidades en el archivo de trabajo"""
        try:
            with open(self.archivo_trabajo, 'w', encoding='utf-8') as f:
                for entidad in self.entidades:
                    f.write(json.dumps(entidad, ensure_ascii=False) + '\n')
            print(f"✅ Entidades guardadas en: {self.archivo_trabajo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def get_key(self, ent):
        """Genera una clave única para agrupar entidades"""
        tipo = str(ent.get('entity_type', '')).lower()
        subtipo = str(ent.get('subtype', '')).lower()
        ciudad = str(ent.get('city', '')).lower()
        nombre = str(ent.get('name', '')).lower()
        return (tipo, subtipo, ciudad, nombre)
    
    def intentar_agrupar_entidad(self, nueva_entidad):
        """Busca entidades similares para agrupar"""
        if not self.entidades:
            return []
        
        nueva_key = self.get_key(nueva_entidad)
        entidades_similares = []
        
        for i, entidad in enumerate(self.entidades):
            if i != self.indice_actual:  # No comparar consigo misma
                entidad_key = self.get_key(entidad)
                if nueva_key == entidad_key:
                    entidades_similares.append((i, entidad))
        
        return entidades_similares
    
    def agrupar_entidades_similares(self, nueva_entidad, entidades_similares):
        """Agrupa entidades similares combinando sus datos"""
        if not entidades_similares:
            return
        
        # Tomar la nueva entidad como base
        base = dict(nueva_entidad)
        
        # Combinar datos de todas las entidades similares
        descripciones = []
        todas_imagenes = []
        websites = []
        todas_urls = []
        
        # Añadir datos de la nueva entidad
        desc = base.get('description', '').strip()
        if desc:
            descripciones.append(desc)
        
        imagenes = base.get('images', [])
        if isinstance(imagenes, list):
            todas_imagenes.extend(imagenes)
        
        website = base.get('official_website', '').strip()
        if website:
            websites.append(website)
        
        url = base.get('source_url', '').strip()
        if url:
            todas_urls.append(url)
        
        # Añadir datos de entidades similares
        for i, entidad in entidades_similares:
            desc = entidad.get('description', '').strip()
            if desc and desc not in descripciones:
                descripciones.append(desc)
            
            imagenes = entidad.get('images', [])
            if isinstance(imagenes, list):
                todas_imagenes.extend(imagenes)
            
            website = entidad.get('official_website', '').strip()
            if website and website not in websites:
                websites.append(website)
            
            url = entidad.get('source_url', '').strip()
            if url and url not in todas_urls:
                todas_urls.append(url)
        
        # Actualizar la entidad base
        base['description'] = " | ".join(descripciones)
        base['images'] = list(set(todas_imagenes))
        base['official_website'] = " | ".join(websites)
        base['all_source_urls'] = todas_urls
        base['appearances'] = len(entidades_similares) + 1
        
        # Reemplazar la entidad actual
        self.entidades[self.indice_actual] = base
        
        # Eliminar entidades similares (en orden inverso para no afectar índices)
        indices_a_eliminar = [i for i, _ in sorted(entidades_similares, reverse=True)]
        for i in indices_a_eliminar:
            del self.entidades[i]
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Información de archivo
        ttk.Label(main_frame, text=f"Archivo: {self.archivo_trabajo.name}", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Contador de entidades
        self.contador_label = ttk.Label(main_frame, text="", font=("Arial", 9))
        self.contador_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Frame de navegación
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Botones de navegación
        ttk.Button(nav_frame, text="⏮️ Primera", command=self.primera_entidad).pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="⏪ Anterior", command=self.anterior_entidad).pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="⏩ Siguiente", command=self.siguiente_entidad).pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="⏭️ Última", command=self.ultima_entidad).pack(fill=tk.X, pady=2)
        
        # Frame de acciones
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Botones de acciones
        ttk.Button(action_frame, text="✏️ Modificar", command=self.modificar_entidad).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🗑️ Eliminar", command=self.eliminar_entidad).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="💾 Guardar Ahora", command=self.guardar_entidades).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🔄 Recargar", command=self.recargar_entidades).pack(fill=tk.X, pady=2)
        
        # Frame de OSM/Wikidata
        osm_frame = ttk.Frame(main_frame)
        osm_frame.grid(row=2, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(osm_frame, text="📍 Enlace OSM:").pack(anchor=tk.W)
        self.osm_entry = ttk.Entry(osm_frame, width=40)
        self.osm_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(osm_frame, text="🆔 Wikidata ID:").pack(anchor=tk.W)
        self.wikidata_entry = ttk.Entry(osm_frame, width=40)
        self.wikidata_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(osm_frame, text="➕ Añadir OSM/Wikidata", command=self.anadir_osm_wikidata).pack(fill=tk.X, pady=5)
        
        # Área de visualización
        self.text_area = scrolledtext.ScrolledText(main_frame, height=25, width=80, font=("Consolas", 9))
        self.text_area.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
    
    def mostrar_entidad_actual(self):
        """Muestra la entidad actual en el área de texto"""
        if not self.entidades:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(1.0, "No hay entidades para mostrar")
            self.contador_label.config(text="No hay entidades")
            return
        
        entidad = self.entidades[self.indice_actual]
        json_str = json.dumps(entidad, indent=2, ensure_ascii=False)
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, json_str)
        
        # Actualizar contador
        self.contador_label.config(text=f"Entidad {self.indice_actual + 1} de {len(self.entidades)}")
    
    def primera_entidad(self):
        """Va a la primera entidad"""
        if self.entidades:
            self.indice_actual = 0
            self.mostrar_entidad_actual()
    
    def anterior_entidad(self):
        """Va a la entidad anterior"""
        if self.entidades and self.indice_actual > 0:
            self.indice_actual -= 1
            self.mostrar_entidad_actual()
    
    def siguiente_entidad(self):
        """Va a la entidad siguiente"""
        if self.entidades and self.indice_actual < len(self.entidades) - 1:
            self.indice_actual += 1
            self.mostrar_entidad_actual()
    
    def ultima_entidad(self):
        """Va a la última entidad"""
        if self.entidades:
            self.indice_actual = len(self.entidades) - 1
            self.mostrar_entidad_actual()
    
    def modificar_entidad(self):
        """Abre ventana para modificar la entidad actual"""
        if not self.entidades:
            return
        
        # Crear ventana de edición
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Modificar Entidad")
        edit_window.geometry("800x600")
        
        # Área de edición
        edit_text = scrolledtext.ScrolledText(edit_window, height=30, width=80, font=("Consolas", 10))
        edit_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cargar JSON actual
        entidad_actual = self.entidades[self.indice_actual]
        json_str = json.dumps(entidad_actual, indent=2, ensure_ascii=False)
        edit_text.insert(1.0, json_str)
        
        # Frame de botones
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def guardar_cambios():
            try:
                # Obtener JSON modificado
                nuevo_json = edit_text.get(1.0, tk.END).strip()
                nueva_entidad = json.loads(nuevo_json)
                
                # Intentar agrupar automáticamente
                entidades_agrupadas = self.intentar_agrupar_entidad(nueva_entidad)
                
                if entidades_agrupadas:
                    # Se encontraron entidades para agrupar
                    respuesta = messagebox.askyesno(
                        "Entidades similares encontradas",
                        f"Se encontraron {len(entidades_agrupadas)} entidades similares.\n\n"
                        f"¿Quieres agruparlas automáticamente?\n\n"
                        f"Entidades encontradas:\n" + 
                        "\n".join([f"• {e.get('name', 'Sin nombre')} (índice {i})" for i, e in entidades_agrupadas])
                    )
                    
                    if respuesta:
                        # Agrupar las entidades
                        self.agrupar_entidades_similares(nueva_entidad, entidades_agrupadas)
                        messagebox.showinfo("Éxito", f"Entidades agrupadas correctamente. Se eliminaron {len(entidades_agrupadas)} entidades duplicadas.")
                    else:
                        # Solo actualizar la entidad actual
                        self.entidades[self.indice_actual] = nueva_entidad
                        messagebox.showinfo("Éxito", "Entidad modificada sin agrupar")
                else:
                    # No se encontraron entidades similares, solo actualizar
                    self.entidades[self.indice_actual] = nueva_entidad
                    messagebox.showinfo("Éxito", "Entidad modificada correctamente")
                
                # Guardar automáticamente
                self.guardar_entidades()
                
                # Actualizar vista
                self.mostrar_entidad_actual()
                
                # Cerrar ventana
                edit_window.destroy()
                
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"JSON inválido: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        def cancelar():
            edit_window.destroy()
        
        ttk.Button(button_frame, text="💾 Guardar", command=guardar_cambios).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Cancelar", command=cancelar).pack(side=tk.LEFT)
    
    def eliminar_entidad(self):
        """Elimina la entidad actual"""
        if not self.entidades:
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar la entidad actual?\n\n"
            f"Nombre: {self.entidades[self.indice_actual].get('name', 'Sin nombre')}"
        )
        
        if respuesta:
            del self.entidades[self.indice_actual]
            
            # Ajustar índice si es necesario
            if self.indice_actual >= len(self.entidades):
                self.indice_actual = max(0, len(self.entidades) - 1)
            
            # Guardar automáticamente
            self.guardar_entidades()
            
            # Actualizar vista
            self.mostrar_entidad_actual()
            
            messagebox.showinfo("Éxito", "Entidad eliminada correctamente")
    
    def recargar_entidades(self):
        """Recarga las entidades desde el archivo"""
        self.entidades = self.cargar_entidades()
        self.indice_actual = 0
        self.mostrar_entidad_actual()
        messagebox.showinfo("Éxito", "Entidades recargadas desde el archivo")
    
    def anadir_osm_wikidata(self):
        """Añade identificadores OSM y Wikidata a la entidad actual"""
        if not self.entidades:
            messagebox.showwarning("Advertencia", "No hay entidades para modificar")
            return
        
        osm_url = self.osm_entry.get().strip()
        wikidata_id = self.wikidata_entry.get().strip()
        
        if not osm_url and not wikidata_id:
            messagebox.showwarning("Advertencia", "Debes introducir al menos un enlace OSM o ID de Wikidata")
            return
        
        entidad = self.entidades[self.indice_actual]
        
        # Procesar OSM
        if osm_url:
            try:
                osm_uid = extract_osm_uid(osm_url)
                entidad['osm_id'] = osm_uid
                print(f"✅ OSM añadido: {osm_uid}")
            except ValueError as e:
                messagebox.showerror("Error OSM", f"URL de OSM inválida: {e}")
                return
        
        # Procesar Wikidata
        if wikidata_id:
            if wikidata_id.startswith('Q') and wikidata_id[1:].isdigit():
                entidad['wikidata_id'] = wikidata_id
                print(f"✅ Wikidata añadido: {wikidata_id}")
            else:
                messagebox.showerror("Error Wikidata", "ID de Wikidata debe tener formato Q123456")
                return
        
        # Guardar automáticamente
        self.guardar_entidades()
        
        # Actualizar vista
        self.mostrar_entidad_actual()
        
        # Limpiar campos
        self.osm_entry.delete(0, tk.END)
        self.wikidata_entry.delete(0, tk.END)
        
        messagebox.showinfo("Éxito", "Identificadores añadidos correctamente")

def iniciar_editor(input_path, output_path):
    """Función para iniciar el editor desde notebook"""
    root = tk.Tk()
    app = EntidadesEditor(root, input_path, output_path)
    root.mainloop() 