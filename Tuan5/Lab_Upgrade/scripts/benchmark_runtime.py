import time
import torch
import onnxruntime as ort
import numpy as np
import pandas as pd

from torchvision.models import resnet18

NUM_RUNS = 20

# ---------------------
# PyTorch
# ---------------------

model = resnet18(weights="DEFAULT")
model.eval()

dummy = torch.randn(1,3,224,224)

torch_times = []

for _ in range(NUM_RUNS):

    start = time.perf_counter()

    with torch.no_grad():
        _ = model(dummy)

    end = time.perf_counter()

    torch_times.append(
        (end-start)*1000
    )

# ---------------------
# ONNX
# ---------------------

session = ort.InferenceSession(
    "Lab_Upgrade/models/exported_ca_nhan/resnet18.onnx"
)

onnx_times = []

input_name = session.get_inputs()[0].name

dummy_np = dummy.numpy()

for _ in range(NUM_RUNS):

    start = time.perf_counter()

    _ = session.run(
        None,
        {input_name: dummy_np}
    )

    end = time.perf_counter()

    onnx_times.append(
        (end-start)*1000
    )

# ---------------------
# Summary
# ---------------------

rows = []

rows.append({
    "runtime":"pytorch",
    "avg_ms":np.mean(torch_times),
    "min_ms":np.min(torch_times),
    "max_ms":np.max(torch_times)
})

rows.append({
    "runtime":"onnx",
    "avg_ms":np.mean(onnx_times),
    "min_ms":np.min(onnx_times),
    "max_ms":np.max(onnx_times)
})

df = pd.DataFrame(rows)

print(df)

df.to_csv(
    "Lab_Upgrade/outputs/runtime_benchmark_ca_nhan.csv",
    index=False
)