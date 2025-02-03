Radio Frequency Fingerprint Identification (RFFID) is a novel approach that aims to differentiate devices based on their unique signal transmissions, rather than their given identities. This approach has promising applications in wireless security, spectrum management, and sensing. Current RFFID research uses deep learning due to its success in various domains, which is largely attributed to the availability of massive labeled datasets for training. However, unlike other domains, labeled data in RFFID is limited, and the labeling process is expensive. In this paper, we propose a label-efficient learning approach for RFFID based on Contrastive Predictive Coding (CPC), a pre-training method that learns to predict future samples given the past without labels. Afterward, the model is fine-tuned to identify the device. We evaluate our approach on a fingerprint dataset of 20 devices. Our results show that CPC learns effective representations of RF signals and outperforms fully supervised learning in both classification performance and label efficiency, requiring up to 10 times fewer labels while maintaining competitive accuracy. Finally, we evaluate CPC's robustness against noise and observe competitive performance after fine-tuning.
