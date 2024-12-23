Here, the two data sets differ in samples and feature space both.
- For eg: One is a bank in China and other is an e-commerce company in the US, so small intersection in user space and features as well.
- FTL is an extension of FL systems that deals with problems exceeding the scope of existing FL algorithms:
$$\mathcal{X_i} \ne \mathcal{X_j}, \mathcal{Y_i} \ne \mathcal{Y_j}, \mathcal{I_i} \ne \mathcal{I_j} \ \forall \mathcal{D_i}, \mathcal{D_j}, \mathcal{i \ne j}$$
- Security Definition: A FTL system involves two parties, the adversary can only learn data from client that is corrupted but not data from other client beyond what is revealed by input and output.

# Architecture
If two parties A and B have a very small set of overlapping samples, we use transfer learning to learn a common representation between features of party A and B, minimizing errors in predicting labels for the target domain party (say A) by leveraging labels in source-domain party (B).

Thus, in comparison to [[Vertical FL]], the gradient computations for A and B are different and still requires both parties to compute the prediction results.


