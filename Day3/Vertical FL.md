Also called as feature-based FL, it is applicable to cases where data sets share the same sample ID space but differ in feature space.

- For eg: Consider a bank and an e-commerce company, the user sets for both of them contain most of the residents of the area, but features space is different (bank records user revenue and exp whereas e-commerce retains user browsing and purchase history).
- We aggregate different features and build a model with data from both parties collaboratively.
- Here, 
$$\begin{equation}
 \mathcal{X_i} \ne \mathcal{X_j} ,\  \mathcal{Y_i} \ne \mathcal{Y_j},\ \mathcal{I_i} = \mathcal{I_j} \ \forall\  \mathcal{D_i, D_j}, i \ne j
\end{equation}$$
- Security Definition: In an honest-but-curious scenario, for two parties, the adversary can only learn data from client that is corrupted but not data from other client beyond what is revealed by input and output.
- When an honest third party is involved for colab, 
	- Part 1: Encrypted entity alignment: Due to diff user space, we use encrypted user ID alignment techniques to confirm common users
	- Part 2: Encrypted model training: Based on the common entities, 
		- colab C creates enc pairs, sends pk to A and B
		- A and B exchange encrypted intermediate results
		- After computing gradients and adding mask, they send the msgs to C
		- C decrypts and sends decrypted gradients and loss back to A and B, A and B unmask the same and update the model parameters accordingly

