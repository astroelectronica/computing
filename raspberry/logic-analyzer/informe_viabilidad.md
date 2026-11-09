# Informe de viabilidad — Analizador lógico de 8 canales con Raspberry Pi 3

**Documento analizado:** `Raspberry_Pi_3_Logic_Analyzer_Master_Prompt_Claude_Free_Enhanced.md` (2 851 líneas, ~12 300 palabras, ~90 KB, 39 secciones)
**Fecha del estudio:** 9 de noviembre de 2026
**Entorno objetivo según el prompt:** Claude.ai, plan Claude Free, conversación web/escritorio (sin API, sin Claude Code)
**Estado:** estudio previo. No se ha generado ni ejecutado código de la aplicación. Solo se ha leído el prompt y se han hecho dos búsquedas web para contrastar el estado de `pigpio`.

---

## 1. Conclusión ejecutiva

| Pregunta | Respuesta |
|---|---|
| Clasificación (§0.6 del prompt) | **CONDICIONALMENTE VIABLE** |
| Comparación con la cuota de Claude Free | **NO VERIFICADA** (falta la pantalla Settings → Usage) |
| Recomendación | **GO condicionado**: solo para un **MVP reducido por etapas**. **NO-GO** para el alcance completo ("comparable a un analizador comercial") tal como está redactado |
| Carga estimada (escenario realista, proyecto completo) | ≈ 3,7 M tokens (entrada + salida) → ≈ 4,9 M con reserva del 30 % |
| Carga estimada (solo MVP) | ≈ 1,9 M tokens → ≈ 2,5 M con reserva |

Razones principales:

1. **El hardware limita más que Claude.** Una Raspberry Pi 3 con Linux, muestreada por GPIO, no da un analizador de propósito general. El prompt lo reconoce (§39), pero las secciones 9, 13, 14 y 38 piden funciones "comparables a un analizador comercial" que contradicen esa admisión.
2. **Claude Free no puede validar la mayor parte del producto.** No toca la Pi, no ejecuta GUI de forma fiable, probablemente no tiene red para instalar dependencias y no puede generar un `.exe` de Windows. Muchos criterios de aceptación (AT04, AT19, AT21, AT25, AT26…) dependen del usuario.
3. **El prompt se contradice en el control del flujo.** La sección 0 exige parar y pedir aprobación; las secciones 37 y 38 piden actuar como agente autónomo y "continuar hasta completar todo".
4. **El plan por etapas es sólido** y es lo que hace viable el proyecto: MVP primero, PoC físico antes de la GUI, checkpoints en `PROJECT_PROGRESS.md`.

---

## 2. Qué se ha hecho en este estudio y con qué fiabilidad

**Hecho:**
- Lectura íntegra de la sección 0 (control de uso), secciones 1–3 (rol, entorno, investigación de GPIO), 7 (motor de adquisición), 26–29 (pruebas, SO, empaquetado), 33–34 (calidad), y revisión por búsqueda de las secciones 4–6, 9–25, 30–32, 35–39.
- Dos búsquedas web sobre el estado de `pigpio` y sus parámetros de muestreo.

**No hecho (a propósito):** ninguna ejecución de código, ningún scaffolding, ninguna medición.

**Convención de fiabilidad usada en este informe:**
- **[VERIFICADO]** contrastado en una fuente consultada hoy (ver Anexo A).
- **[NO VERIFICADO]** procede de conocimiento general o de inferencia y debe confirmarse en la Etapa 1.
- **[DERIVADO]** cálculo a partir de valores verificados; no es una medición.

---

## 3. Descomposición del proyecto en paquetes de trabajo

