# AutoDisloc 2

**Dislocation density of hcp α/α′ titanium alloys (Ti-6Al-4V, CP-Ti, …) from X-ray line profile analysis**

[Türkçe](README.tr.md) · [User manual (PDF)](docs/manual/AutoDisloc2_Manual_EN.pdf) · [Whitepaper (PDF)](docs/whitepaper/AutoDisloc2_Whitepaper_EN.pdf) · [Validation](docs/validation.md) · License: MIT

AutoDisloc computes the dislocation density ρ, the Burgers-vector population (fractions of ⟨a⟩, ⟨c⟩ and ⟨c+a⟩ dislocations) and the Wilkens arrangement parameter M* from laboratory X-ray diffraction patterns. It combines three established line-profile methods:

| Step | Method | Role |
|---|---|---|
| 1 | Voigt peak fitting (Kα1 + Kα2 doublets), instrument model from a line standard | peak widths, lattice parameters |
| 2 | Modified Williamson–Hall (mWH) with the Dragomir–Ungár hexagonal contrast factors, constrained to physically attainable Burgers-vector populations | contrast factors, Burgers-vector population |
| 3 | **Wilkens whole-profile fit** (CMWP-type): size (log-normal spheres) × dislocation (Wilkens) × instrument Fourier coefficients fitted directly to the measured profiles | **main result: ρ with a 95 % interval, M*, h, size** |
| – | Voigt-based modified Warren–Averbach (mWA) | reported for comparison |

The mathematics is derived step by step in the [whitepaper](docs/whitepaper/AutoDisloc2_Whitepaper_EN.pdf), using a synthetic Ti-6Al-4V pattern with known microstructure as the worked example.

## Desktop program (macOS and Windows)

The [user manual](docs/manual/AutoDisloc2_Manual_EN.pdf) explains installation, every window element and all outputs step by step, with screenshots. It is also opened with the *User manual* button of the program.

The interface is in Turkish and English (switch with the **TR | EN** buttons in the toolbar).

| | macOS | Windows |
|---|---|---|
| Ready-made application | Download `AutoDisloc2_macOS.zip` (Apple Silicon) from the Releases page and unzip it. The app is not signed by Apple: open it once, then *System Settings › Privacy & Security › Open Anyway* (macOS 14 and earlier: right-click › **Open**). On Intel Macs run from source. | Download `AutoDisloc2_Windows.zip` from the Releases page and unzip it; if SmartScreen warns, *More info › Run anyway*. Or build it with `packaging\build_windows.bat` |
| Run from source | double-click `AutoDisloc2_Mac.command` | double-click `AutoDisloc2_Windows.bat` |

Requirements for running from source: Python ≥ 3.9 and `pip install -r requirements.txt`.

Workflow (optionally guided by the **Step-by-step assistant**, which asks for every input in turn and is offered when an analysis is started):
1. **Instrument model.** An example model (corundum standard of the diffractometer used in developing the program) is loaded. Build your own from a line-standard pattern measured with the same slits: *Build from a standard pattern…*, choosing the standard material (LaB6 SRM 660c, Si SRM 640f, CeO2, corundum or *other*) and, if certified, its lattice parameter. The peaks are indexed, foreign lines are discarded and the goniometer zero shift is determined.
2. **Samples.** *Add…* the patterns: Bruker RAW v1.01 (`.raw`), Bruker UXD (`.uxd`), PANalytical XRDML (`.xrdml`) or two-column `.xy/.dat/.txt/.csv`. Double-click a name to change it; the name is used in figures and tables.
3. **Measurement and material.** Wavelengths, Kα2/Kα1 ratio and goniometer radius are read from the files; whatever a file lacks is shown as *assumed* and can be set by hand (Cu, Co, Fe, Cr, Mo, Ag Kα or custom; two-column files can carry `# WL1 = …` header lines, see `examples/README.md`). Raw (unstripped) data are recommended: every peak is modelled as a Kα1 + Kα2 doublet. Alloy presets: Ti-6Al-4V (α/α′ + β), CP-Ti (α) or custom lattice parameters; the contrast factors are those of α-Ti.
4. **Run analysis.** Tabs: Summary (comparison chart and table), Pattern, Whole profile, mWH, mWA, Burgers vector, Fourier components, Instrument, Warnings, Peak table.
5. **Export.** *Save this figure…* (PNG/TIFF 600 dpi, PDF, SVG) or *Export all (paper package)…*: every figure in four formats, an Excel report with a column-help sheet, and the result table as CSV and LaTeX. Output files record only the program name and version (e.g. "AutoDisloc 2.0.0") in their metadata.

Figures are drawn at journal column widths (8.5 cm and 17.5 cm) with a colour-vision-deficiency-safe palette.

## Command line

```bash
python -m autodisloc --lang en instrument STANDARD.raw -o instrument.json
python -m autodisloc --lang en analyze S1.raw S2.raw -c instrument.json -o report.xlsx --package paper_package
```

