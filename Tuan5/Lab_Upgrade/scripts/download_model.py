import torch
from torchvision.models import resnet18

model = resnet18(weights="DEFAULT")
model.eval()

torch.save(
    model.state_dict(),
    "/home/vinh_shindo/AIoT/Tuan5/Lab_Upgrade/models/exported_ca_nhan/resnet18.pth"
)

print("Saved")