# AgriSphere - Backend API

Backend de **AgriSphere**, plataforma orientada al control de personal, asistencias y monitoreo agrícola dentro de invernaderos.

El servidor fue desarrollado con **Python y FastAPI** y utiliza **PostgreSQL** como sistema de persistencia. La API es consumida por la aplicación móvil Android de AgriSphere.

---

# Funciones principales

El backend centraliza la lógica relacionada con:

- autenticación de usuarios;
- sesiones mediante JWT;
- control de acceso por roles;
- geolocalización y validación de geocercas;
- generación y validación de códigos QR dinámicos;
- registro de entradas y salidas;
- reportes de asistencia;
- permisos de trabajadores;
- consulta de empleados;
- administración de invernaderos;
- monitoreo agrícola;
- catálogos de observables;
- evidencias fotográficas;
- recuperación de contraseña mediante OTP.

---

# Arquitectura

AgriSphere utiliza una arquitectura cliente-servidor.

```text
Aplicación Android
        │
        │ HTTP / REST
        ▼
     FastAPI
        │
        │ SQLAlchemy Async
        ▼
    PostgreSQL
```

La aplicación Android no se conecta directamente con PostgreSQL.

Toda la autenticación, autorización, validación y persistencia de información se realiza mediante este backend.

---

# Tecnologías utilizadas

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy Async
- asyncpg
- Pydantic
- Pydantic Settings
- bcrypt
- JSON Web Tokens (JWT)
- python-jose
- HMAC SHA-256
- python-multipart

El proyecto fue desarrollado y probado localmente utilizando Python 3.14.

---

# Requisitos

Antes de descargar el proyecto se necesita tener instalado:

- Git.
- Python.
- PostgreSQL.
- pgAdmin o alguna herramienta equivalente para administrar PostgreSQL.

También se recomienda utilizar:

- Visual Studio Code.
- PowerShell en Windows.

---

# Instalación

## 1. Clonar el repositorio

Desde una terminal:

```bash
git clone URL_DEL_REPOSITORIO
```

Entrar a la carpeta:

```bash
cd backend
```

También se puede descargar el proyecto como ZIP desde GitHub y descomprimirlo.

---

# 2. Crear el entorno virtual

Desde la carpeta raíz del backend:

```powershell
py -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Cuando el entorno está activo, la terminal mostrará algo parecido a:

```text
(.venv) PS C:\ruta\del\proyecto\backend>
```

## Error al activar el entorno virtual

Si PowerShell muestra un mensaje indicando que la ejecución de scripts está deshabilitada, ejecutar una vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Cerrar y volver a abrir PowerShell y activar nuevamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 3. Instalar las dependencias

Con el entorno virtual activo:

```powershell
python -m pip install --upgrade pip
```

Después:

```powershell
pip install -r requirements.txt
```

Las dependencias se encuentran definidas en:

```text
requirements.txt
```

No es necesario instalarlas individualmente.

---

# 4. Crear la base de datos PostgreSQL

## Importante

El backend **crea automáticamente las tablas**, pero **no crea automáticamente la base de datos PostgreSQL**.

Por lo tanto, primero debe existir una base de datos vacía.

Se puede crear desde pgAdmin:

```text
Servers
→ PostgreSQL
→ Databases
→ Create
→ Database
```

Por ejemplo:

```text
Database: agrisphere
Owner: postgres
```

También se puede crear mediante SQL:

```sql
CREATE DATABASE agrisphere;
```

Una vez creada la base de datos no es necesario crear manualmente las tablas.

FastAPI se encargará de hacerlo al iniciar.

---

# 5. Configurar las variables de entorno

En la raíz del proyecto existe:

```text
.env.example
```

Crear una copia llamada:

```text
.env
```

Desde PowerShell se puede hacer con:

```powershell
Copy-Item .env.example .env
```

Después abrir `.env`.

La estructura es:

```env
DATABASE_URL=postgresql+asyncpg://postgres:TU_PASSWORD@localhost:5432/agrisphere
SECRET_KEY=TU_SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## DATABASE_URL

Contiene los datos necesarios para conectarse a PostgreSQL.

Formato:

```text
postgresql+asyncpg://USUARIO:CONTRASEÑA@HOST:PUERTO/BASE_DE_DATOS
```

Ejemplo:

```env
DATABASE_URL=postgresql+asyncpg://postgres:mi_password@localhost:5432/agrisphere
```

