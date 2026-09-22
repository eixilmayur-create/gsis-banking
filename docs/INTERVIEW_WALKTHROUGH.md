# Three-Minute Interview Walkthrough

## Script

I built a Graph Schema Intelligence System to solve a common enterprise-data problem: different banking systems use different names for the same business concept. For example, Core Banking may use `customer`, CRM may use `client`, Cards may use `card_holder`, and Fraud may use `subject`. If every incoming name becomes a new graph class, the ontology quickly becomes duplicated and inconsistent.

My project is a 15-stage Python pipeline. It starts by generating deterministic synthetic data across six banking source files and profiling their schemas. The recorded run contains 4,450 records and 49 profiled fields. I created a banking RDF/OWL ontology with concepts such as Party, Customer, Merchant, Account, Card, Transaction, and RiskEvent, then transformed the source records into a 41,799-triple RDF knowledge graph.

The quality layer uses both SHACL and SPARQL. SHACL checks structural and datatype rules, while SPARQL checks referential integrity and duplicates. The pipeline intentionally injects bad records, and the run detected five SHACL violations plus three failing SPARQL rules, including a missing customer reference, a missing card account, and a missing risk-event transaction.

For semantic mapping, I generated Vertex AI embeddings for incoming schema terms and ontology definitions, calculated cosine similarity, and retained the top three candidates. I then used Gemini to reason over those candidates and recommend either reusing an existing concept or creating a new one. A collision detector checks whether the recommendation conflicts with ontology or semantic expectations.

Next, a confidence router combines 40% vector score and 60% Gemini score and treats collisions as governance signals. The thresholds were deliberately conservative, so all 12 mappings went to soft review or human escalation. Reviewers approved correct mappings, remapped `merchant_ref` to Merchant and fraud `subject` to Customer, and approved DigitalWallet as a new concept. Those decisions are written to a feedback store for reuse.

Finally, I evaluated the model recommendations against labeled ground truth. The measured pre-review mapping accuracy was 66.67%, collision recall was 50%, and there were no false automatic approvals because auto-approval coverage was zero. I present those as learning-pipeline results rather than production claims. The main lesson was that embeddings and LLM reasoning are useful evidence, but ontology governance still needs deterministic constraints, calibrated thresholds, and human review.

## Likely follow-up questions

### Why use both embeddings and Gemini?

Embeddings efficiently retrieve plausible ontology candidates. Gemini then reasons about business meaning and whether a concept should be reused or created. Separating retrieval from reasoning also preserves candidate evidence for auditing.

### Why are the similarity scores sometimes below 0.70?

Cosine similarity is model- and prompt-dependent and is not a calibrated probability. The project uses it as one feature in a hybrid confidence score rather than treating `0.70` as universal correctness.

### Why was mapping accuracy only 66.67%?

The result is pre-review accuracy on a small 12-term learning set. The errors expose real design work: ontology aliases, relationship-aware ranking, task-type selection, prompt calibration, and broader ground truth. I retained the result instead of overstating performance.

### What would you improve next?

I would expand the labeled dataset, calibrate thresholds using precision-recall analysis, add ontology aliases and hierarchy-aware scoring, version prompts and models, and move the review workflow from CSV files into an audited service.

### Where does Neo4j fit?

RDF/OWL is the semantic and validation source of truth. Neo4j is an optional serving projection for property-graph exploration. Keeping those responsibilities separate prevents the operational graph from replacing ontology governance.

