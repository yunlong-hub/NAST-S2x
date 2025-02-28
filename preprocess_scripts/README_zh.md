# CVSS-C 数据预处理

这些脚本从零开始处理 CVSS-C 数据，以便用于 StreamSpeech 的训练和测试。

- [步骤 1：下载 CoVoST 2 和 CVSS-C 数据](#步骤-1下载-covost-2-和-cvss-c-数据)
- [步骤 2：下载预训练模型](#步骤-2下载预训练模型)
- [步骤 3：处理训练和测试数据](#步骤-3处理训练和测试数据)
- [最终版本](#最终版本)

---

### 步骤 1：下载 CoVoST 2 和 CVSS-C 数据

- 从以下地址下载 CoVoST 2 和 CVSS-C 数据：

  - [CoVoST: 大规模多语言语音到文本翻译语料库](https://github.com/facebookresearch/covost)

  - [CVSS: 大规模多语言语音到语音翻译语料库](https://github.com/google-research-datasets/cvss)

- 数据的目录结构如下。将 `/data/zhangshaolei/datasets` 替换为你的本地路径 `XXX`。

```
/data/zhangshaolei/datasets
├── covost2/
│   ├── fr/
│   │   ├── clips/
│   │   ├── covost_v2.fr_en.tsv
│   │   ├── train.tsv
│   │   ├── dev.tsv
│   │   ├── test.tsv
│   │   ├── other.tsv
│   │   ├── validated.tsv
│   │   ├── invalidated.tsv
│   │   └── covost_v2.fr_en.tsv.tar.gz
│   ├── de/
│   │   ├── clips/
│   │   ├── covost_v2.de_en.tsv
│   │   ├── train.tsv
│   │   ├── dev.tsv
│   │   ├── test.tsv
│   │   ├── other.tsv
│   │   ├── validated.tsv
│   │   ├── invalidated.tsv
│   │   └── covost_v2.de_en.tsv.tar.gz
│   ├── es/
│   │   ├── clips/
│   │   ├── covost_v2.es_en.tsv
│   │   ├── train.tsv
│   │   ├── dev.tsv
│   │   ├── test.tsv
│   │   ├── other.tsv
│   │   ├── validated.tsv
│   │   ├── invalidated.tsv
│   │   └── covost_v2.es_en.tsv.tar.gz
│   └── ...
└── cvss/
│   ├── cvss-c/
│   │   ├── fr-en/
│   │   │   ├── train/
│   │   │   ├── dev/
│   │   │   ├── test/
│   │   │   ├── train.tsv
│   │   │   ├── dev.tsv
│   │   │   ├── test.tsv
│   │   │   └── cvss_c_fr_en_v1.0.tar.gz
│   │   ├── de-en
│   │   │   ├── train/
│   │   │   ├── dev/
│   │   │   ├── test/
│   │   │   ├── train.tsv
│   │   │   ├── dev.tsv
│   │   │   ├── test.tsv
│   │   │   └── cvss_c_de_en_v1.0.tar.gz
│   │   ├── es-en
│   │   │   ├── train/
│   │   │   ├── dev/
│   │   │   ├── test/
│   │   │   ├── train.tsv
│   │   │   ├── dev.tsv
│   │   │   ├── test.tsv
│   │   │   └── cvss_c_es_en_v1.0.tar.gz
│   │   ├── ...
└──...
```

---

### 步骤 2：下载预训练模型

- 在 [0.download_pretrain_models.sh](./0.download_pretrain_models.sh) 中，将 `ROOT` 替换为 StreamSpeech 仓库的本地路径，运行以下命令：

```shell
bash 0.download_pretrain_models.sh
```

---

### 步骤 3：处理训练和测试数据

- 在 `1.XXX.sh`, `2.XXX.sh`, ... 和 `9.XXX.sh` 文件中，将 `ROOT` 和 `DATA_ROOT` 替换为你的本地路径 `XXX`，然后运行：

```shell
bash preprocess.sh
```

- 修改配置文件 `./configs/fr-en/config_gcmvn.yaml` 和 `./configs/fr-en/config_mtl_asr_st_ctcst.yaml` 中的绝对路径为你的本地路径 `XXX`，然后将它们放到 `cvss-c/fr-en/fbank2unit` 目录下。

  `cvss-c/fr-en/fbank2unit/config_gcmvn.yaml` 示例：

  ```yaml
  global_cmvn:
    stats_npz_path: /XXX/cvss/cvss-c/fr-en/gcmvn.npz 
  input_channels: 1
  input_feat_per_channel: 80
  specaugment:
    freq_mask_F: 27
    freq_mask_N: 1
    time_mask_N: 1
    time_mask_T: 100
    time_mask_p: 1.0
    time_wrap_W: 0
  transforms:
    '*':
    - global_cmvn
    _train:
    - global_cmvn
    - specaugment
  vocoder:
    checkpoint: /XXX/StreamSpeech/pretrain_models/unit-based_HiFi-GAN_vocoder/mHuBERT.layer11.km1000.en/g_00500000
    config: /XXX/StreamSpeech/pretrain_models/unit-based_HiFi-GAN_vocoder/mHuBERT.layer11.km1000.en/config.json
    type: code_hifigan
  ```

  `cvss-c/fr-en/fbank2unit/config_mtl_asr_st_ctcst.yaml` 示例：

  ```yaml
  target_unigram:
     decoder_type: transformer
     dict: /XXX/cvss/cvss-c/fr-en/tgt_unigram6000/spm_unigram_fr.txt
     data: /XXX/cvss/cvss-c/fr-en/tgt_unigram6000
     loss_weight: 8.0
     rdrop_alpha: 0.0
     decoder_args:
        decoder_layers: 4
        decoder_embed_dim: 512
        decoder_ffn_embed_dim: 2048
        decoder_attention_heads: 8
     label_smoothing: 0.1
  source_unigram:
     decoder_type: ctc
     dict: /XXX/cvss/cvss-c/fr-en/src_unigram6000/spm_unigram_fr.txt
     data: /XXX/cvss/cvss-c/fr-en/src_unigram6000
     loss_weight: 4.0
     rdrop_alpha: 0.0
     decoder_args:
        decoder_layers: 0
        decoder_embed_dim: 512
        decoder_ffn_embed_dim: 2048
        decoder_attention_heads: 8
     label_smoothing: 0.1
  ctc_target_unigram:
     decoder_type: ctc
     dict: /XXX/cvss/cvss-c/fr-en/tgt_unigram6000/spm_unigram_fr.txt
     data: /XXX/cvss/cvss-c/fr-en/tgt_unigram6000
     loss_weight: 4.0
     rdrop_alpha: 0.0
     decoder_args:
        decoder_layers: 0
        decoder_embed_dim: 512
        decoder_ffn_embed_dim: 2048
        decoder_attention_heads: 8
     label_smoothing: 0.1
  ```

---

### 最终版本

- CVSS-C 的目录结构应如下所示：

```
/data/zhangshaolei/datasets
├── covost2/
│   └── ... # 无变化
└── cvss/
│   ├── cvss-c/
│   │   ├── fr-en/
│   │   │   ├── train/
│   │   │   ├── dev/
│   │   │   ├── test/
│   │   │   ├── train.tsv
│   │   │   ├── dev.tsv
│   │   │   ├── test.tsv
│   │   │   ├── cvss_c_fr_en_v1.0.tar.gz
│   │   │   ├── fbank2unit/ # 用于 StreamSpeech 训练
│   │   │   │   ├── config_gcmvn.yaml
│   │   │   │   ├── config_mtl_asr_st_ctcst.yaml
│   │   │   │   ├── train.tsv
│   │   │   │   ├── dev.tsv
│   │   │   │   ├── test.tsv
│   │   │   │   ├── train.src
│   │   │   │   ├── dev.src
│   │   │   │   ├── test.src
│   │   │   │   ├── train.txt
│   │   │   │   ├── dev.txt
│   │   │   │   ├── test.txt
│   │   │   │   ├── train.unit
│   │   │   │   ├── dev.unit
│   │   │   │   └── test.unit
│   │   │   ├── fbank2text/ # 用于 S2TT 训练，但不涉及 StreamSpeech
│   │   │   │   ├── config_gcmvn.yaml
│   │   │   │   ├── train.tsv
│   │   │   │   ├── dev.tsv
│   │   │   │   ├── test.tsv
│   │   │   │   ├── spm_unigram_fr.model
│   │   │   │   ├── spm_unigram_fr.txt
│   │   │   │   └── spm_unigram_fr.vocab
│   │   │   ├── src_unigram6000/ # 用于 StreamSpeech 的多任务学习
│   │   │   │   ├── train.tsv
│   │   │   │   ├── dev.tsv
│   │   │   │   ├── test.tsv
│   │   │   │   ├── spm_unigram_fr.model
│   │   │   │   ├── spm_unigram_fr.txt
│   │   │   │   └── spm_unigram_fr.vocab
│   │   │   ├── tgt_unigram6000/ # 用于 StreamSpeech 的多任务学习
│   │   │   │   ├── train.tsv
│   │   │   │   ├── dev.tsv
│   │   │   │   ├── test.tsv
│   │   │   │   ├── spm_unigram_fr.model
│   │   │   │   ├── spm_unigram_fr.txt
│   │   │   │   └── spm_unigram_fr.vocab
│   │   │   ├── simuleval/ # 用于 StreamSpeech 的 SimulEval
│   │   │   │   ├── train/
│   │   │   │   │   ├── wav_list.txt
│   │   │   │   │   └── target.txt
│   │   │   │   ├── dev/
│   │   │   │   │   ├── wav_list.txt
│   │   │   │   │   └── target.txt
│   │   │   │   ├── test/
│   │   │   │   │   ├── wav_list.txt
│   │   │   │   │   └── target.txt
│   │   ├── de-en/
│   │   │   └── ...
│   │   ├── es-en/
│   │   │   └── ...
└──...
```

---

### 训练文件示例

训练的 `train.tsv` 文件（路径为 `/XXX/cvss/cvss-c/fr-en/fbank2unit/train.tsv`，以及相应的 `dev.tsv` 和 `test.tsv` 文件）应如下所示：

```tsv
id	src_audio	src_n_frames	src_text	tgt_text	tgt_audio	tgt_n_frames
common_voice_fr_17732749	/XXX/cvss/cvss-c/fr-en/src_fbank80.zip:17614448698:126208	394	Madame la baronne Pfeffers.	madam pfeffers the baroness	63 991 162 73 338 359 761 430 901 921 549 413 366 896 627 915 143 390 479 330 776 576 384 879 70 958 66 776 663 198 711 124 884 393 946 734 870 290 978 484 249 466 663 179 961 931 428 377 32 835 67 297 265 675 755 237 193 415 772	59
common_voice_fr_17732750	/XXX/cvss/cvss-c/fr-en/src_fbank80.zip:18841732828:226048	706	Vous savez aussi bien que moi que de nombreuses molécules innovantes ont malheureusement déçu.	you know as well as i do that many new molecules have unfortunately been disappointing	63 644 553 258 436 139 340 575 116 281 62 783 803 791 563 52 483 366 873 641 124 337 243 935 101 741 803 693 521 453 366 641 124 362 530 733 664 196 721 250 549 139 340 846 726 603 857 662 459 173 945 29 609 710 892 73 889 172 871 877 384 120 179 207 950 974 86 116 372 139 340 498 324 338 359 655 764 259 453 366 998 319 501 445 137 74 205 521 711 510 337 152 784 429 558 167 650 816 915 143 38 479 330 435 592 103 934 477 59 179 961 931 428 366 901 29 518 56 321 948 86 290 943 488 620 352 915 721 250 333 432 882 924 586 362 734 870 251 0 41 740 908 211 81 664 274 398 53 455 309 584 415	152
...
```

---

### SimulEval 的测试文件

测试文件的格式如下：

1. `/XXX/cvss/cvss-c/fr-en/simuleval/test/wav_list.txt`：

```txt
/XXX/covost2/fr/clips/common_voice_fr_17299399.mp3
/XXX/covost2/fr/clips/common_voice_fr_17299400.mp3
/XXX/covost2/fr/clips/common_voice_fr_17299401.mp3
/XXX/covost2/fr/clips/common_voice_fr_17300796.mp3
/XXX/covost2/fr/clips/common_voice_fr_17300797.mp3
...
```

2. `/XXX/cvss/cvss-c/fr-en/simuleval/test/target.txt`：

```txt
really interesting work will finally be undertaken on that topic
a profound reform is necessary
not that many
an inter ministerial committee on disability was held a few weeks back
i shall give the floor to mr alain ramadier to support the amendment number one hundred twenty eight
...
```

3. `/XXX/cvss/cvss-c/fr-en/simuleval/test/src.txt`：

```txt
un vrai travail intéressant va enfin être mené sur ce sujet
une réforme profonde est nécessaire
pas si nombreuses que ça
un comité interministériel du handicap s'est tenu il y a quelques semaines
la parole est à monsieur alain ramadier pour soutenir l'amendement numéro cent vingt-huit
...
```

---

通过上述步骤和配置，CVSS-C 数据预处理完成，可以用于 StreamSpeech 的训练和测试！