# GHCN station processing

Preprocessing and plotting methods for GHCN hourly and daily
ground station data.

## GHCN Daily

### Precip Measurement Flags Found

- **B**: Total from 2x 12-hour totals
- **D**: Total from 4x 6-hour totals
- **P**: Precip missing, presumed zero
- **T**: Trace precipitation

### Precip Quality Flags Found

- **D**: Failed duplicate check
- **G**: Failed gap check
- **I**: Failed internal consistency check
- **K**: Failed streak/frequent-value check
- **L**: Failed multi-day length check
- **N**: Failed naught check
- **O**: Failed climo outlier check
- **S**: Failed spatial consistency check
- **X**: Failed bounds check
- **Z**: Flagged from datazilla investigation

### Precip Source Flags Found

- **0**: USCRN Summary
- **1**: CF6 climate summary from NWS
- **2**: SSOD version 2
- **6**: CDMP Summary
- **7**: WxCoder3 Summary
- **A**: ASOS Real-time (post 2006)
- **B**: Older ASOS (2000-2005)
- **C**: Environment Canada
- **D**: NWS CF6 from high plains RCC
- **E**: European climate assessment
- **H**: High plains regional climate center
- **I**: International collection
- **K**: US Co-op from paper obs
- **N**: CoCoRaHS
- **R**: NCDC CRN and historical climo
- **S**: GTS synoptic reports (caution)
- **T**: SNOTEL
- **W**: WBAN/ASOS summary from ISD
- **X**: US First-order summary of the day
- **Z**: Datazilla additions or replacements
- **d**: NWS DSMs from high plains RCC
- **m**: Mexican CONAGUA
