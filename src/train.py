from utils import UtillFuctions
import argparse
from dataset import CustomCocoDataset
import torchvision.transforms as transforms
import torch
from torch.utils.data import DataLoader
from ultralytics import YOLO

parser = argparse.ArgumentParser()
parser.add_argument('--config_path',type=str,default='config.yaml')
args = parser.parse_args()


if __name__ == '__main__':
    config = UtillFuctions.load_config(args.config_path)
    train_json = config
    # Dataset paths and hyperparameters
    train_json = config['dataset']['train_json']
    train_images = config['dataset']['train_images']
    val_json = config['dataset']['val_json']
    val_images = config['dataset']['val_images']

    batch_size = config['training']['batch_size']
    learning_rate = config['training']['learning_rate']
    num_epochs = config['training']['num_epochs']
    image_size = tuple(config['training']['image_size'])

    pretrained_weights = config['model']['pretrained_weights']

    # Transformations for the image
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
    ])

    # Load the dataset
    train_dataset = CustomCocoDataset(
        json_path=train_json,
        img_dir=train_images,
        transform=transform
    )
    val_dataset = CustomCocoDataset(
    json_path=val_json,
    img_dir=val_images,
    transform=transform
    )   
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=lambda x: x)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=lambda x: x)

    # Load the YOLOv8 model with pretrained weights
    model = YOLO(pretrained_weights)  # Load the pretrained YOLOv8 model

    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # Define optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    for epoch in range(num_epochs):
        model.train(data='coco.yaml')
        total_loss = 0

        for batch_idx, batch in enumerate(train_loader):
            images = [item['image'].to(device) for item in batch]
            targets = [{
                'boxes': item['bboxes'].to(device),
                'labels': item['labels'].to(device)
            } for item in batch]

            optimizer.zero_grad()

            # Forward pass
            outputs = model(images)

            # Compute loss
            loss = model.compute_loss(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {avg_loss:.4f}")

        # Validation step (optional)
        model.eval()
        with torch.no_grad():
            val_loss = 0
            for batch in val_loader:
                images = [item['image'].to(device) for item in batch]
                targets = [{
                    'boxes': item['bboxes'].to(device),
                    'labels': item['labels'].to(device)
                } for item in batch]

                outputs = model(images)
                loss = model.compute_loss(outputs, targets)
                val_loss += loss.item()
            
            avg_val_loss = val_loss / len(val_loader)
            print(f"Validation Loss: {avg_val_loss:.4f}")

    print("Training complete!")