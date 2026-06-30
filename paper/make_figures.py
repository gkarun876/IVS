"""Generate the two data figures for the IVS paper."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
})

# ── Figure 1: Positional Entropy Profile ────────────────────────────────────
positions = [0, 1, 2, 3, 4, 5, 6, 7]
entropy   = [6.579, 6.021, 6.124, 5.985, 5.708, 5.502, 5.181, 5.073]

fig, ax = plt.subplots(figsize=(6, 3.8))

ax.plot(positions, entropy, "o-", color="#1a4c7a", linewidth=2,
        markersize=7, markerfacecolor="white", markeredgewidth=2,
        zorder=3)

# Annotate the key drop
ax.annotate("", xy=(1, entropy[1]), xytext=(0, entropy[0]),
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5))
ax.text(0.5, (entropy[0]+entropy[1])/2 + 0.07,
        "−0.558 bits", ha="center", va="bottom", fontsize=9,
        color="#c0392b", fontstyle="italic")

ax.set_xlabel("Sign position in inscription (0 = initial)")
ax.set_ylabel("Shannon entropy (bits)")
ax.set_title("Figure 1 — Positional Entropy Profile ($N = 2{,}742$)")
ax.set_xticks(positions)
ax.set_ylim(4.8, 7.0)
ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("fig1_entropy.pdf", bbox_inches="tight")
fig.savefig("fig1_entropy.png", bbox_inches="tight", dpi=300)
print("Saved fig1_entropy.pdf / .png")

# ── Figure 2: Geographic Gradient ───────────────────────────────────────────
sites      = ["Mohenjo-daro\n(train)", "Harappa", "Lothal",
              "Chanhudaro", "Kalibangan", "Other\nSites", "West Asian"]
vs_random  = [9.94, 6.19, 6.01, 5.29, 5.34, 4.05, 1.08]
sample_n   = [1347, 1103, 112, 58, 80, 29, 13]
# Approximate geographic distance from MD (km, rough)
distances  = [0, 570, 650, 140, 730, None, 1500]

colors = []
for v in vs_random:
    if v >= 9:
        colors.append("#1a4c7a")
    elif v >= 5:
        colors.append("#2980b9")
    elif v >= 2:
        colors.append("#85c1e9")
    else:
        colors.append("#d5e8f3")

fig, ax = plt.subplots(figsize=(7, 4))

bars = ax.barh(sites[::-1], vs_random[::-1], color=colors[::-1],
               edgecolor="white", linewidth=0.5, height=0.6, zorder=3)

# Random baseline reference line
ax.axvline(0, color="#888", linewidth=1.2, linestyle="--", zorder=2)
ax.text(0.1, -0.6, "random\nbaseline", fontsize=8, color="#888",
        va="top", ha="left")

# Annotate n= on each bar
for bar, n, v in zip(bars, sample_n[::-1], vs_random[::-1]):
    ax.text(v + 0.15, bar.get_y() + bar.get_height()/2,
            f"n={n}", va="center", fontsize=8, color="#333")

ax.set_xlabel("Log-likelihood above random baseline (bits/bigram)")
ax.set_title("Figure 2 — Geographic Grammar Gradient\n"
             "Trained on Mohenjo-daro, scored at all sites ($Z = 50.12$, $p = 0$)")
ax.set_xlim(-0.5, 12)
ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))
ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("fig2_gradient.pdf", bbox_inches="tight")
fig.savefig("fig2_gradient.png", bbox_inches="tight", dpi=300)
print("Saved fig2_gradient.pdf / .png")
