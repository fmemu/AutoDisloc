# Examples

| File | Content |
|---|---|
| `synthetic_Ti64_A.xy` | Synthetic Ti-6Al-4V pattern, ρ = 1.0×10¹⁵ m⁻², M* = 1.3, h⟨a⟩ = 0.86, size median 90 nm |
| `synthetic_Ti64_B.xy` | Same, ρ = 1.0×10¹¹ m⁻² (below the detection limit), size median 300 nm |
| `make_synthetic_example.py` | Generator (Wilkens whole-profile model, example instrument model, Cu Kα1+Kα2, Poisson noise) |

The true parameters are written in the header of each file. They are the worked examples of the whitepaper.
M* and Re* are in AutoDisloc's convention (η = L/Re*); in the MWP-fit/CMWP convention M* = 1.3 corresponds to
1.3/2.568 ≈ 0.51 (see the README, Limitations).

Plain two-column files carry no measurement data, so AutoDisloc would assume Cu Kα. The examples therefore
declare it in header lines, which you can also add to your own `.xy` / `.txt` / `.csv` files:

```text
# WL1 = 1.540598      (Kα1, Å)        or   # ANODE = Cu
# WL2 = 1.544426      (Kα2, Å)
# WLRATIO = 0.5       (Kα2/Kα1; 0 = Kα2 stripped)
# RADIUS = 250        (goniometer radius, mm)
```

```bash
python -m autodisloc --lang en analyze examples/synthetic_Ti64_A.xy examples/synthetic_Ti64_B.xy -c autodisloc/data/instrument_corundum_example.json -o report.xlsx
```
