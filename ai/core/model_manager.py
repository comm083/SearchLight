import torch
import os

class ModelManager:
    """AI 모델의 디바이스 관리 및 로딩을 담당하는 공통 매니저"""
    
    @staticmethod
    def get_device():
        """사용 가능한 최적의 디바이스(CUDA/CPU)를 반환합니다."""
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @staticmethod
    def get_model_path(relative_path: str):
        """프로젝트 루트 기준의 절대 경로를 반환합니다."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(project_root, relative_path)

model_manager = ModelManager()