| # | Paquete | Contenido principal | Depende de | Validable sin la Pi |
|---|---|---|---|---|
| WP0 | Viabilidad y plan | Este informe, `PROJECT_PROGRESS.md`, `DEVELOPMENT_LOG.md` | — | Sí |
| WP1 | Investigación hardware | Pinout, seguridad eléctrica, métodos de adquisición, plan de pruebas | Modelo exacto de Pi y SO | Parcial (documental) |
| WP1b | PoC físico | Captura mínima de 8 GPIO, medición de tasa, CPU, pérdidas | WP1 + Pi + generador de señal | **No** |
| WP2 | Arquitectura mínima | `pyproject.toml`, modelos de datos, interfaz de backend | WP1 | Sí |
| WP3 | Backend virtual | Generador determinista de 8 canales | WP2 | Sí |
| WP4 | Motor de adquisición | Bloques, buffers, marcas de tiempo, desbordes | WP3 | Sí (con simulación) |
| WP5 | GUI mínima | PyQt6, visor de formas de onda, zoom/pan | WP4 | **Limitado** (ver §6) |
| WP6 | Backend GPIO real | Integración con el método verificado | WP1b, WP4 | **No** |
| WP7 | Disparo básico | Flanco/nivel, captura pre/post limitada | WP4 | Sí |
| WP8 | Medidas | Periodo, frecuencia, ancho de pulso, ciclo de trabajo, cursores | WP4 | Sí |
| WP9 | Decodificador UART | Primer protocolo | WP8 | Sí |
| WP10 | SPI + I2C | Un decodificador cada vez | WP9 | Sí |
| WP11 | Sesiones y exportación | Sesión nativa, CSV, VCD | WP4 | Sí |
| WP12 | Avanzado | Disparo secuencial, CAN, LIN, auto-detección, jitter, búsqueda | MVP | Sí/No según función |
| WP13 | Integración y rendimiento | Regresión, memoria, rendimiento | Todo | **Parcial** |
| WP14 | Documentación y paquete | README, guías, PyInstaller, ZIP | Todo | **Parcial** |

---

## 4. Viabilidad técnica en la Raspberry Pi 3

### 4.1 Hechos verificados sobre `pigpio`

- **[VERIFICADO]** Su periodo de muestreo es de 1, 2, 4, 5, 8 o 10 µs, con 5 µs por defecto, y se fija al arrancar el demonio.
- **[VERIFICADO]** Ofrece notificaciones de cambio de estado para los GPIO 0–31 mediante una máscara de bits, y el campo `level` da el nivel de todos los GPIO a la vez. Esto encaja con el requisito de "instantánea común del banco de GPIO" del prompt (§7, §39.3).
- **[VERIFICADO]** No funciona en Raspberry Pi 5; el propio repositorio lo rechaza por diseño.
- **[VERIFICADO]** La versión empaquetada en Debian figura como 1.78.
- **[VERIFICADO, fuente secundaria: foros]** Se la considera una biblioteca "heredada" y específica de Raspberry Pi frente a `libgpiod`/`lgpio`; hay usuarios que la reinstalan a mano en sistemas nuevos y otros que migran a alternativas. Hay que confirmar en la Etapa 1 si el paquete existe en la versión de Raspberry Pi OS elegida.

### 4.2 Comparación de métodos de adquisición

| Método | Modelo de datos | Ventajas | Riesgos | Valoración preliminar |
|---|---|---|---|---|
| `pigpio` (DMA + notificaciones) | Eventos con marca de tiempo y nivel de 32 GPIO (equivale a muestreo cada 1–10 µs, **[NO VERIFICADO]** cómo se generan internamente) | Única opción de las evaluadas que probablemente da una instantánea común de los 8 canales | Biblioteca heredada; conflictos con PWM/PCM si se usan; la marca de tiempo es un contador de 32 bits que se reinicia periódicamente **[NO VERIFICADO]**; un lector lento puede perder eventos | **Candidata principal** |
| `libgpiod` / cdev | Eventos por línea con marca de tiempo del kernel | Mantenida; se instala por apt; marca de tiempo del kernel **[NO VERIFICADO]** | Cada canal genera su propio flujo de eventos; sin instantánea común; la cola puede desbordarse con señales densas | Respaldo para señales lentas |
| `RPi.GPIO` / GPIO Zero | Callbacks en Python | Sencillo | Latencia y planificación impredecibles. Según un foro, `RPi.GPIO` ya no funciona en Bookworm sin el shim `rpi-lgpio` | Solo control, no captura |
| Sondeo en Python | Lecturas repetidas | Ninguna práctica | Jitter alto; sin sincronía | Descartado (el prompt ya lo limita a línea base) |
| Extensión en C (demonio propio) | A definir | Mejor determinismo y menor CPU | Sale del alcance "solo Python" y complica la distribución | Opción si el PoC falla |

### 4.3 Envolvente de rendimiento realista **[DERIVADO, no medido]**

Con muestreo nominal de 5 µs (200 kS/s) o 1 µs (1 MS/s), y exigiendo 8 muestras por bit como mínimo prudente:

