import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

# --- ПАРАМЕТРЫ ИЗ УСЛОВИЯ ---
WHEEL_DIAMETER_MM = 584  # Значение из скобок в условии
GEAR_RATIO = 42 / 11
TARGET_TIME_STR = "2025-04-12 08:12:30"
UTC_OFFSET = 3  # Москва GMT+3

def calculate_speed_from_csv(file_path):
    # 1. Загрузка данных
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return "Файл не найден. Пожалуйста, проверьте путь."

    # 2. Перевод искомого времени в Unix Timestamp
    tz = timezone(timedelta(hours=UTC_OFFSET))
    target_dt = datetime.strptime(TARGET_TIME_STR, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    target_ts = target_dt.timestamp()

    # 3. Выделяем фрагмент данных (окно 2 секунды для точного определения частоты)
    window = df[(df['Time (Unix Timestamp)'] >= target_ts - 1) & 
                (df['Time (Unix Timestamp)'] <= target_ts + 1)]
    
    if window.empty:
        return "Нет данных для указанного времени"

    # 4. Вычисляем каденс (частоту педалирования)
    # Используем ось X акселерометра (на шатуне она дает самый четкий синус)
    signal = window['X (mG)'].values
    time_ms = window['Time (ms MCU)'].values
    
    # Частота дискретизации (Hz)
    fs = 1000 / np.mean(np.diff(time_ms))
    
    # FFT (быстрое преобразование Фурье) для поиска основной частоты вращения
    n = len(signal)
    # Убираем постоянную составляющую (mean), чтобы пик на 0 Гц не мешал
    yf = np.abs(np.fft.rfft(signal - np.mean(signal)))
    xf = np.fft.rfftfreq(n, d=1/fs)
    
    # Находим частоту с максимальной амплитудой
    cadence_hz = xf[np.argmax(yf)]
    
    # 5. Итоговый расчет скорости
    # Длина окружности в метрах
    circumference = (WHEEL_DIAMETER_MM / 1000) * np.pi
    
    # Скорость = Частота_педалей * Передача * Длина_колеса * 3.6 (в км/ч)
    speed_kmh = cadence_hz * GEAR_RATIO * circumference * 3.6
    
    return round(speed_kmh, 2)

# Пример использования:
# result = calculate_speed_from_csv('your_data_file.csv')
# print(f"Скорость велосипедиста: {result} км/ч")