Si la contraseña de PostgreSQL contiene caracteres especiales, puede ser necesario codificarlos correctamente dentro de la URL.

---

## SECRET_KEY

Se utiliza para firmar:

- tokens JWT;
- tokens de recuperación;
- códigos QR dinámicos.

Debe ser una cadena larga y difícil de adivinar.

Se puede generar una desde Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copiar el resultado dentro de `.env`:

```env
SECRET_KEY=resultado_generado
```

La misma `SECRET_KEY` debe mantenerse mientras los tokens existentes necesiten seguir siendo válidos.

---

## ALGORITHM

Actualmente:

```env
ALGORITHM=HS256
```

---

## ACCESS_TOKEN_EXPIRE_MINUTES

Indica cuánto tiempo permanece vigente un JWT de sesión.

La configuración utilizada durante el desarrollo es:

```env
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

Esto equivale a 8 horas.

---

# 6. ¿La base de datos se crea automáticamente?

La respuesta se divide en dos partes.

## La base de datos PostgreSQL

**No.**

Debe crearse manualmente una vez:

```sql
CREATE DATABASE agrisphere;
```

## Las tablas

**Sí.**

Al iniciar FastAPI se ejecuta:

```python
Base.metadata.create_all
```

Por lo tanto, si la conexión a PostgreSQL es correcta, SQLAlchemy comprueba las tablas registradas y crea las que no existan.

No es necesario ejecutar manualmente un archivo SQL para crear las tablas en una base nueva.

---

# 7. ¿Los datos se cargan automáticamente?

**No completamente.**

El proyecto incluye:

```text
seed.py
```

Este script permite crear algunos datos iniciales de prueba y también verifica la existencia de las tablas.

Puede ejecutarse con:

```powershell
python seed.py
```

Sin embargo, el `seed.py` actual es un **seed mínimo de desarrollo**.

No llena automáticamente toda la información necesaria para reproducir la base utilizada durante las pruebas de la aplicación.

Una base completamente nueva puede requerir datos en tablas como:

```text
usuarios
expedientes_trabajadores
empresas
invernaderos
zonas_invernadero
catalogo_observables
```

y posteriormente irá generando información en:

```text
registro_asistencias
permisos_asistencia
reportes_monitoreo
reportes_observables
evidencias_monitoreo
recuperacion_password
```

Por esta razón:

```text
crear base PostgreSQL
        ↓
configurar .env
        ↓
iniciar FastAPI
        ↓
tablas creadas automáticamente
        ↓
cargar/configurar datos iniciales
        ↓
utilizar la aplicación
```

El script `seed.py` puede utilizarse como apoyo para desarrollo, pero no debe considerarse actualmente una carga completa de datos de producción.

---

# 8. Ejecutar el servidor

Con:

- PostgreSQL iniciado;
- base de datos creada;
- `.env` configurado;
- entorno virtual activo;
- dependencias instaladas;

ejecutar:

```powershell
uvicorn app.main:app --reload
```

Si todo funciona correctamente aparecerá algo parecido a:

```text
Uvicorn running on http://127.0.0.1:8000
```

El parámetro:

```text
--reload
```

se utiliza durante desarrollo para reiniciar el servidor automáticamente cuando cambia el código.

---

# 9. Comprobar que el servidor funciona

Abrir:

```text
http://127.0.0.1:8000/
```

La API debe responder indicando que el servidor está en línea.

---

# 10. Swagger / documentación de la API

FastAPI genera automáticamente una interfaz para probar los endpoints.

Abrir:

```text
http://127.0.0.1:8000/docs
```

Desde Swagger es posible:

- consultar los endpoints;
- revisar los parámetros;
- enviar solicitudes;
- consultar respuestas;
- probar autenticación Bearer;
- revisar códigos de error.

También se encuentra disponible la especificación OpenAPI generada por FastAPI.

---

# Estructura principal

```text
backend/
│
├── app/
│   │
│   ├── auth/
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── utils.py
│   │
│   ├── modulos/
│   │   │
│   │   ├── dashboard/
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── empresa/
│   │   │   ├── models.py
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── escaner/
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   │
│   │   └── monitoreo/
│   │       ├── models.py
│   │       ├── router.py
│   │       └── schemas.py
│   │
│   ├── utils/
│   │   └── qr_security.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── static/
│   └── fotos_monitoreo/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── seed.py
└── README.md
```

---

# Módulos

## Autenticación

Prefijo:

```text
/api/auth
```

Incluye operaciones relacionadas con:

- login;
- usuarios;
- trabajadores;
- perfil;
- QR del trabajador;
- asistencia;
- permisos;
- recuperación de contraseña.

---

## Escáner

Prefijo:

```text
/api/escaner
```

Permite:

- validar códigos QR;
- consultar asignaciones de trabajadores.

Los códigos son firmados utilizando la `SECRET_KEY` configurada en el backend.

---

## Dashboard

Prefijo:

```text
/api/dashboard
```

Proporciona información resumida utilizada por la aplicación móvil.

---

## Monitoreo

Prefijo:

```text
/api/monitoreo
```

Incluye:

- creación de reportes;
- consulta de historial;
- catálogo de observables;
- zonas de invernadero;
- evidencias fotográficas.

---

## Empresa

Prefijo:

```text
/api/empresa
```

Contiene operaciones relacionadas con:

- configuración de empresa;
- parámetros;
- registros de reloj.

---

# Roles

Los roles principales definidos por el sistema son:

```text
Usuario
Jefe Área
Oficina
```

Los endpoints protegidos utilizan validación RBAC.

Una solicitud protegida debe incluir:

```http
Authorization: Bearer TOKEN_JWT
```

Si el JWT no existe o es inválido se devuelve normalmente:

```text
401 Unauthorized
```

Si el JWT es válido pero el rol no tiene permiso:

```text
403 Forbidden
```

---

# Autenticación

El login genera un JWT que contiene información como:

```text
sub
rol
device_id
iat
exp
```

El token está firmado mediante:

```text
SECRET_KEY
ALGORITHM
```

configurados en `.env`.

---

# Geolocalización y geocerca

El backend permite almacenar en la empresa:

```text
geocerca_latitud
geocerca_longitud
geocerca_radio_metros
```

Durante operaciones móviles se puede comprobar la distancia entre:

```text
ubicación del dispositivo
        ↓
