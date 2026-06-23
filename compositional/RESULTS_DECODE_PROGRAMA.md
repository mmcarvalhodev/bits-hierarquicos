# DECODE-PROGRAMA NO CABEÇALHO — payload vira programa

Imagem 512×512. 'programa' = id da regra + parâmetros no cabeçalho; o decoder EXECUTA o programa em vez de ler o resultado.

| objeto | raw | WebP | decode-programa | programa vs WebP |
|---|---|---|---|---|
| anéis (GERADO por regra) | 786.4 KB | 37.8 KB | **21 B** | **1,798× menor** |
| foto (SINAL) | 786.4 KB | 64.0 KB | ≈ 64.0 KB (não há programa curto) | ~1× |

## LEITURA HONESTA

- **Para dado GERADO por regra, o programa no cabeçalho ESMAGA** — os anéis são 21 bytes (id + 5 parâmetros) e reconstroem EXATO, contra 37.8 KB do WebP, que não sabe que é uma fórmula e o trata como sinal de alta frequência. Tua intuição está certa: instruções no cabeçalho reduzem o payload — drasticamente, quando o dado é gerado.
- **Para SINAL (foto), o programa NÃO pode ser menor que a entropia** (Kolmogorov/Shannon: o menor programa que gera ruído é ~o próprio ruído). Aí o WebP reina e o programa não ajuda.
- **É a MESMA lei, na sua forma mais profunda:** payload→programa reduz exatamente na medida em que o dado é ESTRUTURA (gerado por regra) e não SINAL (ruído/perceptual). Gradiente, fórmula, composição, fractal, UI, cena procedural → programa minúsculo. Foto, áudio, textura orgânica → entropia manda.
- **O trade honesto:** mover a decode-instruction para o cabeçalho exige um decoder PROGRAMÁVEL (executa instruções) em vez de FIXO. Mais flexível e potencialmente minúsculo no payload, mas mais complexo — e com risco de segurança (executar instrução não-confiável: foi o buraco do PostScript/PDF/Flash). O JPEG é rígido mas seguro; o programável é poderoso mas pesa.
- **E a separação que o Márcio fez:** BH é o FORMATO que pode carregar esses decode-programas por região; Intent é o SISTEMA que computa a transformação de significado (encode texto→arquétipo, decode arquétipo→texto). Os dois usam 'dado-como-programa/estrutura', mas são coisas diferentes — o BH guarda; o Intent transforma.
