# SPEC — MODELO DE HARDWARE NATIVO (Bits Hierárquicos)
## Projeção transparente a partir dos testes reais de GPU

**Autor:** Márcio M. Carvalho
**Spec:** Junho 2026, v1.0
**Âncora empírica:** medições reais na RTX 3060 (`real_gpu.py`, `heavy_gpu.py`)
**Natureza:** MODELO de projeção — não é medição de hardware nativo (que não
existe). Cada parâmetro tem proveniência rotulada.

---

## 0. PRINCÍPIO DA SPEC

O documento de Dez/2025 cometeu o erro de afirmar ganhos de hardware (5-35×)
**sem modelo e sem medição**. Esta spec faz o oposto: define um **modelo
paramétrico** onde

```
[MEDIDO]        = vem dos nossos testes reais na RTX 3060
[PROJETADO]     = número físico/publicado, com a fonte (não medido por nós)
[ESPECULATIVO]  = propriedade de um silício BH-nativo que não existe
```

A saída do modelo é uma **projeção**, sempre rotulada. O valor não é o número;
é a rastreabilidade: troca-se um parâmetro e o resultado muda. Implementação:
`src/bench/native_model.py`.

---

## 1. PARÂMETROS E PROVENIÊNCIA

| símbolo | valor | proveniência | fonte |
|---|---|---|---|
| `BW_eff` | 342 GB/s | **[MEDIDO]** | redução cupy na 3060 (perto do teto 360) |
| `launch_floor` | 2,8 µs | **[MEDIDO]** | piso de lançamento de kernel (BH O(1)) |
| `T_build` | Bytes/BW_eff | **[MEDIDO]** | build lê o array 1× (bandwidth-bound) |
| `mem_latency` | 0,3 µs | **[PROJETADO]** | latência de acesso GDDR6 (~300 ns, publicado) |
| `e_byte` | ~5 pJ/B | **[PROJETADO]** | energia p/ mover 1 B de DRAM (ordem publicada; INCERTO) |
| `near_memory_build` | sim | **[ESPECULATIVO]** | controlador computa agregados na escrita |

---

## 2. EQUAÇÕES DO MODELO

```
Tempo flat (varredura):        T_flat   = Bytes_flat / BW_eff
Tempo BH (software):           T_bh_sw  = T_build + launch_floor        (consultas vetorizadas)
Tempo BH (nativo):             T_bh_nat = T_build_nat + N_q · mem_latency
   onde  T_build_nat = 0           se near_memory_build  [ESPECULATIVO]
                     = T_build      caso contrário        [MEDIDO]

Energia por operação:          E = Bytes_movidos · e_byte
   (memória domina; energia prop. a dados movidos — aproximação)

Ganho na aplicação (Amdahl):   S_app = 1 / ((1 - f) + f / S_op)
   f = fração do tempo da app que é a operação acelerada
```

---

## 3. PROJEÇÕES (com os parâmetros da §1)

### 3.1 Latência — consulta única (redução de 1 GB)

```
flat ......................... 2,92 ms   [MEDIDO]
BH software (piso lançamento)  2,80 µs   [MEDIDO]      -> 1.044×
BH NATIVO (latência memória) . 0,30 µs   [PROJETADO]   -> 9.747×
```
**O nativo recupera ~9× sobre o software** — porque o piso deixa de ser o
lançamento de kernel (artefacto de software) e passa a ser a latência física
de ler o agregado.

### 3.2 Tempo — lote de 6.000 consultas (flat varre 3,51 TB)

```
flat ......................... 10,26 s   [MEDIDO base]
BH software (build + gather) . 5,85 ms   -> 1.754×
BH NATIVO (build folded) ..... 1,80 ms   [PROJ+ESPEC]  -> 5.702×
```
O build (5,85 ms) é o custo dominante do BH no lote. Se o controlador o
calcula durante a escrita (near-memory, especulativo), ele some, e o ganho
sobe de ~1.755× para ~5.700×.

### 3.3 Energia — proporcional aos dados movidos

```
flat move 3,51 TB ............ 17,55 J   [MEDIDO bytes × PROJ energia]
BH move ~2 GB (build) ........ 10,00 mJ  -> 1.755× menos energia
```
A razão de energia ≈ razão de dados movidos (~1.755×) — porque para carga
bandwidth-bound a energia é dominada pelo movimento de dados.

---

## 4. SENSIBILIDADE

Os parâmetros [PROJETADO] são incertos; o modelo é honesto sobre isso:
- **`mem_latency`** (0,3 µs): é o PISO físico (latência de memória), um teto
  OTIMISTA. Um primitivo BH-nativo real teria latência ≥ esta. Dobrar para
  0,6 µs corta o ganho single-shot pela metade (~4.900×).
- **`e_byte`** (5 pJ/B): ordem de grandeza publicada. A razão de energia NÃO
  depende do valor absoluto (cancela), só do *quociente de bytes movidos* —
  esse é [MEDIDO]. Logo o "~1.755× menos energia" é robusto; o valor absoluto
  em Joules é que é incerto.
- **`near_memory_build`**: liga/desliga o ganho extra no lote (1.755× ↔ 5.700×).

---

## 5. LIMITES (o que o modelo NÃO captura)

```
- design real de silício, área, custo de fabricação (anos, foundry).
- overhead do compute near-memory (assumido ~0; real > 0 — otimista).
- a latência nativa é a latência de MEMÓRIA, não de um primitivo BH medido
  (que não existe). É piso físico, teto de ganho.
- Amdahl governa o nível da aplicação: S_app = 1/((1-f)+f/S_op). Um ganho de
  operação de 9.747× numa app que gasta 90% nisso dá ~10× de app.
- vale só para carga bandwidth-bound + agregação/range + dado reusado.
```

---

## 6. COMO USAR ESTA SPEC

```
1. Os números [MEDIDO] são fixos (vêm da 3060). Não os invente.
2. Os [PROJETADO] são parâmetros — declare a fonte e varie na análise.
3. Os [ESPECULATIVO] são hipóteses — marque cada conclusão que depende deles.
4. Toda saída é PROJEÇÃO até existir silício e medição. Nunca reporte uma
   linha deste modelo como "medimos X× em hardware nativo".
```

Reprodução: `X:/miniconda3/python.exe src/bench/native_model.py`.

---

*A diferença entre esta spec e o doc de Dez/2025: aquele afirmou hardware sem
modelo; esta dá um modelo com cada entrada rastreável — e diz, em cada linha,
o que é medido, o que é físico-publicado e o que é especulação.*
