# 1. Inicializar el repositorio Git local
git init

# 2. Agregar todos los archivos (Git leerá el .gitignore y excluirá tus secretos de forma automática)
git add .

# 3. Crear tu primer commit de respaldo seguro
git commit -m "Feat: Lanzamiento oficial del portafolio con arquitectura TDD"

# 4. Renombrar tu rama principal a los estándares modernos
git branch -M main

# 5. Vincular tu computadora con tu repositorio de GitHub (Remplaza con tu URL real de GitHub)
git remote add origin https://github.com/tu_usuario/tu_repositorio_comercial.git

# 6. Subir tu código blindado a la nube de GitHub
git push -u origin main