ubicación configurada de la empresa
```

El cálculo se realiza en metros mediante coordenadas geográficas.

Si el usuario se encuentra fuera del radio permitido, el backend puede responder:

```text
403 Forbidden
```

---

# QR dinámico

El QR del trabajador incluye:

```text
usuario
timestamp
firma
```

La firma se genera utilizando HMAC SHA-256 y la `SECRET_KEY`.

El código tiene una vigencia corta.

El servidor vuelve a calcular la firma al escanear el QR para comprobar que no haya sido modificado.

Un QR expirado o con una firma incorrecta es rechazado.

---

# Asistencias

El backend permite registrar:

```text
check-in
check-out
```

y generar información relacionada con:

- horas trabajadas;
- retardos;
- horas extra;
- salida anticipada;
- permisos.

Los registros se almacenan en PostgreSQL.

---

# Monitoreo agrícola

Un reporte de monitoreo puede almacenar:

- usuario;
- invernadero;
- zona;
- sección;
- temperatura;
- humedad;
- tipo de observación;
- especie;
- nivel de infestación;
- observables;
- notas.

Los observables asociados se guardan de forma relacionada con el reporte principal.

---

# Evidencias fotográficas

Las imágenes enviadas desde la aplicación Android se almacenan localmente en:

```text
static/fotos_monitoreo/
```

El directorio se crea automáticamente si no existe.

Los archivos reciben nombres únicos para evitar colisiones.

Las fotografías generadas durante pruebas locales no deben subirse al repositorio.

---

# Recuperación de contraseña

El backend implementa el flujo:

```text
correo
  ↓
generar OTP
  ↓
verificar OTP
  ↓
generar reset token
  ↓
cambiar contraseña
  ↓
invalidar token
```

## Importante en desarrollo

Actualmente el envío de correo se encuentra **simulado**.

El código OTP se muestra en la terminal donde está ejecutándose Uvicorn.

Durante una prueba se verá un mensaje similar a:

```text
[SIMULACIÓN EMAIL] Código OTP para usuario@correo.com: XXXXXX
```

No existe todavía un proveedor SMTP o servicio de correo configurado.

---

# Contraseñas

Las contraseñas no se almacenan como texto plano.

El backend utiliza bcrypt para:

```text
contraseña
    ↓
hash bcrypt
    ↓
