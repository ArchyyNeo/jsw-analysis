import os
import time
import shutil
import streamlit as st

from utils.constants import DEVICE, MAX_FILE_SIZE_BYTES
import streamlit as st

from utils.constants import DEVICE
from services.session_service import cleanup_old_sessions
from services.job_service import process_single_image

from PIL import Image
import traceback

from utils.logger import logger

# ====================================================
# PAGE CONFIG
# ====================================================
try:
    st.set_page_config(
        page_title="JSW Analysis",
        page_icon="🦴",
        layout="wide"
    )
except Exception as e:
    logger.error(f"Ошибка конфигурации страницы Streamlit: {e}\n{traceback.format_exc()}")


# ====================================================
# CSS
# ====================================================
def load_css():
    css_path = "static/style.css"
    try:
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                st.markdown(
                    f"<style>{f.read()}</style>",
                    unsafe_allow_html=True
                )
        else:
            logger.warning(f"Файл стилей не найден по пути: {css_path}")
    except Exception as e:
        logger.error(f"Не удалось загрузить CSS-стили: {e}\n{traceback.format_exc()}")

load_css()


# ====================================================
# SESSION INIT
# ====================================================
try:
    if "cleaned" not in st.session_state:
        cleanup_old_sessions()
        st.session_state.cleaned = True
except Exception as e:
    logger.error(f"Ошибка при очистке старых сессий: {e}\n{traceback.format_exc()}")

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None


# ====================================================
# HEADER / FILE UPLOADER
# ====================================================
run_analysis = False

try:
    _, center, _ = st.columns([1.5, 2, 1.5])

    with center:
        with st.container(border=True):
            st.markdown("""
            <div class="hero-title">JSW Analysis</div>
            <div class="hero-sub">
                Автоматический анализ ширины суставной щели
            </div>
            """, unsafe_allow_html=True)

            uploaded_file = st.file_uploader(
                "Загрузить снимок",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )

            # Флаг для контроля доступности кнопки анализа после проверок
            is_file_valid = False

            if uploaded_file is None:
                st.session_state.analysis = None
                st.session_state.file_name = None
            else:
                # 1. Проверка формата файла
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                # 2. Проверка на R или L на конце имени (поддерживает варианты: image_R, imageR)
                base_name = os.path.splitext(uploaded_file.name)[0]
                has_side_suffix = (
                    base_name.endswith('R') or 
                    base_name.endswith('L') or 
                    base_name.endswith('_R') or 
                    base_name.endswith('_L')
                )
                # 3. Проверка размера
                file_size = uploaded_file.size

                if file_ext not in [".png", ".jpg", ".jpeg"]:
                    st.error("❌ Неверный формат файла. Допускаются только изображения .PNG, .JPG, .JPEG")
                    st.session_state.analysis = None
                    st.session_state.file_name = None
                elif not has_side_suffix:
                    st.error("❌ Некорректное имя файла. Имя снимка должно обязательно заканчиваться на букву 'R' (правое колено) или 'L' (левое колено) перед расширением (например: image_R.png).")
                    st.session_state.analysis = None
                    st.session_state.file_name = None
                elif file_size > MAX_FILE_SIZE_BYTES:
                    st.error(f"❌ Превышен максимальный размер файла. Лимит: {MAX_FILE_SIZE_BYTES / (1024 * 1024):.1f} МБ.")
                    st.session_state.analysis = None
                    st.session_state.file_name = None
                else:
                    # Если всё хорошо — разрешаем кликать на кнопку
                    is_file_valid = True
                    if st.session_state.file_name != uploaded_file.name:
                        st.session_state.analysis = None
                        st.session_state.file_name = uploaded_file.name

            run_analysis = st.button(
                "Анализ",
                use_container_width=True,
                type="primary",
                disabled=not is_file_valid
            )
except Exception as e:
    logger.error(f"Ошибка интерфейса в блоке заголовка/загрузки: {e}\n{traceback.format_exc()}")
    st.error("Произошла критическая ошибка интерфейса при загрузке элементов управления.")
    uploaded_file = None


# ====================================================
# RUN ANALYSIS
# ====================================================
# Проверяем locals(), чтобы Pylance не ругался, если try-блок выше выбросит исключение
if 'uploaded_file' in locals() and uploaded_file and run_analysis:
    try:
        with st.spinner("Выполняется анализ..."):
            result = process_single_image(uploaded_file)
            st.session_state.analysis = result
            
        if result and result.get("success"):
            st.toast("Анализ успешно завершён", icon="✅")
    except Exception as e:
        error_msg = f"Критическая ошибка во время выполнения анализа изображения: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        st.session_state.analysis = {"success": False, "error": "Внутренняя ошибка сервера при обработке снимка."}


