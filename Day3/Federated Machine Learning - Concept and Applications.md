# Authors
	1. QUING YANG, Hong Kong University of Science and Technology
	2. YANG LIU, Webank, China
	3. TIANJIAN CHEN, Webank, China
	5. YONGXIN TONG, Beihang University, China

- In a sensitive domain, such as Healthcare, where data is of utmost importance, it can be difficult to break the barriers between data sources. 
- In contrast to traditional machine learning where data is collected at a central server for training and inference, we require a method that leaks minimal to zero information about any individual. 
- Hence, simple data transaction models where one party collects and another party does the cleaning of data, passes on to yet another party that builds the final version of the model. Such a pipeline faces challenges with the new data regulations and laws. 
- In this situation, where our data is in isolated islands which cannot always be fused and collected together, *[[federated learning]]* comes to the rescue.
## Main idea
Since the data is stored across multiple devices,we train models on individual datasets locally.

## Privacy in FL
Privacy Techniques in FL include:
1. [[SMC]]
2. [[DP]]
3. [[k-anonymity]]
4. [[HE]]
### Indirect Information Leakage
Even though the raw data is not leaked, parameter updates can leak information. Various types attacks include:
1. [[Backdoor attack]]
2. [[Inference attacks]]
3. [[Model poisoning]]

## Categorization of FL:
Let $\mathcal{X}$ be the feature space, $\mathcal{Y}$ is the label space and $\mathcal{I}$ be the sample ID space.

1. [[Horizontal FL]]
2. [[Vertical FL]]
3. [[Federated Transfer Learning (FTL)]]

## [[PPML]]
- FL can be considered as Privacy preserving decentralized collaborative ML, hence it is related to multi-party PPML.

## Keywords:
1. [[Privacy Preserving Data Mining]]
2. [[Secure FL]]
3. [[Semi-supervised FL]] 
4. [[PPM]]
5. [[DAP]]
6. [[VDAF]]
7. 