PostgreSQL
```

La nueva contraseña utilizada durante una recuperación debe cumplir las reglas de validación definidas por el backend.

---

# Aplicación Android

Este repositorio contiene únicamente el backend.

La aplicación móvil se mantiene en un repositorio independiente.

En Android Emulator la aplicación utiliza normalmente:

```text
http://10.0.2.2:8000/
```

para comunicarse con este servidor cuando FastAPI se encuentra ejecutándose en la misma computadora.

---

# Utilizar un teléfono físico

Para aceptar conexiones desde otro dispositivo de la red local, iniciar Uvicorn con:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Después la aplicación Android debe utilizar la IP local de la computadora.

Ejemplo:

```text
http://192.168.1.100:8000/
```

El teléfono y la computadora deben encontrarse en la misma red.

También puede ser necesario permitir Python/Uvicorn a través del Firewall de Windows.

---

# Problemas comunes

## Uvicorn no inicia

Comprobar:

1. que el entorno virtual esté activo;
2. que las dependencias estén instaladas;
3. que `.env` exista;
4. que PostgreSQL esté iniciado;
5. que `DATABASE_URL` sea correcta.

---

## Error al conectar PostgreSQL

Revisar:

```env
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/base
```

Comprobar:

- usuario;
- contraseña;
- puerto;
- nombre de la base;
- servicio de PostgreSQL.

---

## La base existe pero no tiene tablas

Iniciar:

```powershell
uvicorn app.main:app --reload
```

El proceso de inicio ejecuta automáticamente la creación de las tablas faltantes.

---

## Error `relation does not exist`

Puede indicar que:

- la aplicación se conectó a otra base;
- `DATABASE_URL` apunta al nombre incorrecto;
- FastAPI no terminó de iniciar correctamente.

---

## Error 401

Indica generalmente:

- JWT ausente;
- JWT inválido;
- JWT expirado.

Volver a iniciar sesión para obtener un token nuevo.

---

## Error 403

Indica normalmente:

- rol sin permisos;
- usuario fuera de geocerca;
- operación no permitida para el perfil actual.

Revisar el `detail` de la respuesta.

---

## Error 422

FastAPI devuelve `422` cuando el JSON, parámetros o formulario recibido no coincide con el esquema esperado.

Revisar la documentación:

```text
http://127.0.0.1:8000/docs
```

---

## El OTP no llega al correo

Es el comportamiento esperado en el entorno actual.

El envío está simulado.

Revisar la terminal donde está ejecutándose Uvicorn para encontrar:

```text
[SIMULACIÓN EMAIL]
```

---

# Modificaciones en los modelos

Actualmente el proyecto no utiliza un sistema de migraciones como Alembic.

`Base.metadata.create_all()` crea tablas que todavía no existen, pero **no realiza migraciones completas sobre tablas ya creadas**.

Si durante desarrollo se modifica la estructura de un modelo, puede ser necesario:

- modificar manualmente la tabla;
- eliminar y volver a crear la base de datos de desarrollo;
- o implementar una migración.

No eliminar una base con información importante sin generar primero un respaldo.

---

# Seguridad del repositorio

Nunca se debe subir:

```text
.env
.venv/
__pycache__/
*.pyc
```

Tampoco deben publicarse:

- contraseñas de PostgreSQL;
- `SECRET_KEY`;
- JWT reales;
- credenciales;
- archivos privados;
- fotografías de prueba o producción.

El archivo que sí puede permanecer en el repositorio es:

```text
.env.example
```

porque únicamente describe qué variables necesita el proyecto y no debe contener credenciales reales.

---

# Flujo rápido desde cero

Para una instalación local nueva:

```text
1. Instalar Python
2. Instalar PostgreSQL
3. Clonar el repositorio
4. Crear .venv
5. Activar .venv
6. Instalar requirements.txt
7. Crear la base PostgreSQL
8. Copiar .env.example como .env
9. Configurar DATABASE_URL y SECRET_KEY
10. Ejecutar uvicorn app.main:app --reload
11. Verificar http://127.0.0.1:8000/docs
12. Cargar los datos iniciales necesarios
13. Ejecutar la aplicación Android
```

Comandos principales:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

---

# Estado actual

La versión actual integra:

- API REST con FastAPI;
- PostgreSQL asíncrono;
- creación automática de tablas;
- autenticación JWT;
- RBAC;
- hashing de contraseñas;
- recuperación mediante OTP;
- geolocalización;
- geocerca;
- QR dinámicos firmados;
- validación de QR;
- asistencias;
- permisos;
- empleados;
- invernaderos;
- monitoreo agrícola;
- evidencias fotográficas;
- dashboard.

El backend se encuentra preparado actualmente para ejecución y pruebas en entorno local.