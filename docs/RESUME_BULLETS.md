# Resume Bullets

## Recommended version

- Built a 15-stage Graph Schema Intelligence System in Python for governing schema integration across six synthetic retail-banking sources, profiling 49 fields and converting 4,450 records into a 41,799-triple RDF knowledge graph.
- Combined Vertex AI embeddings, cosine retrieval, Gemini semantic mapping, RDF/OWL constraints, SHACL, and SPARQL to recommend ontology reuse or creation while preserving auditable evidence for every mapping decision.
- Implemented confidence-based routing, semantic collision detection, and human review for 12 labeled mappings; identified one semantic mismatch and captured 12 completed reviewer decisions including remaps and approval of a new `DigitalWallet` concept.
- Created deterministic graph-quality controls that surfaced five SHACL violations and three referential-integrity failures while confirming four of seven SPARQL checks passed.
- Evaluated the learning pipeline against labeled ground truth, measuring 66.67% pre-review mapping accuracy, 50% collision recall, and 0 false automatic approvals; documented threshold calibration and dataset-size limitations.

## Short version

- Developed a Python-based semantic-governance pipeline using Vertex AI, Gemini, RDF/OWL, SHACL, SPARQL, and Neo4j to map heterogeneous banking schemas into a controlled ontology.
- Processed 4,450 synthetic records into a 41,799-triple graph and implemented validation, collision detection, confidence routing, human review, feedback capture, and ontology-migration analysis.
- Evaluated 12 schema mappings against ground truth and documented measured accuracy, collision recall, validation findings, and conservative automation behavior.

## Accuracy note

Use “pre-review mapping accuracy” when quoting 66.67%. Do not describe it as production accuracy. The evaluation contains 12 labeled mappings, and the recorded run automatically approved none of them.

