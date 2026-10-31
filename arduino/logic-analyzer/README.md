# Analizador lógico de 8 canales con Arduino Uno R3

Analizador lógico de bajo coste formado por:

- **Firmware** para Arduino Uno R3 (`arduino_logic_analyzer/arduino_logic_analyzer.ino`): captura 8 canales digitales en bloques de hasta 1024 muestras y los envía por USB.
- **Aplicación de PC** en Python (`pc_gui/logic_analyzer_gui.py`): configura la captura, dibuja las formas de onda y ofrece herramientas de medida y exportación.

La interfaz gráfica y los comentarios del código están en inglés, como se pidió.

```
logic_analyzer/
├── README.md
├── arduino_logic_analyzer/
│   └── arduino_logic_analyzer.ino     <- firmware (Arduino IDE)
└── pc_gui/
    ├── logic_analyzer_gui.py          <- aplicación de PC
    └── requirements.txt
```

---

## 1. Características

| Función | Detalle |
|---|---|
| Canales | 8 entradas, cada una se puede activar/desactivar y **renombrar** |
| Conversión numérica | Carril "BUS" con el valor de los canales activos en **binario, decimal, hexadecimal y octal**; también en la lectura de los cursores y en el CSV |
| Escala de tiempo | **Time/div configurable** (lista 1-2-5 o valor escrito, p. ej. `250us`, `1.5 ms`), 10 divisiones |
| Zoom | Botones Zoom +/−, Fit, "To cursors", rueda del ratón (centrada en el puntero), barra de desplazamiento, Pan, arrastre con botón central |
| Cursores | Cursor A (clic izquierdo) y B (clic derecho o Shift+clic), arrastrables. Muestran ΔT, 1/ΔT, nº de muestras y el valor del bus y de cada canal en cada cursor |
| Sample rate | Configurable de 1 Hz a 250 kHz (ver límites) |
| Threshold | Modo analógico con umbral ajustable de 0 a 5 V (ver limitaciones) |
| Trigger | Flanco de subida, bajada, cualquier flanco, nivel alto, nivel bajo; canal seleccionable; pre-trigger 0-90 %; modo Auto/Normal |
| Control | Run (continuo), Single, Stop y **Pause display** (congela la pantalla) |
| Exportar | **PNG** de la gráfica, **PDF** (tema claro para imprimir) y **CSV** con los datos |
| Modo DEMO | Dispositivo simulado para probar la interfaz sin hardware |

---

## 2. Requisitos

### Hardware
- Arduino Uno R3 (o compatible con ATmega328P a 16 MHz) y cable USB.
- Cables de prueba/pinzas. **Conecta siempre GND del circuito bajo prueba al GND del Arduino.**

### Software
- Arduino IDE 1.8.x / 2.x (o `arduino-cli`).
- Python 3.8 o superior con Tkinter (en Linux Debian/Ubuntu: `sudo apt install python3-tk`).
- Librerías de Python: `pyserial`, `numpy`, `matplotlib`.

---

## 3. Instalación y uso

### 3.1 Firmware
1. Abre `arduino_logic_analyzer/arduino_logic_analyzer.ino` en el Arduino IDE (la carpeta debe llamarse igual que el `.ino`).
2. Selecciona **Arduino Uno** y el puerto, y pulsa *Subir*.
3. Cierra el Monitor Serie si lo abriste (el puerto debe quedar libre). El firmware trabaja a **500000 baudios**.

### 3.2 Aplicación de PC
```bash
cd pc_gui
python -m pip install -r requirements.txt
python logic_analyzer_gui.py
```
En Linux puede que necesites permisos sobre el puerto: `sudo usermod -aG dialout $USER` y volver a iniciar sesión.

### 3.3 Primera captura
1. Elige el puerto y pulsa **Connect** (el Arduino se reinicia al abrir el puerto; la conexión tarda ~2 s). Para probar sin hardware elige `DEMO (simulated device)`.
2. Ajusta **Sample rate** (regla práctica: al menos 5-10 veces la frecuencia más alta de la señal).
3. Pulsa **Run** o **Single**.

### 3.4 Conexionado

| Canal | Modo digital (rápido) | Modo analógico (umbral ajustable) |
|---|---|---|
| CH1 | D2 | A0 |
| CH2 | D3 | A1 |
| CH3 | D4 | A2 |
| CH4 | D5 | A3 |
| CH5 | D6 | A4 |
| CH6 | D7 | A5 |
| CH7 | D8 | D8 (digital) |
| CH8 | D9 | D9 (digital) |
| GND | GND | GND |

D0/D1 están ocupados por el puerto serie USB.

> **Tensión máxima de entrada: 5 V.** Las entradas del Arduino no tienen protección. Para señales de más tensión usa divisores resistivos o adaptadores de nivel; es recomendable una resistencia en serie de 1-10 kΩ.
> Las entradas no tienen pull-up: una entrada sin conectar flota y lee ruido.

---

## 4. Guía de la interfaz

**Barra superior:** puerto, baudios (deben coincidir con el firmware, 500000), Connect/Disconnect, Run, Single, Stop, Pause display, Save PNG, Export PDF, Export CSV.

