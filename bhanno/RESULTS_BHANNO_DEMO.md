# bhanno — adversarial annotations over a shared substrate (measured demo)

- items: **200** · annotators: **5** · substrate: **1.20 MB** · labels: **59 KB**

## 1. The matrix of interpretations: shared substrate vs K copies

Holding K rival interpretations the usual way means **K annotated copies** — the heavy substrate stored K times. bhanno stores it **once** and co-registers K label layers.

| | bytes |
|---|---|
| `.bha` (substrate once + 5 layers) | **1,316,033 B** |
| 5 independent annotated copies | 6,059,255 B |
| **saving** | **4.6× smaller** |

> Hold 5 contesting interpretations for ~the price of one substrate + 5 thin layers. The saving approaches K as the substrate dominates — the wafer law (§3.4).

## 2. The readings (real bytes read)

| reading | what it returns | bytes read | % of file | vs full |
|---|---|---|---|---|
| `item(id)` | one shared substrate (1) | 62,778 B | 4.8% | **21× less** |
| `layer('alice')` | one annotator's labels (200) | 68,646 B | 5.2% | **19× less** |
| `item_views('img0002')` | ALL K views of one item (5) | 57,074 B | 4.3% | **23× less** |
| `disagreements()` | contested items (labels only) (75) | 116,033 B | 8.8% | **11× less** |
| `adjudicate()` | majority + agreement (labels only) (200) | 116,033 B | 8.8% | **11× less** |
| `full()` | everything (baseline) (200) | 1,316,033 B | 100.0% | **1× less** |

## 3. Adjudication (read from labels only, no substrate touched)

- agreement rate: **62%** (125 unanimous, **75 contested** of 200)
- example contested item `img0002`: votes {'alice': 8, 'bob': 3, 'carol': 8, 'dave': 3, 'erin': 8} → majority **8** (agreement 60%)

## What this demonstrates

- **Adverse interpretations cost ~1 substrate, not K.** The capability no format offers: K contesting labelings co-registered over data stored once.
- **Adjudication is a structural read.** `disagreements()` / `adjudicate()` find the contested items reading **only the label layers** — never the heavy substrate.
- **Honest boundary.** bhanno surfaces the contest; it does not decide who is right. Resolving truth is a modeling choice the envelope exposes.