# ====================================================
# CONTENT / VISUALIZATION
# ====================================================
try:
    result = st.session_state.analysis
    left, center, right = st.columns([1, 4, 1])

    # Безопасное получение ссылки на файл для Pylance без перетирания логики Streamlit
    current_file = uploaded_file if 'uploaded_file' in locals() else None

    with center:
        col1, col2, col3 = st.columns(3, gap="large")

        # Флаг корректности отображения исходного снимка
        original_image_ok = True

        # --- ORIGINAL IMAGE ---
        with col1:
            with st.container(border=True):
                st.markdown('<div class="result-title">Исходный снимок</div>', unsafe_allow_html=True)
                if current_file is not None:
                    try:
                        st.image(current_file, use_container_width=True)
                    except Exception as img_err:
                        original_image_ok = False  # Ломаем флаг, чтобы не рендерить битые метрики
                        logger.error(f"Ошибка отображения исходного изображения: {img_err}\n{traceback.format_exc()}")
                        st.error("Не удалось отобразить исходный снимок.")

        # --- RESULT IMAGE ---
        with col2:
            with st.container(border=True):
                st.markdown('<div class="result-title">Результат анализа</div>', unsafe_allow_html=True)
                if original_image_ok and result and result.get("success"):
                    img_path = result.get("result_image_path")
                    if img_path:
                        if os.path.exists(img_path):
                            try:
                                st.image(img_path, use_container_width=True)
                                metrics = result.get("metrics", {}) if result else {}

                                try:
                                    from PIL import Image, ImageDraw, ImageFont
                                    import io

                                    pil_img = Image.open(img_path).convert("RGB")
                                    draw = ImageDraw.Draw(pil_img)

                                    font_size = max(18, int(pil_img.width * 0.025))
                                    
                                    font = None
                                    for font_name in ["Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]:
                                        try:
                                            font = ImageFont.truetype(font_name, font_size)
                                            break
                                        except:
                                            continue
                                    if font is None:
                                        font = ImageFont.load_default()

                                    x, y = 30, 30

                                    draw.text((x, y), "JSW Metrics:", fill="blue", font=font)
                                    y += int(font_size * 1.4)

                                    line_spacing = int(font_size * 1.4)
                                    stroke_w = max(1, int(font_size * 0.08))

                                    for name, value in metrics.items():
                                        display_val = f"{value}" if isinstance(value, (int, float)) else str(value)
                                        text_line = f"- {name}: {display_val}"
                                        
                                        if name != "Asymmetry Ratio":
                                            draw.text((x, y), text_line, fill="white", font=font, stroke_width=stroke_w, stroke_fill="black")
                                            y += line_spacing
                                        else:
                                            color = "green"
                                            float_value = float(value)
                                            if float_value < 0.7:
                                                color = "red"
                                            draw.text((x, y), text_line, fill=color, font=font, stroke_width=stroke_w, stroke_fill="black")
                                            y += line_spacing

                                    buffer = io.BytesIO()
                                    pil_img.save(buffer, format="PNG")
                                    file_bytes = buffer.getvalue()

                                except Exception as e:
                                    logger.error(f"Ошибка отрисовки метрик на изображении: {e}")
                                    with open(img_path, "rb") as f:
                                        file_bytes = f.read()

                                orig_name = st.session_state.file_name or "result.png"
                                download_name = f"proc_{orig_name}"
                                st.download_button(
                                    label="Скачать результат",
                                    data=file_bytes,
                                    file_name=download_name,
                                    mime="image/png",
                                    use_container_width=True
                                )
                            except Exception as img_err:
                                logger.error(f"Ошибка вывода или подготовки скачивания изображения ({img_path}): {img_err}\n{traceback.format_exc()}")
                                st.error("Ошибка визуализации или скачивания результата.")

                            except Exception as img_err:
                                logger.error(f"Ошибка вывода результирующего изображения ({img_path}): {img_err}\n{traceback.format_exc()}")
                                st.error("Ошибка визуализации результата.")

                        else:
                            logger.error(f"Файл результата анализа отсутствует по пути: {img_path}")
                            st.error("Файл изображения результата не найден на сервере.")

        # --- METRICS ---
        with col3:
            with st.container(border=True):
                st.markdown('<div class="result-title">Метрики</div>', unsafe_allow_html=True)
                if original_image_ok and result and result.get("success"):
                    metrics = result.get("metrics", {})
                    
                    if isinstance(metrics, dict):
                        for name, value in metrics.items():
                            display_value = value
                            if isinstance(value, (int, float)):
                                display_value = f"{value:.3f}"

                            value_class = ""
                            if str(name).lower() == "asymmetry ratio":
                                try:
                                    if float(value) < 0.7:
                                        value_class = "metric-bad"
                                    else:
                                        value_class = "metric-good"
                                except (ValueError, TypeError) as val_err:
                                    logger.warning(f"Не удалось распарсить значение метрики '{name}': {value}. Ошибка: {val_err}")

                            st.markdown(
                                f"""
                                <div class="metric-card">
                                    <div class="metric-label">{name}</div>
                                    <div class="metric-value {value_class}">
                                        {display_value}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        logger.error(f"Поле 'metrics' в ответе не является словарем. Получено: {type(metrics)}")
                        st.error("Некорректный формат метрик.")

except Exception as e:
    logger.error(f"Ошибка рендеринга блоков контента: {e}\n{traceback.format_exc()}")
    st.error("Произошла ошибка при попытке отобразить результаты анализа.")


# ====================================================
# ERROR HANDLING DISPLAY
# ====================================================
try:
    if result and not result.get("success"):
        st.error(result.get("error", "Ошибка анализа"))
except Exception as e:
    logger.error(f"Ошибка при выводе сообщения об ошибке: {e}\n{traceback.format_exc()}")


# ====================================================
# FOOTER
# ====================================================
try:
    st.markdown("<br>", unsafe_allow_html=True)
    device_str = str(DEVICE).upper() if DEVICE else "UNKNOWN"
    st.markdown(
        f"""
        <div class="footer">
            JSW Analysis • U-Net ResNet34 • {device_str}
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    logger.error(f"Ошибка рендеринга футера: {e}\n{traceback.format_exc()}")
