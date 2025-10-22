import os

class Config:
    # Obtener la clave secreta de la variable de entorno
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_dev')
    
    # Configuración de SQLite para desarrollo (datos no persistentes en Render)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ----------------------------------------------------------------------
    # IMPORTANTE: Configuración para PostgreSQL en Render
    # Si vas a desplegar en Render y usar su DB gratuita, 
    # la URL debe obtenerse del entorno y se vería así:
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    # Recomiendo configurar la URL real de Render en tus variables de entorno.
    # ----------------------------------------------------------------------

# Puedes añadir otras clases de configuración (por ejemplo, ProductionConfig)
# si tienes configuraciones diferentes para desarrollo y producción.
