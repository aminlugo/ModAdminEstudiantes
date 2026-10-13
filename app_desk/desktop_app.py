import webview

def main():
    # URL directa de tu aplicación desplegada en Render
    url_cloud = "https://modadminestudiantes.onrender.com/"
    
    # Crear la ventana nativa de escritorio apuntando a la nube
    webview.create_window(
        title="Módulo de Administración de Estudiantes",
        url=url_cloud,
        width=1250,
        height=700,
        resizable=True,
        min_size=(800, 600)
    )
    
    # Iniciar la interfaz gráfica
    webview.start()

if __name__ == '__main__':
    main()

#comando para compilara app de escritorio: pyinstaller --noconsole --onefile desktop_app.py