Options: `--ka2 auto|present|stripped`, `--radiation Cu|Co|Fe|Cr|Mo|Ag|WL1,WL2[,RATIO]`, `--radius MM`, `--standard corundum|LaB6|Si|CeO2|other` and `--std-lattice A[,C]` (instrument), `--material Ti-6Al-4V|CP-Ti`, `--lattice A,C[,Aβ]`, `--zero`, `--mwh constrained|free`, `--fourier voigt|eq13` (A(L) of the Voigt-mWA: Voigt transform, or Muiruri 2020 Eq. 13 for comparison), `--mc N` (Monte Carlo draws of the Voigt-mWA), `--no-whole-profile`. Turkish command names (`cihaz`, `analiz`) are equivalent.

As a library:

```python
from autodisloc import read_pattern, InstrumentModel, analyze, set_language
set_language("en")
inst = InstrumentModel.load("instrument.json")
res = analyze(read_pattern("examples/synthetic_Ti64_A.xy"), inst, "A")
print(res.summary()["rho_text"], res.wp.M_star, res.wp.h)
```

## Repository layout

| Path | Content |
|---|---|
| `autodisloc/` | engine, desktop program (`gui.py`), figures, report, Turkish/English texts (`i18n.py`) |
| `autodisloc/data/` | example instrument model |
| `docs/manual/` | user manual in English and Turkish (PDF/HTML), screenshots and build scripts |
| `docs/whitepaper/` | whitepaper in English and Turkish (PDF/HTML) and the script that builds it from the engine |
| `docs/validation.md` | reproduction of published numbers |
| `examples/` | synthetic Ti-6Al-4V patterns with known microstructure and their generator |
| `tests/` | automated tests (`python -m pytest tests`) |
| `packaging/` | PyInstaller definition and build scripts for macOS and Windows |

## Limitations

- The contrast-factor constants are those of pure Ti (Dragomir & Ungár 2002).
- The average contrast factor assumes an untextured polycrystal; strongly textured reflections are flagged (Harris texture index).
- For weakly broadened samples, ρ and M* cannot be determined together; M* is then fixed and the interval covers a band of M* (whitepaper, Section 10). The default reference M* = 2.64 (band 1.5–4.0) is only the geometric mean of the free-fit M* (2.17 and 3.21) of two well-conditioned samples measured during the development of the program with the example instrument model; it is not a universal constant. ρ then depends on the assumed M* (a larger M* gives a smaller ρ), so set the reference M* (option *Reference M\**) to a value appropriate for your material and instrument, e.g. from free fits of your own well-conditioned samples.
- **M* convention.** The program evaluates the Wilkens function f*(η) at η = L/Re* with Re* = Re/(e^1.75/2) = Re/2.877, where Re is the cut-off radius of the logarithmic form ln(Re/L) of the mWA equation, and reports M* = Re*·√ρ. Wilkens and MWP-fit/CMWP use η = ½·e^(−1/4)·L/Re* and M* = Re*·√ρ ([Ribárik, Ungár & Gubicza 2001, J. Appl. Cryst. 34, 669, Eq. 4](https://doi.org/10.1107/S0021889801011451); Re = e²·Re*). For the same physical state, **M\*(CMWP) = M\*(AutoDisloc) / (2·e^(1/4)) = M\*(AutoDisloc) / 2.568** (same factor for Re*). The arrangement parameter M = Re·√ρ of [Ungár et al. 2001, J. Appl. Cryst. 34, 298](https://doi.org/10.1107/S0021889801003715) (Eq. 25a, Re of the ln form) equals 2.877 × M\*(AutoDisloc). ρ is the same in all conventions.
- The least-squares weights (1/√y) and therefore the χ²/dof and the error intervals assume raw counts. Files in counts per second, normalised or otherwise processed intensities are analysed the same way, but a warning is shown; raw-count data are recommended.
- A direct comparison with the CMWP program on identical data has not yet been made.

## License

AutoDisloc is released under the [MIT License](LICENSE). The ready-made applications also contain third-party components (Qt/PySide6 under the GNU LGPLv3, NumPy, SciPy, pandas, matplotlib, openpyxl, Pillow, Python); see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Their licence texts are inside each package (*About › Third-party licences*), and the Qt source archives are attached to each release.

## Development

The calculation method of AutoDisloc is based on the dislocation-density measurement method of the author's doctoral thesis (TOBB University of Economics and Technology, 2025). The Python implementation, the graphical user interface, the reports, the packaging and the documentation were developed with the assistance of Claude Opus 5.5 (Anthropic) under the author's direction and review.

## Citation

If you use AutoDisloc in scientific work, please cite it as given in [CITATION.cff](CITATION.cff) (GitHub: *Cite this repository*; Zenodo DOI on each release).

© 2026 Fırat Memu · MIT License
