import streamlit as st
import torch
import segmentation_models_pytorch as smp
from utils.constants import DEVICE


@st.cache_resource(show_spinner="Загрузка нейросети...")
def load_model(weights_path: str = "models/best_model.pth"):
    """Загружает модель один раз и кэширует"""
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=1,
        classes=1,
    )
    model.load_state_dict(torch.load(weights_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model
