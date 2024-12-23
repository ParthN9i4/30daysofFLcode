The scenario where data sets share same feature space but different samples. For eg: Two regional banks might have different user groups but business is similar.

$$\mathcal{X}_i = \mathcal{X}_j, \mathcal{Y}_i = \mathcal{Y}_j, \mathcal{I}_i \ne \mathcal{I}_j\ \forall \mathcal{D}_i, \mathcal{D}_j, i \ne j$$

*Security Definition* : A horizontal FL system assumes honest participants and security against a honest-but-curious server. 

When it comes to architecture, there are k participants with same data structure learning in colab. The training process is as follows:

1. Participants locally compute training gradients, make a selection of gradients with encryption (DP or secret sharing) and send masked results of server
2. Server performs secure aggregation
3. Server sends back aggregated results to participants
4. Participants update their model with decrypted gradients

From the perspective of security, this arch protects data leakage against semi-honest server if grads are aggregated with [[SMPC]] or [[HE]]. But it is vulnerable to malicious participant training a [[GAN]] in the colab learning process.