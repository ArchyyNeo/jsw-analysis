import os
import torch
import numpy as np
import cv2
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
from core.model_loader import load_model
from utils.constants import DEVICE


class InferenceDataset(Dataset):
    def __init__(self, file_paths):
        self.file_paths = file_paths

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        img_path = self.file_paths[idx]
        img_bytes = np.fromfile(img_path, dtype=np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Не удалось прочитать: {img_path}")
        img = img.astype(np.float32) / 255.0
        return torch.tensor(img).unsqueeze(0), img_path


def run_inference_on_single_file(model, input_file: str, output_dir: str):
    """Инференс для одного файла"""
    os.makedirs(output_dir, exist_ok=True)
    
    dataset = InferenceDataset([input_file])
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    model.eval()
    with torch.no_grad():
        for images, img_paths in loader:
            images = images.to(DEVICE)
            outputs = model(images)
            preds = (torch.sigmoid(outputs) > 0.5).float()
            preds_np = preds.cpu().numpy()

            for i in range(preds_np.shape[0]):
                filename = os.path.basename(img_paths[i])
                save_path = os.path.join(output_dir, filename)
                
                mask_to_save = (preds_np[i].squeeze() * 255).astype(np.uint8)
                cv2.imwrite(save_path, mask_to_save)


def run_inference_on_folder(model, input_dir: str, output_dir: str, batch_size=8):
    """Инференс для папки (batch)"""
    all_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_files.append(os.path.join(root, file))

    if not all_files:
        return 0

    dataset = InferenceDataset(all_files)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    model.eval()
    processed = 0

    with torch.no_grad():
        for images, img_paths in tqdm(loader, desc="Инференс"):
            images = images.to(DEVICE)
            outputs = model(images)
            preds = (torch.sigmoid(outputs) > 0.5).float().cpu().numpy()

            for i in range(preds.shape[0]):
                rel_path = os.path.relpath(img_paths[i], input_dir)
                save_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                mask = (preds[i].squeeze() * 255).astype(np.uint8)
                cv2.imwrite(save_path, mask)
                processed += 1

    return processed
