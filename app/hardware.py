from app.config import settings


def send_serial(word: int) -> str:
    if not settings.serial_enabled:
        return "Serial deshabilitado: palabra generada en modo simulación."
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Instala las dependencias del proyecto para habilitar serial") from exc
    # Serial UART transmite bytes; se requiere un adaptador ARINC 429 certificado/aislado.
    # El orden de bytes debe ajustarse al adaptador específico de laboratorio.
    with serial.Serial(settings.serial_port, settings.serial_baudrate, timeout=1) as port:
        port.write(word.to_bytes(4, byteorder="little", signed=False))
        port.flush()
    return f"Palabra enviada al adaptador serial {settings.serial_port}; verificar el formato del adaptador."


def play_value_audio(value: float) -> str:
    if not settings.audio_enabled:
        return "Audio deshabilitado; sin salida acústica."
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Instala el extra opcional audio para habilitarlo") from exc
    # Tono indicador únicamente; una salida de auriculares no es una salida DC calibrada.
    frequency = 440.0 + min(abs(value), 2000.0) % 440.0
    duration = 0.15
    t = np.arange(int(settings.audio_sample_rate * duration)) / settings.audio_sample_rate
    signal = (0.03 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    sd.play(signal, settings.audio_sample_rate, blocking=True)
    return f"Tono indicativo reproducido ({frequency:.0f} Hz, amplitud digital baja); no es tensión calibrada."
