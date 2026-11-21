# Validation: reproduction of published numbers

Every item is repeated by an automated test in `tests/` (`python -m pytest tests`).

## 1. Burgers-vector population (h fractions) and b²C̄

### 1.1 Dragomir & Ungár 2002, J. Appl. Cryst. 35, 556, Section 5.3 (the source of the method)
For ECAP Ti, q₁ = −0.05 ± 0.02 and q₂ = 0.18 ± 0.02 were measured. The paper's result: ⟨a⟩ 75 ± 10 %, ⟨c⟩ 20 ± 5 %, ⟨c+a⟩ 5 ± 3 %; b²C̄ = 0.0222 nm².

| Our calculation (type average, Eqs. 10–13) | h_a | h_c | h_c+a | b²C̄ (nm²) |
|---|---|---|---|---|
| Step (i): all sub-systems except S3 | 0.763 | 0.224 | 0.013 | 0.0198 |
| Step (iii): prismatic ⟨a⟩ with double weight | 0.725 | 0.226 | 0.049 | **0.0220** |
| Paper | 0.75 ± 0.10 | 0.20 ± 0.05 | 0.05 ± 0.03 | **0.0222** |

**Reproduced.** The h fractions lie within the paper's error in both steps. With step (iii), b²C̄ = 0.0220 against 0.0222. With step (i), b²C̄ is 11 % lower, which would give an 11 % higher ρ. This difference is an uncertainty of the method itself; the report gives it as the b²C̄ range.

### 1.2 Muiruri, Maringa & du Preez 2020, Materials 13, 5355
- **b²C̄ (Table 4):** The b²C̄ values computed with the type average from the paper's h values agree with the paper to 4 digits for all five samples (0.0253 / 0.0245 / 0.0245 / 0.0252 / 0.0249). **Reproduced.**
- **h (Table 4) from q (Table 2):** **Not reproducible.** The paper's h values do not give its own q values. For sample A, h = 0.88/0/0.12 gives q₁ ≈ −0.14 back, while Table 2 lists −0.34. Every averaging tried (C-weighted, plain mean, b², b, b⁰ weights, q₁ only, q₂ only) and the 40-combination method give different results. Samples B and D have the same q₁, yet their h values change in opposite directions. The paper is internally inconsistent here, and its h values should not be used as a reference.
- **A(L) formula (Eq. 13):** not the Fourier transform of a Voigt profile (whitepaper, Section 8). Muiruri's ρ values (Table 5) therefore cannot be compared directly without the raw data.

### 1.3 The combination method (one sub-system per Burgers type)
`autodisloc.contrast.combinations()` solves Dragomir & Ungár 2002, Eqs. 11–13 for every combination of one ⟨a⟩, one ⟨c⟩ and one ⟨c+a⟩ sub-system (4 × 2 × 5 = 40 for Ti), i.e. the sub-systems are reduced to one per Burgers type (Dragomir 2002, §3.1). The test checks that every solution satisfies the three equations (Σh = 1 and the measured q₁, q₂ reproduced). The program reports the **mean of the physical solutions (all h between 0 and 1)**.

The only condition of the method is that the measured q lies inside the region attainable by Ti slip systems. Outside it, no combination is physical, and a free fit whose q lies outside the region can only be represented by the nearest physical point (e.g. the pure ⟨a⟩ corner).

**Constrained mWH.** The contrast factor is written directly with the h fractions:

ΔK² = α + K² Σ g_t P_t (1 + q₁ᵗ x + q₂ᵗ x²), g_t ≥ 0

so q is always physical and h always a proper fraction. When q is already inside the region the result equals the free fit (tested).

## 2. Modified Williamson–Hall

### Shintani, Murata et al. 2010, Mater. Trans. 51, 1067 (Mg AX52, hcp; FWHM table given)
From the 6 peak widths of Table 3, the paper's α = 4.29×10⁻⁵ nm⁻² and D = 137 nm are obtained only with **ΔK = 2cosθ·FWHM(2θ)/λ** (we obtain 4.44×10⁻⁵ and 135 nm). With the correct definition ΔK = cosθ·FWHM(2θ)/λ, α is four times smaller; q is unchanged. **Our mWH code reproduces the paper's numbers when the authors' own definition is used.**

## 3. Whole-profile (Wilkens) fit: the main result

- **Synthetic recovery:** Ti-6Al-4V patterns were generated with known ρ, M*, h and size distribution, the example instrument model and Poisson noise, and fitted. ρ is recovered within 2–18 % (largest deviation for the weakest broadening), h_a within 0.01–0.02; χ²/ν ≈ 1 (whitepaper, validation section; `tests/test_wholeprofile.py`).
- **Literature reference value:** Cottam et al. 2019, Metals 9, 60, SLM Ti-6Al-4V, eCMWP (neutron): ρ = (2.4 ± 0.3)×10¹⁵ m⁻², ⟨a⟩ 85 %, ⟨c+a⟩ 10 %, ⟨c⟩ 5 %.
- **Still open:** analysis of the same raw data with CMWP (Ribárik) for a direct comparison. The code uses the CMWP model (Wilkens + log-normal size + Dragomir contrast), but it has not been compared with the program itself.

## 4. Contrast-factor table
`TI_SUBSYSTEMS` was compared entry by entry with the Ti column of Table 2 of Dragomir & Ungár 2002; all 11 sub-systems agree. Muiruri Table 3 uses the same numbers.
