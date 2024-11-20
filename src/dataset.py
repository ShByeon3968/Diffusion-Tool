import torch
from torch.utils.data import Dataset
from PIL import Image
import os

from utils import UtillFuctions

class CustomCocoDataset(Dataset):
    def __init__(self, json_path, img_dir, transform=None):
        self.coco_data = UtillFuctions.json_loader(json_path)
        self.img_dir = img_dir
        self.transform = transform
        self.images = self.coco_data['images']
        self.annotations = self.coco_data['annotations']
        self.categories = {cat['id']: cat['name'] for cat in self.coco_data['categories']}

    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # 이미지 로드
        img_info = self.images[idx]
        img_path = os.path.join(self.img_dir, img_info['file_name'])
        image = Image.open(img_path).convert('RGB')
        # 어노테이션 정보
        img_id = img_info['id']
        targets = [ann for ann in self.annotations if ann['image_id'] == img_id]
        # 바운딩 박스 , labels
        bboxes = [ann['bbox'] for ann in targets]
        labels = [ann['category_id'] for ann in targets]
        # bbox -> [x_min, y_min, x_max, y_max]
        bboxes = torch.tensor([[x, y, x + w, y + h] for x, y, w, h in bboxes], dtype=torch.float32)
        labels = torch.tensor(labels, dtype=torch.int64)

        sample = {
            'image': self.transform(image) if self.transform else image,
            'bboxes': bboxes,
            'labels': labels
        }
        return sample