| Protocolo | A 200 kS/s (5 µs) | A 1 MS/s (1 µs) |
|---|---|---|
| UART | hasta ~25 kbaud (9600 y 19200 sí; 115200 no) | hasta ~125 kbaud (115200 justo) |
| I2C | no recomendable ni a 100 kHz | 100 kHz marginal; 400 kHz no |
| SPI | solo reloj de decenas de kHz | unos pocos cientos de kHz como mucho |
| LIN (19,2 kbps) | sí | sí |
| CAN (125 kbps, tras transceptor) | no | marginal |
| CAN (≥500 kbps) | no | no |

La tasa nominal de la biblioteca **no** garantiza una tasa sostenida de extremo a extremo (el propio prompt lo exige en §3.5). Estas cifras son techos teóricos y hay que medirlas con un generador de señal en la Etapa 1b.

**Consecuencia:** el MVP debe fijarse en torno a UART lento/medio, mediciones de pulso, y captura de señales de baja velocidad. Prometer SPI/I2C rápidos, CAN y "jitter" fiable con este hardware sería engañoso.

### 4.4 Seguridad eléctrica (resumen)

- Los GPIO son de 3,3 V y **no toleran 5 V** **[NO VERIFICADO en esta sesión, pero es la regla que fija el propio prompt y es coherente con la documentación oficial conocida]**.
- Hace falta masa común, y para señales de 5 V o industriales un adaptador de nivel o amortiguador con ancho de banda conocido.
- CAN y RS-485 son diferenciales: necesitan transceptor; nunca conectar a los GPIO.
- Candidatos de pines del prompt: BCM 4, 5, 6, 12, 13, 16, 17, 22. Están dentro de GPIO 0–31, compatible con las notificaciones de `pigpio`. Falta comprobar conflictos con el modelo exacto, HATs y la configuración de arranque (§3.3 del prompt).

### 4.5 Disparo y pre-disparo

Sin un mecanismo de disparo en hardware, el disparo es **por software sobre datos ya capturados**. El pre-disparo es posible solo mientras el búfer circular conserve los datos, y la posición del disparo tendrá una incertidumbre igual a la latencia de entrega más el periodo de muestreo. El "disparo secuencial" de §9.4 es factible como lógica sobre datos capturados, pero no como disparo en hardware.

---

## 5. Topología: recomendación

El prompt pide comparar (A) todo en la Pi y (B) servicio sin pantalla en la Pi + GUI en un PC.

| Criterio | A. Todo en la Pi 3 | B. Servicio en la Pi + GUI remota |
|---|---|---|
| CPU/RAM | La GUI compite con la adquisición en una máquina con 1 GB de RAM (Pi 3 B/B+) **[NO VERIFICADO]** | La Pi solo captura y transmite |
| Margen de adquisición | Menor; riesgo de perder eventos al redibujar | Mayor |
| Instalación | Hay que instalar PyQt6 y PyQtGraph en ARM; compatibilidad por verificar | La GUI se instala en un PC con ruedas estándar; la Pi solo necesita el servicio |
| Latencia de control | Mínima | Red local; irrelevante para captura diferida |
| Fiabilidad | Sin dependencia de red | Hay que tratar cortes de red (el prompt exige guardar datos en local, AT21) |
| Experiencia de uso | Pantalla y teclado en la Pi | Cómoda en un PC |

**Recomendación: B (servicio sin pantalla + GUI en PC)**, con captura en búfer local en la Pi y transferencia al terminar la captura. Es lo más coherente con "no comprometer la integridad de los datos" y reduce el riesgo en WP5. Debe confirmarse con medidas en el PoC. El modo A queda como opción experimental.

Impacto en el alcance: B añade un protocolo de red, autenticación básica y gestión de desconexión. Estimo +10–15 % de trabajo respecto a A, ya incluido en los totales de la sección 8.

---

## 6. Viabilidad del entorno Claude Free

### 6.1 Lo que no se puede asumir

Los siguientes puntos **no están verificados** y condicionan la viabilidad:

1. **¿Dispone Claude Free de ejecución de código y creación de archivos en este entorno?** El prompt exige ejecutar `pytest`, `ruff`, `mypy` y generar archivos y un ZIP. Si no está disponible, Claude solo puede escribir código en la conversación y el usuario tendría que ejecutarlo y pegar los resultados. Esto multiplica las iteraciones.
2. **Red.** En la sesión actual el entorno de ejecución tiene la red desactivada. Si ocurre lo mismo en el proyecto, `pip install PyQt6 pyqtgraph numpy scipy pandas pytest` no funcionará en el entorno de Claude, y la GUI y sus pruebas no podrán ejecutarse allí.
3. **Cuota.** Claude Free limita el uso por sesión y por ventanas móviles, sin una cifra fija pública. Un proyecto de millones de tokens exigirá muchas sesiones separadas por esperas.
4. **Contexto.** Un prompt de ~22–28 mil tokens reenviado en cada sesión consume una parte apreciable del contexto. El propio prompt lo advierte (§0.11): hay que tenerlo como archivo y citarlo por secciones.

### 6.2 Qué puede validar Claude y qué no

| Criterio de aceptación | ¿Lo puede validar Claude? |
|---|---|
| AT01–03, AT06–07, AT09, AT11–14, AT16–18, AT20, AT22–23 | Sí, con el backend virtual y pytest (si hay ejecución) |
| AT19 (GUI fluida), AT15 (grandes capturas navegables) | Solo parcialmente: requiere PyQt6 y un entorno gráfico |
| AT04, AT05 (adquisición real), AT21 | **No**: requieren la Pi física y señales reales |
| AT08, AT10 (pre/post-disparo, secuencial) | Sí en simulación; en real depende del hardware |
| AT24 (documentación = código) | Sí, mediante revisión |
| AT25, AT26 (instalación en Windows/Linux) | **No**: las debe ejecutar el usuario en sus máquinas |

PyInstaller no genera ejecutables de Windows desde un entorno Linux, así que el `.exe` de §29 **no puede producirlo Claude**; solo puede dejar el script de compilación para que lo ejecute el usuario en Windows.

**Consecuencia:** el criterio de §27 ("el proyecto debe pasar todos los tests de aceptación") es inalcanzable solo con Claude Free. Debe reescribirse como "pasa los tests verificables en simulación; el resto queda como pendiente de validación del usuario".

---

## 7. Problemas detectados en el prompt

### 7.1 Contradicciones

| Dónde | Problema | Resolución propuesta |
|---|---|---|
| §0.1 y §0.14 frente a §37 y §38 | §0 prohíbe generar código hasta tener aprobación; §37 manda "continuar implementando el proyecto completo" y §38 acaba con "empieza por la Fase 1… procede por todas las fases". | Mantener §0 como regla superior. Reescribir §37/§38 para que cada etapa termine en una puerta de aprobación |
| §0.14 frente a §3 y §38 | §0.14 pide como primera respuesta el informe de uso; §3 y §38 piden empezar por la investigación de GPIO | Orden: informe (esta fase) → investigación → PoC |
| §0.7 (Etapa 2: esqueleto mínimo, "no crear decenas de módulos vacíos") frente a §4.1 (árbol con decenas de módulos, incl. `can_decoder.py`, `lin_decoder.py`) | El árbol completo no debe crearse de golpe | Usar §4.1 como destino, no como plantilla inicial |
| §0.13 (una sola aprobación por etapa) frente a §37 (no preguntar nunca) | Dos normas de decisión | Mantener §0.13 |
| §27 (pasar los AT01–AT26) frente a §6.2 de este informe | Hay AT que Claude no puede ejecutar | Etiquetar cada AT por quién lo puede ejecutar |
| §1 y §38 ("funcionalidad comparable a analizadores comerciales", "el máximo técnicamente posible") frente a §39 y §34.18 | Se pide equivalencia comercial y a la vez se prohíbe prometerla | Sustituir por "el máximo que permita la envolvente medida" |

### 7.2 Restos y ambigüedades

- **§28, línea 2321:** "No conserves instrucciones ni dependencias del hardware de adquisición anterior". No existe un hardware anterior en este prompt; parece un resto de una versión previa. Conviene eliminarla o aclararla.
- **§2.1:** todo en inglés, incluidos la GUI, la documentación y el README, mientras que usted trabaja en español. Es coherente si es intencionado, pero conviene confirmarlo. La documentación del repositorio y este informe serían entonces de idioma distinto.
- **§2.2:** exige SciPy y Pandas además de NumPy. En una Pi 3 son pesadas de instalar; si se adopta la topología B, deberían ir solo en el cliente. Recomiendo marcarlas como "solo cliente" o "opcionales".
- **§0.4 y §0.3** piden estimar "sesiones" sin conocer la cuota; este informe lo hace de forma cualitativa (ver §8.3).
- **§3.1** deja sin fijar el modelo exacto (3 B, 3 B+ o 3 A+) y el SO. La RAM de la 3 A+ es menor que la de la 3 B/B+ **[NO VERIFICADO]**, lo que cambiaría la recomendación de topología.

