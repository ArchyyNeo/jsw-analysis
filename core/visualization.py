import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from utils.helpers import extract_metadata
from utils.constants import MAX_DEVIATION_PCT, CENTRAL_BLIND_ZONE_PCT

def visualize_professional_jsw(mask_path: str, image_path: str, output_path=None, max_deviation_pct=MAX_DEVIATION_PCT):
    patient_id, side_1 = extract_metadata(image_path)
    
    if not os.path.exists(mask_path) or not os.path.exists(image_path):
        return False, {}

    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    orig_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if mask is None or orig_img is None:
        return False, {}

    if orig_img.shape != mask.shape:
        mask = cv2.resize(mask, (orig_img.shape[1], orig_img.shape[0]), cv2.INTER_NEAREST)

    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    if num_labels <= 1:
        return False, {}

    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    clean_mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)

    ys, xs = np.where(clean_mask > 0)
    if len(xs) == 0:
        return False, {}

    min_x, max_x = xs.min(), xs.max()
    total_width = max_x - min_x
    img_width = mask.shape[1]
    center_x = (min_x + max_x) // 2

    deviation_pct = abs(center_x - img_width / 2) / img_width
    if deviation_pct > max_deviation_pct:
        return False, {}

    start_x = int(min_x + 0.15 * total_width)
    end_x = int(max_x - 0.15 * total_width)

    x_positions, tops, bottoms = [], [], []
    for x in range(start_x, end_x):
        y_coords = np.where(clean_mask[:, x] > 0)[0]
        if len(y_coords) >= 2:
            tops.append(y_coords.min())
            bottoms.append(y_coords.max())
            x_positions.append(x)

    if not x_positions:
        return False, {}

    x_positions = np.array(x_positions)
    tops = np.array(tops)
    bottoms = np.array(bottoms)
    widths = bottoms - tops + 1

    vis_img = cv2.cvtColor(orig_img, cv2.COLOR_GRAY2BGR)
    overlay = vis_img.copy()

    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(clean_mask, kernel, iterations=1)
    overlay[dilated == 255] = (220, 220, 220)

    COLOR_MEDIAL = (60, 60, 200)
    COLOR_LATERAL = (220, 160, 60)

    medial_widths, lateral_widths = [], []
    medial_idx, lateral_idx = [], []
    central_blind = int(CENTRAL_BLIND_ZONE_PCT * total_width)

    for i, x in enumerate(x_positions):
        is_left = x < center_x
        is_medial = (side_1 == "L") == is_left
        dist_to_center = abs(x - center_x)

        if is_medial:
            color = COLOR_MEDIAL
            if dist_to_center > central_blind:
                medial_widths.append(widths[i])
                medial_idx.append(i)
        else:
            color = COLOR_LATERAL
            if dist_to_center > central_blind:
                lateral_widths.append(widths[i])
                lateral_idx.append(i)

        cv2.line(overlay, (x, tops[i]), (x, bottoms[i]), color, 1)

    alpha = 0.45
    cv2.addWeighted(overlay, alpha, vis_img, 1 - alpha, 0, vis_img)

    # Центральная ось
    cv2.line(
        vis_img,
        (center_x, 0),
        (center_x, vis_img.shape[0]),
        (0, 200, 0),
        1
    )

    # Границы слепой зоны
    left_blind_border = center_x - central_blind
    right_blind_border = center_x + central_blind

    cv2.line(
        vis_img,
        (left_blind_border, 0),
        (left_blind_border, vis_img.shape[0]),
        (100, 100, 100),
        1
    )

    cv2.line(
        vis_img,
        (right_blind_border, 0),
        (right_blind_border, vis_img.shape[0]),
        (100, 100, 100),
        1
    )

    # Подсветка истинных минимумов
    def highlight_min(indices, widths_array):
        if len(indices) == 0:
            return

        local_min_idx = np.argmin(widths_array)
        global_idx = indices[local_min_idx]

        x_min = x_positions[global_idx]

        cv2.line(
            vis_img,
            (x_min, tops[global_idx]),
            (x_min, bottoms[global_idx]),
            (0, 255, 255),
            1
        )

    highlight_min(medial_idx, np.array(medial_widths))
    highlight_min(lateral_idx, np.array(lateral_widths))

    # --- Метрики ---
    medial_min = float(np.min(medial_widths)) if medial_widths else 0.0
    medial_mean = float(np.mean(medial_widths)) if medial_widths else 0.0
    lateral_min = float(np.min(lateral_widths)) if lateral_widths else 0.0
    lateral_mean = float(np.mean(lateral_widths)) if lateral_widths else 0.0
    global_std = float(np.std(widths)) if len(widths) else 0.0

    ratio = medial_mean / lateral_mean if lateral_mean > 0 else 0.0

    side_text = "Левая" if side_1 == "L" else "Правая"

    metrics = {
        "Сторона": side_text,
        "Medial Min (Узкое место)": round(medial_min, 2),
        "Medial Mean (Средняя)": round(medial_mean, 2),
        "Lateral Min (Узкое место)": round(lateral_min, 2),
        "Lateral Mean (Средняя)": round(lateral_mean, 2),
        "Global Std (Изрезанность)": round(global_std, 2),
        "Asymmetry Ratio": round(ratio, 3)
    }

    # Визуализация (matplotlib)
    if output_path:
        fig, ax = plt.subplots(figsize=(8, 8))

        ax.imshow(
            cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB)
        )

        ax.axis("off")

        from matplotlib.patches import Patch

        legend_elements = [
            Patch(facecolor='#C83C3C', label='Медиальный отдел'),
            Patch(facecolor='#3CA0DC', label='Латеральный отдел'),
            Patch(facecolor='#FFFF00', label='Точка истинного минимума'),
            Patch(facecolor='#00C800', label='Центральная ось'),
            Patch(facecolor='#646464', label='Слепая зона (10%)'),
            Patch(facecolor='#DCDCDC', label='Сегментация')
        ]

        ax.legend(
            handles=legend_elements,
            loc='upper right',
            fontsize=10,
            framealpha=0.9
        )

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches='tight',
            pad_inches=0
        )

        plt.close(fig)

    return True, metrics
