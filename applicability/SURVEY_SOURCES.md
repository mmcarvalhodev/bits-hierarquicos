# Survey sources — BH applicability sweep

Each domain was researched by one web-grounded agent. Key citations below
(selected from the full set the agents returned). They ground the scorecard's
scores and verdicts in real data volumes, real tools, and real disagreement
problems — not opinion.

| domain | key sources |
|---|---|
| Knowledge graphs | hpcwire (Wikidata 16B triples), dbpedia.org, ScienceDirect (ontology alignment), ontotext (RDF-star) |
| Medical imaging | dicom.nema.org (DICOM WSI), learn.canceridc.dev (SEG references source), weasis.org, Nature s41467-025-66889-0 |
| Earth observation | earthdata.nasa.gov (COG), ogc.org (COG standard 2023), ceda.ac.uk (Sentinel PB volumes), up42 (cloud-native asset model) |
| Legal eDiscovery | relativity.com (processing + fields), trec.nist.gov (TREC legal), consilio.com (predictive coding) |
| Video / MAM | evolphin.com (PB masters), cloud.google.com (preservation masters), iconik.io (AI metadata), aws Rekognition segments |
| Dataset versioning | lakefs.io (zero-copy 10TB branching), DVC/lakeFS acquisition, Delta Lake / Iceberg time-travel |
| Data labeling | supervisely.com (consensus), cleanlab.ai (multiannotator), datasetninja COCO-2017, cvat.ai |
| Genomics | PMC3706896 (caller concordance), academic.oup.com/bioinformatics (CRAM), GATK GRCh38, biorxiv variant tools |
| Geospatial tiles | cogeo.org, registry.opendata.aws (Sentinel-2 COGs), wikipedia vector tiles, docs.ogc.org |
| CAD / BIM | PMC7099568, arxiv 2312.14931 (IFC versioning), ondsel.com (native-IFC), github ifc-git, ScienceDirect clash |
| Model checkpoints | arxiv 2311.03285 (S-LoRA), MLSys Punica, arxiv ExpertWeave, nebius (checkpoint TB sizes) |
| Agent memory | arxiv 2606.01435, databricks (memory scaling), vectorize (Mem0 vs Zep), Graphiti redundancy |
| Scientific sim / HPC | ceda.ac.uk (CMIP6 30PB), arxiv 2408.04440, unidata Zarr, WaveRange/zfp compression |
| Autonomous driving | nuscenes.org, waymo.com/open, arxiv 2303.06250, ICCV2025 SAM4D |
| Time-series / IoT | arxiv 1701.08530 (Gorilla), influxdata storage engine, cratedb IoT, expanso telemetry |
| RLHF / preference | huggingface Anthropic/hh-rlhf, arxiv 2410.14632 (MultiPref), crawler.sh (preference collection), nvidia HelpSteer |
| Distributed tracing | grafana.com/docs/tempo (TraceQL), clickhouse OTel storage, queue.acm.org, signoz (million spans) |
| 3D scenes / glTF | Khronos MSFT_lod + KHR_draco, cesium.com (Draco), CesiumGS/3d-tiles, CMU progressive mesh |
| Vector DBs (control) | research.ibm.com (100B vectors), aws OpenSearch quantization, weaviate (model upgrades), qdrant |
| Image/audio codecs (control) | exiv2 (JPEG metadata ~0.5%), wikipedia SVC, audioutils PCM, audio format comparison |

*Full citation lists (≈160 URLs) were returned by the survey agents; this is a
curated subset. Scores are research-informed estimates, not market data.*