### 7.3 Riesgos de alcance

- **Demasiados decodificadores a la vez** (UART, SPI, I2C, CAN, LIN, más "adicionales" en §13.6). El prompt ya prioriza UART primero; conviene mantenerlo.
- **Auto-detección de protocolo (§14) y análisis de jitter/correlación (§11.3)**: con una resolución de 1–10 µs y sin garantía de determinismo, los resultados serían de baja fiabilidad. Recomiendo diferirlos.
- **Búsqueda avanzada (§15), exportaciones adicionales (§16.1) y dispositivo GPIO virtual completo (§17)**: valiosos pero no necesarios en el MVP.

---

## 8. Estimación de tokens

### 8.1 Método y salvedades

- Se estima por separado entrada y salida de cada etapa.
- **Entrada** = prompt y archivos reenviados + contexto acumulado de la conversación + resultados de búsquedas y de herramientas. Es la parte que más crece, porque en cada turno se reprocesa el contexto previo. **No se distingue entre entrada nueva y entrada en caché**, porque Claude.ai no expone esa cifra al usuario.
- **Salida** = código, pruebas, documentación, informes y explicaciones. Hipótesis de partida: ~10 tokens por línea de código, ~13–15 mil líneas de Python de aplicación, ~7–9 mil líneas de pruebas, ~60–80 mil tokens de documentación.
- Son **estimaciones de planificación**, no medidas. No equivalen a un número garantizado de mensajes ni de uso de la suscripción.
- "Sesiones" = bloques de trabajo continuos, **no** periodos de cuota de Claude Free (se desconoce su tamaño).

### 8.2 Tabla por fases (cifras en miles de tokens, escenario realista)

| Fase | Alcance | Entrada | Salida | Total | Sesiones/interacciones | Confianza | Dependencias |
|---|---|---:|---:|---:|---|---|---|
| 0 | Viabilidad, plan, ficheros de progreso | 30 k | 12 k | 42 k | 1–2 | Alta | — |
| 1 | Investigación de hardware y documentos de viabilidad | 120 k | 30 k | 150 k | 3–5 | Media | Modelo de Pi y SO |
| 1b | PoC físico (script de captura, informe) | 40 k | 25 k | 65 k | 3–6 (con ciclos de medición del usuario) | **Baja** | Pi, cableado, generador |
| 2 | Esqueleto y modelos de datos | 60 k | 35 k | 95 k | 2–3 | Media | Fase 1 |
| 3 | Backend virtual y vectores de prueba | 80 k | 45 k | 125 k | 2–4 | Media | Fase 2 |
| 4 | Motor de adquisición e integridad | 150 k | 70 k | 220 k | 4–6 | Media | Fase 3 |
| 5 | GUI mínima y visor | 250 k | 110 k | 360 k | 6–10 | **Baja** | Fase 4; PyQt6 |
| 6 | Integración con GPIO real | 150 k | 60 k | 210 k | 4–8 | **Baja** | Fase 1b y 4 |
| 7 | Disparo básico y captura | 100 k | 40 k | 140 k | 3–5 | Media | Fase 4 |
| 8 | Medidas y detección de flancos | 120 k | 50 k | 170 k | 3–5 | Media | Fase 4 |
| 9 | Decodificador UART | 90 k | 40 k | 130 k | 2–4 | Media-alta | Fase 8 |
| 10 | SPI e I2C | 180 k | 80 k | 260 k | 4–6 | Media | Fase 9 |
| 11 | Sesiones, CSV, VCD | 150 k | 70 k | 220 k | 3–5 | Media | Fase 4 |
| 12 | Funciones avanzadas (cada una con su puerta) | 450 k | 200 k | 650 k | 10–20 | **Baja** | MVP |
| 13 | Integración, regresión, rendimiento | 400 k | 120 k | 520 k | 6–12 | **Baja** | Todo |
| 14 | Documentación, empaquetado, entrega | 250 k | 130 k | 380 k | 5–8 | Media | Todo |
| **Total** | | **≈ 2 620 k** | **≈ 1 117 k** | **≈ 3 740 k** | **≈ 60–110** | | |

