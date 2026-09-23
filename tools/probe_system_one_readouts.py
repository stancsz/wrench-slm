"""Compare small readouts on saved, unsealed Qwen training features only.

The independent evaluation requests and labels are deliberately not opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def score(logits, target):
    prediction = logits >= 0
    positive = target.bool()
    return {
        "accuracy": float((prediction == positive).float().mean()),
        "eligible_coverage": float(prediction[positive].float().mean()),
        "unsafe_passes": int(prediction[~positive].sum()),
        "rows": int(target.numel()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    data = torch.load(args.features, map_location="cpu", weights_only=True)
    x = data["features"].float()
    y = data["labels"].long()
    train = torch.tensor(data["train_indexes"])
    cal = torch.tensor(data["calibration_indexes"])
    if len(x) != len(y) or len(cal) < 20 or len(train) < 20 or set(train.tolist()) & set(cal.tolist()):
        raise ValueError("invalid saved feature split")
    xt, yt, xc, yc = x[train], y[train], x[cal], y[cal]
    plain = torch.tensor([i % 2 == 1 for i in cal.tolist()])
    results = []

    similarity = xc @ xt.T
    for k in (1, 3, 5, 11, 21):
        values, indices = similarity.topk(k, dim=1)
        votes = (yt[indices].float() * values.softmax(-1)).sum(-1)
        margin = votes - .5
        results.append({"model": f"cosine_knn_{k}", "all": score(margin, yc),
                        "plain": score(margin[plain], yc[plain])})

    # Kernel ridge is a small non-linear readout over the same frozen features.
    kernel_train = xt @ xt.T
    for sharpness in (10., 30., 100.):
        train_kernel = torch.exp(sharpness * (kernel_train - 1))
        cal_kernel = torch.exp(sharpness * (similarity - 1))
        for ridge in (.01, .1, 1.):
            alpha = torch.linalg.solve(train_kernel + ridge * torch.eye(len(xt)),
                                       yt.float() * 2 - 1)
            margin = cal_kernel @ alpha
            results.append({"model": f"rbf_{sharpness:g}_ridge_{ridge:g}",
                            "all": score(margin, yc), "plain": score(margin[plain], yc[plain])})

    for width in (0, 32, 64, 128):
        torch.manual_seed(47)
        head = (torch.nn.Linear(x.shape[-1], 2) if width == 0 else
                torch.nn.Sequential(torch.nn.Linear(x.shape[-1], width),
                                    torch.nn.GELU(), torch.nn.Linear(width, 2)))
        optimizer = torch.optim.AdamW(head.parameters(), lr=.03 if width == 0 else .003,
                                       weight_decay=.01)
        for _ in range(400):
            loss = torch.nn.functional.cross_entropy(head(xt), yt)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
        with torch.inference_mode():
            logits = head(xc)
            margin = logits[:, 1] - logits[:, 0]
        results.append({"model": "linear" if width == 0 else f"mlp_{width}",
                        "all": score(margin, yc), "plain": score(margin[plain], yc[plain])})

    receipt = {"schema": "wrench.system-one-unsealed-readout-probe.v1",
               "feature_source": str(args.features), "independent_evaluation_read": False,
               "train_vectors": len(train), "calibration_vectors": len(cal),
               "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    for item in sorted(results, key=lambda item: item["plain"]["accuracy"], reverse=True):
        print(item["model"], item["plain"], item["all"])


if __name__ == "__main__":
    main()