**Channels:** casilla para activar/desactivar, color, nombre editable y pines asociados. Los nombres se usan en la gráfica, en la lectura de cursores y en las cabeceras del CSV.

**Acquisition**
- *Sample rate*: admite valores como `250k`, `100 kHz`, `500`. El firmware devuelve la tasa real obtenida (se muestra en el título de la gráfica).
- *Samples*: 128, 256, 512 o 1024 muestras.
- *Input mode*: digital (rápido, umbral fijo) o analógico (umbral ajustable).
- *Threshold (V)*: solo activo en modo analógico.

**Trigger**
- *Type*: Off, Rising edge, Falling edge, Any edge, High level, Low level.
- *Channel*: canal que se vigila. *Pre-trigger (%)*: porcentaje del buffer que se guarda antes del disparo.
- *Mode*: **Auto** (si no hay disparo en un buffer completo, muestra los datos igualmente) o **Normal** (espera indefinidamente; se cancela con Stop).
- Con trigger, el instante del disparo es `t = 0` y se marca con una línea amarilla "T". Sin trigger, `t = 0` es la primera muestra.

**Display**
- *Time/div*: escala horizontal (10 divisiones). Se muestra también en la etiqueta del eje X.
- *Bus format*: base numérica del carril BUS y de las lecturas. Convención: **CH1 = bit 0 (LSB) … CH8 = bit 7 (MSB)**; los canales desactivados cuentan como 0.
- *Light plot theme*: tema claro (el PDF siempre se exporta en claro).

**Cursores y ratón**
- Clic izquierdo: cursor A (arrastrable). Clic derecho o Shift+clic: cursor B.
- Rueda: zoom; Shift+rueda: desplazamiento; botón central arrastrando: pan.
- El panel inferior muestra A, B, ΔT, 1/ΔT, número de muestras y el valor del bus (BIN/DEC/HEX/OCT) y de cada canal en cada cursor.

**Pause display:** congela la pantalla (formas de onda y valores) para analizarla; la adquisición sigue en segundo plano y al reanudar se muestra la última captura. Las exportaciones usan lo que hay en pantalla.

**Exportación**
- *PNG*: guarda la gráfica (no la ventana completa) a 150 dpi.
- *PDF*: gráfica vectorial en tema claro.
- *CSV*: columnas `Sample, Time_s, <canales activos>, Value_BIN, Value_DEC, Value_HEX, Value_OCT`. El tiempo es relativo al trigger (o a la primera muestra).

---

## 5. Cómo funciona

```
 Señales ──► Arduino Uno ──(USB serie, 500000 baud)──► Python GUI
             · Timer1 marca el ritmo de muestreo         · hilo lector (tramas)
             · buffer de 1024 bytes en SRAM              · cola de eventos → Tk
             · trigger + buffer circular                 · Matplotlib (dibujo)
```

### 5.1 Firmware
- **Muestreo digital:** se lee `PIND` (D2-D7) y `PINB` (D8-D9) y se empaquetan en un byte: `(PIND >> 2) | (PINB << 6)`. Cada canal es un bit, lo que permite leer los 8 canales a la vez con muy pocas instrucciones.
- **Temporización:** Timer1 en modo CTC genera el reloj de muestreo; el bucle espera el flag `OCF1A` por *polling* y toma la muestra. Se elige automáticamente el prescaler para cubrir de 1 Hz a 250 kHz. Durante la captura las interrupciones están desactivadas (sin jitter por la UART ni `millis()`).
- **Trigger y pre-trigger:** con trigger activo las muestras se escriben en un **buffer circular**. Cuando ha pasado el pre-trigger y se cumple la condición, se capturan las muestras restantes y se envía el buffer en orden cronológico.
- **Cancelación:** mientras se espera el trigger o a tasas lentas (< 2 kHz), el firmware vigila el puerto serie; cualquier byte recibido (el PC envía `A`) aborta la captura.
- **Modo analógico:** para A0-A5 se hace una conversión ADC por canal (reloj de ADC de 1 MHz) y se compara con el umbral, que el PC envía en mV.

### 5.2 Protocolo serie
Comandos ASCII terminados en `\n`:

| Comando | Respuesta |
|---|---|
| `ID` | `LA8 1.0 1024` |
| `A` | `ABORT` |
| `S <rate> <analog> <thr_mV> <trigType> <trigCh> <prePct> <auto> <count>` | una trama binaria, o `ERR ...` / `ABORT` |

Trama (little endian): `A5 5A | flags(1) | tasa_real(4) | count(2) | trigPos(2) | datos[count] | checksum(1)`. `flags`: bit0 = disparado, bit1 = modo analógico. El checksum es la suma de los datos módulo 256. El PC resincroniza y descarta tramas con checksum erróneo.

### 5.3 Aplicación de PC
- Un **hilo lector** separa líneas de texto y tramas binarias y las deja en una cola; Tk la consulta cada 20 ms.
- Una pequeña máquina de estados (`IDLE / ARMED / ABORTING`) arma capturas, reintenta en modo Run y reconfigura al cambiar ajustes mientras se captura.
- El dibujo usa Matplotlib (`step` para las ondas, `PolyCollection` para el bus). Los valores del bus se rotulan cuando el segmento es lo bastante ancho (si no cabe con prefijo `0x`/`0b`/`0o`, se muestra sin prefijo).