**MVP (§0.8): fases 0 a 9 y 11** → entrada ≈ 1 340 k, salida ≈ 587 k, total ≈ **1 930 k**, con ≈ 38–65 interacciones.

### 8.3 Resumen por escenarios

| Escenario | Total estimado | Reserva | Carga global con reserva | Hipótesis principales |
|---|---:|---:|---:|---|
| Optimista | ≈ 2,4 M | 25 % (≈ 0,6 M) | ≈ 3,0 M | Pi y SO definidos pronto; `pigpio` funciona sin sorpresas; pocas correcciones; ejecución de código disponible |
| Realista | ≈ 3,7 M | 30 % (≈ 1,1 M) | ≈ 4,9 M | Integración normal; GUI con iteraciones; PoC con 1–2 rondas de ajuste |
| Pesimista | ≈ 6,0 M | 25 % (≈ 1,5 M) | ≈ 7,5 M | `pigpio` no disponible o poco fiable en el SO elegido (hay que cambiar de método); GUI problemática por falta de entorno gráfico; muchos ciclos de depuración con resultados pegados a mano |
| Solo MVP (realista) | ≈ 1,9 M | 30 % (≈ 0,6 M) | ≈ 2,5 M | Sin fase 12 ni empaquetado completo |

**Por qué la reserva:** (1) las fases 1b, 5, 6, 12 y 13 tienen confianza baja; (2) la depuración en Claude.ai sin ejecución integrada obliga a repetir ciclos; (3) el contexto acumulado encarece cada turno; (4) el hardware real puede invalidar decisiones ya tomadas (§0.13: cambio de arquitectura → reaprobación).

**Qué puede cambiar mucho las cifras:** disponibilidad de ejecución de código; pegar logs largos; tamaño de los ficheros que se vuelven a leer; cambio de topología; cambio de método de adquisición; pedir "reescribe el fichero entero" en lugar de parches.

### 8.4 Categorías de tokens que no se informan

Claude.ai no expone al usuario tokens en caché ni de razonamiento. No se inventan cifras para ellas.

---

## 9. Plan por etapas recomendado

1. **Etapa 0 (esta):** informe + decisiones abiertas (§12). Sin código.
2. **Etapa 1:** investigación documental de `pigpio`/`libgpiod`/SO, y `docs/*` de §3.7. Sin código de adquisición.
3. **Etapa 1b:** PoC físico mínimo en la Pi. **Puerta**: informe de rendimiento real. Si falla, cambio de método con reaprobación.
4. **Etapas 2–4:** esqueleto mínimo, backend virtual, motor de adquisición. Primeras pruebas automáticas.
5. **Etapa 5 con topología B:** visor mínimo en el PC.
6. **Etapa 6:** integración con la Pi real.
7. **Etapas 7–9 y 11:** disparo básico, medidas, UART, sesiones/CSV/VCD.
8. **Puerta MVP.**
9. **Después, una a una:** SPI/I2C → VCD → disparo secuencial → CAN/LIN (solo con transceptor y tasa suficiente) → el resto.

**MVP propuesto (más estricto que §0.8):**
- Captura de 8 canales con tasa medida y declarada.
- Visor con zoom y desplazamiento.
- Flancos y medidas básicas con incertidumbre mostrada.
- Disparo por flanco/nivel con aviso de incertidumbre.
- UART a velocidades que la envolvente medida permita.
- Guardado de sesión y CSV.
- Informe de pérdidas y límites visible en la interfaz.

**Diferir explícitamente:** CAN, LIN, auto-detección de protocolo, correlación/jitter, disparo secuencial, búsqueda avanzada, `.exe` automático.

---

## 10. Lo que usted debe comprobar manualmente

En Claude.ai, **Settings → Usage** (el nombre puede variar). Indique solo lo que se muestra:

1. Uso o capacidad restante de la sesión actual, si se muestra.
2. Si ha alcanzado algún límite.
3. Hora de reinicio o próxima disponibilidad.
4. Cualquier límite semanal o móvil.
5. Modelo seleccionado.

