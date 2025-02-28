lang=$1

CVSS_ROOT=/workspace/zyl/NAST-S2x/dataset/cvss/cvss-c
ROOT=/workspace/zyl/NAST-S2x

# 该脚本的主要作用是：
# 	•	从原始的 TSV 数据中提取文本（源文本或目标文本）。
# 	•	根据用户指定的词汇类型（字符、音素、unigram）生成 SentencePiece 词汇表，或者对文本进行音标化处理。
# 	•	将处理后的文本数据保存为新的 TSV 文件，供后续的训练使用。
# 总结：即构建ASR的数据形式，到src_unigram6000文件中



PYTHONPATH=$ROOT/fairseq python $ROOT/preprocess_scripts/prep_cvss_c_multitask_data.py \
    --data-dir $CVSS_ROOT/${lang}-en/fbank2unit \
    --output-dir $CVSS_ROOT/${lang}-en/src_unigram6000 \
    --lang $lang \
    --is-src-text \
    --vocab-type unigram --vocab-size 6000