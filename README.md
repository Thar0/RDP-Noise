# RDP Noise Reverse Engineering

This repository contains analysis tools for reverse engineering linear feedback shift registers used by the Nintendo 64's Reality Display Processor (RDP).

In particular, it analyzes the Color Combiner's NOISE input and determines the LFSRs responsible for generating the resulting bit patterns.

## Results

The RDP uses three different LFSRs to produce Color Combiner noise inputs of the form `abc100000` where `a`,`b`,`c` are the LFSR outputs for the current cycle. The use of 3 LFSRs is convenient to generate 3 largely uncorrelated bits per clock cycle.

Their polynomial forms are

$$
\begin{aligned}
a(x) &= x^{29} + x^2 + 1
\\
b(x) &= x^{28} + x^3 + 1
\\
c(x) &= x^{27} + x^5 + x^2 + x + 1
\end{aligned}
$$

Notably, these are all primitive polynomials with the smallest number of terms for their respective degrees 29, 28 and 27. They each achieve their maximum periods of `2^degree - 1`.

## Method

First, it is necessary to obtain samples from the console for examination. This is achieved by rendering noise pixels with some specific settings:
- A 1016x1 framebuffer. Switching to a new line eats 1 cycle of data, and we would like consecutive samples for later steps.
- 32-bit framebuffer. So that downsampling the output to the 5:5:5:3 pixel format does not destroy any information.
- 1-Cycle mode. This is so each pixel receives just one LFSR cycle.
- Blending and Dithering disabled. So that we can straightforwardly go from framebuffer pixels to Color Combiner pixels.
- Color Combiner configured to use `NOISE * PRIM_LOD_FRAC` for `PRIM_LOD_FRAC=255`. Ideally we wouldn't need to multiply, but it is not possible to place noise in a combiner slot that doesn't require multiplying it by something. `PRIM_LOD_FRAC` may be substituted for any other constant input configured to 255.

Once the framebuffer with these settings has been downloaded, `fb2data.py` transforms the framebuffer pixels into individual datasets for each bit `a`,`b`,`c`.

These datasets are used by `rdp_noise_lfsr.c` to determine the forms of the LFSR polynomials `a(x)`, `b(x)`, `c(x)`. For `a` and `b` the datasets output by `fb2data.py` are complete and sequential, determining the polynomials is just a straightforwrd application of the Berlekamp-Massey algorithm. For `c` the dataset is incomplete (see comments in `fb2data.py`) so instead a brute-force search over all primitive polynomials over GF(2) for degree <= 32 is performed until a sequence is found that matches the data.
