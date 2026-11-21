# Changelog

## 2.0.0 — 2026-11-12 (release preparation; numerical results unchanged)
- Output files (figures, Excel report, LaTeX/CSV tables, instrument models) record only the program name and version in their metadata; no author and no hidden marks.
- M* convention documented: the program's M* = Re*·√ρ with η = L/Re* (Re* = Re/2.877); M*(CMWP, Ribárik et al. 2001) = M*/2.568. Column help, manual, whitepaper and README give the conversion.
- The reference M* (default 2.64, band 1.5–4.0) is explained in the program (tooltip, assistant, warning when M* is fixed, Excel column help) and in the documentation: it is not a universal constant and should be set for the material and instrument.
- Warning when the intensities are not raw counts (declared counts per second, non-integer or very low values); the fit weights and error intervals assume raw counts. The intensity unit is listed in the Excel sheet "Measurement and material".
- Whole-profile fit: when every fit with M* fixed fails, no whole-profile result is reported (clear warning) instead of an error.
- Figures that cannot be drawn are reported in the tab, the Warnings tab and the status line instead of leaving the tab empty.
- The default name of an instrument model built from a standard is the file name of the standard, not its full path.
- Voigt-mWA option "eq13" (command line `--fourier voigt|eq13`) for the A(L) form of Muiruri et al. 2020 Eq. 13 / HajyAkbary et al. 2015 Eq. 23.
- Continuous integration tests the oldest supported (3.9) and the newest Python version.

## 2.0.0 — 2026-11-07
- Optional step-by-step assistant (data and measurement → material → instrument standard → options → summary), offered when an analysis is started ("do not ask again" possible) and available from the left panel.
- Other diffractometers: PANalytical XRDML reader; wavelengths, Kα2/Kα1 ratio and goniometer radius read from RAW, UXD and XRDML files and from header lines of two-column files; values a file lacks are flagged as assumed (dialog, assistant, Excel sheet "Measurement and material", warning); radiation (Cu, Co, Fe, Cr, Mo, Ag Kα or custom), Kα2 state and radius can be set by hand.
- Line standards: corundum, LaB6 (SRM 660c), Si (SRM 640f), CeO2 or other, with editable lattice parameters; peaks are indexed, foreign lines discarded, goniometer zero shift and displacement determined; warnings for a wrong standard/radiation, for a sample/standard wavelength mismatch and for a different goniometer radius (sample from another diffractometer). Optional zero-shift correction of the lattice parameters.
- Titanium alloy presets (Ti-6Al-4V, CP-Ti, custom); the nominal lattice is adjusted automatically when it would misplace a reflection by more than 0.35° (results with the right preset unchanged).
- Fit windows: expected peaks closer than 1.5° share a window (α 11.2/20.1 always together).
- Command line: --radiation, --radius, --standard, --std-lattice, --material, --lattice, --beta, --no-refine, --zero.
- Local builds (packaging/build_mac.sh, build_windows.bat) run in their own virtual environment with exactly the pinned versions, independent of conda or other Python installations.
- Manual: page numbers in the table of contents fixed (the contents page was searched as well).
- Licence compliance of the packaged applications: only LGPL-licensed Qt parts are packaged (allow-list), PySide6-Essentials instead of the full PySide6, third-party licence texts, GNU GPL/LGPL copies and Qt source information in every package (About › Third-party licences), Qt/PySide6 source archives attached to releases, pinned build requirements.
- CITATION.cff with abstract and thesis reference; .zenodo.json licence id `mit`; consistency test of the citation metadata.
- User manual: contents on its own page; statement that the calculation method is based on the dislocation-density measurement method of the author's doctoral thesis, and on the AI-assisted development.

## 2.0.0 — 2026-11-04
- Lattice parameters of α (a, c, c/a) by Cohen's method with the specimen-displacement term, and of β from the significant β reflections, with standard errors; shown in the program (new tab and summary columns), the Excel report and as CSV/LaTeX tables.
- User manual in English and Turkish with screenshots (docs/manual), opened from the program.
- Kα2 state of Bruker RAW 1.01 files read from the file header.
- Default instrument model: raw corundum measured 2026 (Kα1+Kα2 doublet fit); reference M* 2.64, band 1.5–4.0.
- Figures on screen keep their proportions (scaling by width and height).

## 2.0.0 — 2026-11-01
- Desktop program (PySide6) for macOS and Windows with a Turkish/English interface.
- Wilkens whole-profile fit (CMWP-type) as the main result, with Jacobian, M*-band and profile-likelihood 95 % intervals and detection-limit upper limits.
- Constrained modified Williamson–Hall: the contrast factor is written with the Burgers-type fractions, so q is always physically attainable.
- The 40-combination Burgers-vector method (one sub-system per type) for comparison.
- Voigt-based modified Warren–Averbach with the Fourier coefficients of the Voigt profile, reflection-dependent contrast factors and ρ = 2s/π; L-range sensitivity reported.
- Kα1/Kα2 doublet fitting of raw data; Bruker RAW v1.01, UXD and text readers.
- Publication-ready figures (PNG/TIFF 600 dpi, PDF, SVG), Excel report, CSV and LaTeX tables.
- Whitepaper in English and Turkish, built from the engine.
- Literature reproductions as automated tests (Dragomir & Ungár 2002; Muiruri et al. 2020; Shintani et al. 2010).
- Synthetic example patterns with known microstructure.
