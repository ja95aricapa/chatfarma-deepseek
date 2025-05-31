===========================================
          ChatFarma-DeepSeek en USB
            (Windows 11 – Sin Docker)
===========================================

1. Inserta la USB en el PC con Windows 11.
2. Abre la carpeta "backend" y haz doble clic en "model-server.exe".
   - Verás una ventana de consola: el servidor REST se está levantando (DeepSeek-R1).
   - Espera a que aparezca en la consola algo como "Uvicorn running".

3. Abre la carpeta "chat-app" y haz doble clic en "ChatFarma.exe".
   - Se iniciará la aplicación de chat.
   - Si el firewall pregunta, permite el acceso local (localhost:8000).

4. Uso diario:
   a) **Actualizar conocimientos de farmacología**:  
      - Coloca tus PDFs, Docs, Excel o imágenes relevantes en "backend/data_to_train/".  
      - En la app, presiona "Actualizar conocimientos" para indexar todo en DeepSeek-R1.  

   b) **Consultar formulaciones**:  
      - Escribe tu pregunta en la caja de texto y presiona "Enviar".  
      - La respuesta vendrá con contexto de los artículos indexados.  

   c) **Cargar historia clínica de un paciente**:  
      - En la app, pulsa "Subir historia clínica" y elige el PDF/Doc/imagen.  
      - Ese contexto vivirá SOLO en RAM (no se guarda a disco) y se usará en la sesión actual.  

5. Para borrar historias clínicas y evitar que contaminen otras consultas:
   - Cierra la ventana de ChatFarma (la app llamará internamente a `/clear_session`).  

6. Cuando termines de usar:
   - Cierra ChatFarma (limpia sesión de pacientes).  
   - Ve a "backend" y haz doble clic en "stop_backend.bat" para detener el servidor.  
   - Extrae la USB con seguridad: no quedan procesos ni datos de pacientes en disco.

-------------------------------------------
Requisitos previos (solo 1 vez por PC):
- Tener Windows 11 instalado.
- No necesitas instalar Docker ni Python: todo está en la USB.
-------------------------------------------