---

## 6. Limitaciones

Es importante conocerlas antes de fiarse de una medida:

1. **Captura por bloques, no en continuo.** Solo caben 1024 muestras (SRAM de 2 KB). Entre capturas hay un tiempo muerto (transferencia + dibujo, decenas de ms), por lo que no se ven eventos que ocurran entre bloques.
2. **Velocidad máxima:** 250 kS/s sin trigger, 125 kS/s con trigger y 5 kS/s en modo analógico (el firmware limita el valor pedido y la GUI muestra el real). Con 8 canales y una captura de 1024 muestras la ventana es corta a tasas altas (4 ms a 250 kS/s). Para ver bien una señal conviene muestrear 5-10 veces más rápido que su frecuencia: **no es adecuado para buses rápidos** (SPI/I²C a alta velocidad, etc.). Sirve para UART, I²C/1-Wire lentos, PWM, señales de sensores, lógica de baja frecuencia.
3. **Umbral (threshold):** en modo digital el umbral es el del ATmega328P a 5 V (nivel bajo < ≈1,5 V, nivel alto > ≈3 V) y **no es ajustable**. Un "threshold" real solo es posible en el modo analógico, que:
   - solo cubre CH1-CH6 (A0-A5); CH7 y CH8 siguen siendo digitales con umbral fijo;
   - muestrea los canales de forma secuencial, con un desfase de unos 13-15 µs entre canales, a un máximo de 5 kS/s;
   - tiene precisión aproximada de 8 bits efectivos y usa AVcc (≈5 V por USB) como referencia, así que el umbral absoluto tiene un error de décimas de voltio;
   - necesita fuentes de baja impedancia (< 10 kΩ) y no incluye histéresis (una señal ruidosa cerca del umbral puede oscilar).
   Para lógica de 3,3 V en modo digital el nivel alto (≈3,3 V) queda justo por encima del mínimo de 3 V: puede funcionar, pero con poco margen.
4. **Precisión temporal:** depende del oscilador de la placa (cristal de la Uno original, pero resonador cerámico en muchos clones, menos preciso). La resolución es el periodo de muestreo (p. ej. 4 µs a 250 kS/s) y, mientras se espera el trigger, hay un jitter de muestreo de hasta ≈0,5 µs.
5. **Sin protecciones de entrada** ni adaptación de nivel: máximo 5 V.
6. **El PC solo puede cancelar** una captura en trigger, modo analógico o tasas < 2 kHz. A tasas altas sin trigger la captura (< 0,5 s) no es cancelable.
7. **Bus numérico simple:** se interpreta el byte completo (CH1 = LSB); no hay decodificadores de protocolo (UART, I²C, SPI…).
8. **"Pause" congela la pantalla**, no detiene la adquisición en el Arduino (usa Stop para eso).
9. Los dispositivos con convertidor USB-serie económico (CH340, etc.) normalmente aceptan 500000 baudios; si no, reduce `SERIAL_BAUD` en el firmware y el valor de baudios en la GUI a 250000 o 115200 (el sistema funciona, solo tarda más en transferir).

### Estado de las pruebas
- La lógica del firmware (empaquetado de canales, buffer circular, trigger/pre-trigger, checksum, límites de tasa, cálculo del divisor) se verificó compilándola en un PC con registros simulados.
- La aplicación de PC se ejecutó con el dispositivo simulado (modo DEMO): protocolo, capturas, trigger, zoom, cursores y exportaciones PNG/PDF/CSV.
- **No se ha probado con una placa Arduino real** ni se han medido con osciloscopio los tiempos del bucle de muestreo. Se recomienda una primera comprobación con una señal conocida (p. ej. un generador de funciones a 1 kHz) y, si se desea ir cerca del límite de 250 kS/s, verificar la tasa real.

---

## 7. Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| "No answer from the Arduino" | Firmware no subido, puerto ocupado (Monitor Serie abierto) o baudios distintos de 500000 |
| No aparece el puerto | Falta el driver (CH340/CP210x en clones), cable solo de carga, o permisos (`dialout` en Linux) |
| La captura no se dispara en modo Normal | El canal no cumple la condición; pulsa Stop o usa modo Auto |
| Señales con ruido o valores erráticos | Entrada sin conectar (flotante), falta GND común o cables largos |
| Flancos "perdidos" | Tasa de muestreo insuficiente para la señal; sube el sample rate |
| `ModuleNotFoundError: tkinter` | Instala el paquete de Tkinter de tu sistema (`python3-tk`) |

---

## 8. Ideas de ampliación

- Decodificadores de protocolo (UART, I²C, SPI) sobre los datos capturados.
- Más profundidad de captura con RAM externa o usando una placa con más memoria (p. ej. un Arduino Mega o una Raspberry Pi Pico para velocidades mayores).
- Comparador externo (p. ej. LM393 + PWM filtrado) para tener un umbral ajustable también en modo rápido.
