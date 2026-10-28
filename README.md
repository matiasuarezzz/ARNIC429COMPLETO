# Gestor de envíos ARINC 429

Aplicación en español para registrar instrumentos y envíos, codificar una palabra ARINC 429 BNR de 32 bits y consultar el historial. Incluye interfaz web, API REST, persistencia MySQL y simulación por defecto.

## Requisitos y puesta en marcha

- Python 3.11 o superior.
- Docker con Compose, si se usará MySQL.
- Para conectar hardware real: adaptador/transmisor ARINC 429 apropiado y aislado; un puerto UART USB no genera señal ARINC 429 directamente.

1. Copiar `.env.example` a `.env` y mantener las opciones de hardware desactivadas inicialmente.
2. Iniciar MySQL con `docker compose up -d mysql`.
3. Crear entorno virtual e instalar el proyecto con `python -m pip install -e ".[test]"`.
4. Ejecutar la aplicación con `uvicorn app.main:app --reload`.
5. Abrir `http://127.0.0.1:8000` en el navegador.

Sin `.env`, la aplicación usa SQLite local como alternativa de desarrollo. Las tablas `instruments` y `shipments` se crean automáticamente al arrancar. La documentación interactiva de la API está disponible en `/docs`.

## Uso

- Agregar instrumentos indicando nombre, etiqueta, SDI, resolución y unidad. Etiqueta y SDI son parámetros de codificación, no selecciones de software para un equipo físico específico.
- Seleccionar instrumento y valor para crear un envío. Se almacena en la base de datos junto a la palabra hexadecimal y el resultado de salida.
- El historial permite consultar y eliminar envíos. La API ofrece CRUD completo para instrumentos y envíos: `POST`, `GET`, `PUT` y `DELETE` bajo `/api/instruments` y `/api/shipments`.

## Codificación y salidas físicas

La implementación construye una palabra BNR: etiqueta, SDI, datos, SSM, signo y paridad impar. En ARINC 429 el orden de bits en el cable y las convenciones de etiqueta dependen del estándar/perfil del equipo; verificar la definición de cada parámetro con la documentación del sistema destino antes de cualquier prueba.

El serial está deshabilitado por defecto. La opción `SERIAL_ENABLED=true` solamente escribe cuatro bytes en el puerto configurado; no produce niveles eléctricos ARINC 429 ni implementa temporización de bits o velocidades ARINC. Para una transmisión real se requiere un transmisor/adaptador ARINC 429 dedicado, aislado y validado en banco. No conectar directamente a aeronaves o sistemas operacionales. Ajustar el orden de bytes al manual del adaptador.

La opción `AUDIO_ENABLED=true` reproduce por la salida de audio del equipo un tono indicativo relacionado con el valor, a nivel digital bajo. Un auricular y su salida de audio no producen tensión DC calibrada, ni son un actuador de tensión seguro. Para generar una tensión física proporcional hace falta un DAC/acondicionador aislado con rango, carga y protección definidos; esa interfaz debe diseñarse y calibrarse según los requisitos del usuario y no se simula como una tensión real.

## Pruebas

Ejecutar `pytest`. Para habilitar audio opcional: instalar `python -m pip install -e ".[audio,test]"`.

## Límites

Este proyecto es un prototipo didáctico/de laboratorio, no equipo aeronáutico certificado. Se recomienda revisar las convenciones de palabra con un experto y probar únicamente en un banco controlado con interfaces certificadas.
