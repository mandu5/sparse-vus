"""Render verified constructed witnesses, separately from corpus prevalence."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "experiments/exploration/sampling_theory_20261023.json"
    data = json.loads(source.read_text())
    for name, expected in data["sources"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Witness source changed: {name}")
    rows = [r for r in data["overestimation"] if "same_label_competitor" in r]
    assert [r["L"] for r in rows] == [30, 100, 300]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(8.7, 3.05), layout="constrained",
                             gridspec_kw={"width_ratios": [1, 1.15]})
    rank = np.arange(1, 13)
    recall = (rank >= 4).astype(float)
    mass = np.zeros(12)
    mass[3:] = 1
    for k in range(4, 12):
        mass[k] = mass[k-1]+np.sqrt(1-(k-3)/30)
    precision = mass/rank
    ax = axes[0]
    ax.axvspan(4, 11, color="#f0d9ac", alpha=.45)
    ax.step(rank, recall, where="post", color="#222222", label="Exact recall")
    ax.plot(rank, precision, marker="o", ms=3, color="#007e87", label="Precision")
    ax.axvline(11, color="#a65d00", ls="--", lw=1)
    ax.annotate("Next sampled threshold", xy=(11, precision[10]), xytext=(6.0, .43),
                fontsize=8, arrowprops={"arrowstyle": "->", "color": "#a65d00"})
    ax.text(4.5, .84, "Buffer mass grows\nafter recall reaches 1", fontsize=8)
    ax.set(xlabel="Descending score rank", ylabel="Recall / precision",
           title="(a) Post-saturation inflation, w = 30", ylim=(-.02, 1.08), xlim=(.7, 12.3))
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.set_xticks([1, 4, 7, 11])
    ax = axes[1]
    x = np.arange(3)
    w = .17
    values = ([r["exact"] for r in rows], [r["sampled"] for r in rows],
              [r["same_label_competitor"]["exact"] for r in rows],
              [r["same_label_competitor"]["sampled"] for r in rows])
    labels = ["A exact", "A sampled", "B exact", "B sampled"]
    colors = ["#c07b24", "#c07b24", "#2860a4", "#2860a4"]
    for j, vals in enumerate(values):
        ax.bar(x+(j-1.5)*w, vals, width=w*.93, color=colors[j] if j%2==0 else "white",
               edgecolor=colors[j], hatch="///" if j%2 else None, linewidth=1, label=labels[j])
    ax.set(xticks=x, xticklabels=["L = 30", "L = 100", "L = 300"],
           ylabel="VUS-PR", ylim=(0, 1.38), title="(b) Every width included, H = 250")
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.legend(ncol=2, loc="upper left", fontsize=8, frameon=False)
    for i, row in enumerate(rows):
        ax.text(i, 1.01, f"regret {row['same_label_competitor']['wrong_selection_regret']:.3f}",
                ha="center", fontsize=8)
    out = ROOT / "paper/figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out/"sampling_witnesses.pdf", metadata={"Title": "Constructed threshold-sampling failures", "CreationDate": None})
    fig.savefig(out/"sampling_witnesses.png", dpi=180)
    receipt = {"source": source.relative_to(ROOT).as_posix(),
               "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "scope": "Constructed witnesses; no corpus prevalence inference"}
    (out/"sampling_witnesses.json").write_text(json.dumps(receipt, indent=2)+"\n")


if __name__ == "__main__":
    main()
