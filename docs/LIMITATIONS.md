# SentinelNet — Architectural Limitations & Failure Modes

An honest, production-grounded assessment of where each tier in SentinelNet fails and the underlying mathematical or architectural causes.

---

## Tier 0: Static Deterministic Rules
* **Failure Mode:** Complete blindness to low-and-slow threats.
* **Why It Fails:** Thresholds on `packets_per_sec` and `bytes_per_sec` rely on volumetric surges. Stealthy C2 beaconing (1 packet every 45 seconds) and low-rate internal SMB lateral movements stay orders of magnitude below static thresholds, resulting in a **100% false negative rate on advanced persistent threats (APTs)**.
* **False Alarm Vulnerability:** Legitimate bulk transfers (e.g., database backups, large file synchronization) exceed volumetric thresholds, generating 330 false positive alerts in testing.

---

## Tier 1: Known-Signature LightGBM Classifier
* **Failure Mode:** Total vulnerability to zero-day attack patterns and unseen protocols.
* **Why It Fails:** Supervised decision trees learn orthogonal splits over historical training distributions. When evaluated on novel C2 exfiltration or stealth lateral movement, the feature vectors fall into benign leaf nodes, yielding **0.0% recall on unrepresented threat categories**.
* **IP Memorization Risk:** If IP addresses or ephemeral source ports are exposed to tree splits, LightGBM memorizes training subnets and achieves near-100% test accuracy while becoming completely useless against attacks originating from novel IP space. (Mitigated in SentinelNet by strictly barring routing metadata from the training matrix).

---

## Tier 2: Unsupervised PyTorch Autoencoder
* **Failure Mode:** Higher false alarm baseline on non-stationary, bursty benign applications.
* **Why It Fails:** Because the Autoencoder flags any high reconstruction MSE as anomalous, legitimate but rare network events (e.g., an executive joining an unfamiliar video conference software, unusual SSL certificate chains) generate high reconstruction errors, causing a **1.5% to 2.0% false alarm rate on benign traffic**. In an enterprise processing 10,000,000 flows/day, a 1.5% FAR would yield 150,000 alerts/day without Tier 1/Tier 3 arbitration.

---

## Tier 3: Temporal East-West Interaction Graph
* **Failure Mode:** North-South traffic pollution and enterprise dynamic IP churn (DHCP).
* **Why It Fails:** If North-South (Internet egress) flows are ingested into the interaction graph, everyday web browsing creates hundreds of novel external edges, triggering catastrophic false out-degree bursts. (Mitigated in SentinelNet by restricting Tier 3 strictly to East-West RFC1918 subnets).
* **DHCP Leases:** When a DHCP lease reassigns an IP address to a new machine, historical communication edges are invalidated, causing brief transient spikes in Jaccard edge novelty.

---

## Tier 4: Adversarial Evasion & Defense
* **Failure Mode:** Feature-space gradient attacks vs. packet-space real-world constraints.
* **Why It Fails:** Unbounded FGSM perturbations can generate mathematically adversarial vectors that violate packet-level protocol invariants (e.g., declaring negative TCP segment sizes or zero duration with non-zero bytes). SentinelNet bounds perturbations using coupled physics, but real-world adversaries with full payload encryption (e.g., TLS 1.3 with Encrypted Client Hello) obscure statistical flow features further.

---

## Tier 5: Cost Calibration & Drift Monitoring
* **Failure Mode:** Asymptotic p-value collapse in Kolmogorov-Smirnov test over large sample sizes.
* **Why It Fails:** For large window buffers ($N > 10,000$), the two-sample KS test p-value approaches zero ($p < 10^{-15}$) even for negligible, benign distribution shifts. (Mitigated in SentinelNet by prioritizing Population Stability Index [PSI] and Wasserstein Distance over raw KS p-values).