Además, conviene comprobar en su cuenta:
- Si están disponibles la **ejecución de código y creación de archivos** (Settings → Capabilities, o el nombre actual).
- Si puede **adjuntar archivos** en una nueva conversación y cuántos.

No hace falta compartir credenciales, facturación ni datos personales. Hasta que lo haga, la comparación con la cuota queda **NO VERIFICADA**.

---

## 11. Riesgos principales

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| `pigpio` no disponible o inestable en el SO elegido | Media | Alto | Elegir SO con paquete verificado; plan B con `libgpiod`; plan C con demonio en C |
| Tasa sostenida real muy inferior a la nominal | Alta | Alto | PoC antes de la GUI; publicar solo cifras medidas |
| Pérdida de eventos con señales densas | Media | Alto | Contadores de secuencia y avisos; limitar canales o tasa |
| GUI no probable en el entorno de Claude | Alta | Medio | Separar lógica y presentación; pruebas sin GUI; validación del usuario |
| Cuota de Claude Free insuficiente por sesión | **Desconocida** | Alto | Etapas pequeñas, checkpoints, no reenviar el prompt entero |
| Falta de generador de señales | Media | Medio | Bucle GPIO de salida a entrada con límites declarados |
| Daño eléctrico (5 V en GPIO) | Baja | **Crítico** | Tabla de cableado segura; adaptación de nivel; rechazar configuraciones inseguras |
| Deriva de alcance hacia "comercial" | Alta | Alto | MVP congelado y reaprobación para cada extra |
| Contradicciones del prompt (autonomía vs. aprobación) | Alta | Medio | Corregir el prompt antes de continuar |

---

## 12. Recomendación GO / NO-GO y decisiones que necesito

**Recomendación: GO condicionado.**
- **GO** para las etapas 0 a 4 y el PoC físico, con el MVP reducido de la sección 9.
- **NO-GO** para el alcance completo de las 39 secciones como entregable único bajo Claude Free.
- **Condiciones:** (a) corregir las contradicciones de §7.1; (b) confirmar capacidades de su cuenta (§10); (c) aceptar un calendario de varias sesiones separadas por límites de uso; (d) aceptar que parte de la validación la hará usted.

**Información mínima que necesito para afinar el estudio:**
1. **Modelo exacto de la Pi** (3 B, 3 B+ o 3 A+) y el **SO/kernel** que piensa usar (32 o 64 bits).
2. **¿Tiene un generador de señales o analizador de referencia** para medir la tasa real?
3. **¿Aprueba la topología B** (servicio en la Pi + GUI en el PC)? ¿Qué sistema operativo tiene el PC?
4. **Idioma:** ¿se mantiene todo el código y documentación en inglés (§2.1)?
5. Lo que muestre **Settings → Usage** y si tiene ejecución de código y archivos.

**Siguiente paso, solo tras su aprobación explícita:** Etapa 1 (investigación documental), sin código de adquisición.

---

## Anexo A — Fuentes consultadas hoy

| Fuente | Qué respalda |
|---|---|
| Documentación de `pigpiod_if2` (manpage Debian) | Periodos de muestreo 1/2/4/5/8/10 µs, 5 µs por defecto; notificaciones por máscara de GPIO con nivel de todos los pines |
| Código de `pigpio.py` 1.78 (sources.debian.org) | Versión de la biblioteca; flags de notificación; `notify_open/begin/pause/close` |
| Repositorio `joan2937/pigpio`, incidencia #589 | `pigpio` no soporta Raspberry Pi 5 |
| Foros de Node-RED, DietPi y openHAB (fuentes secundarias) | Carácter heredado de `pigpio`; cambios en `RPi.GPIO` y los nombres de los dispositivos GPIO en SO recientes; migración a `lgpio`/`rgpio` |

**Pendiente de verificar en la Etapa 1 (todo lo marcado [NO VERIFICADO]):** disponibilidad de `pigpio` en el SO elegido, formato exacto de las notificaciones y comportamiento del contador de tiempo, capacidades de `libgpiod` v2, tensiones y corrientes límite de los GPIO en la hoja de datos oficial, RAM y reloj de cada variante de Pi 3, compatibilidad de PyQt6 con ARM de 32/64 bits.

---

*Este informe es una estimación de planificación. Ninguna cifra de rendimiento está medida y ninguna cifra de tokens es un compromiso de consumo.*
