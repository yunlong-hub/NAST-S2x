lang=$1
CVSS_ROOT=/workspace/zyl/NAST-S2x/dataset/cvss/cvss-c
ROOT=/workspace/zyl/NAST-S2x

# 1.生成目标数据集：输入的 fbank2unit 特征数据将会根据设定的词汇表类型（unigram）和大小（6000）进行处理，转换成适合训练的文本格式。处理后的数据将会保存在指定的输出目录 tgt_unigram6000 下。
# 2.生成词汇表：脚本会根据 unigram 类型和词汇表大小（6000）生成一个包含 6000 个最常用单词的词汇表，作为目标文本数据的词汇表。这些词汇会用于后续的训练过程。

PYTHONPATH=$ROOT/fairseq python $ROOT/preprocess_scripts/prep_cvss_c_multitask_data.py \
    --data-dir $CVSS_ROOT/${lang}-en/fbank2unit \
    --output-dir $CVSS_ROOT/${lang}-en/tgt_unigram6000 \
    --lang $lang \
    --vocab-type unigram --vocab-size 6000