# bash preprocess.sh 

lang=fr

ROOT=/workspace/zyl/NAST-S2x
PREPROCESS_ROOT=$ROOT/preprocess_scripts

export CUDA_VISIBLE_DEVICES=0,1

stage=1 # start from 0 if you need to start from data preparation
stop_stage=8


FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

# You should change the following two parameters for multiple machine training,
# see https://pytorch.org/docs/stable/elastic/run.html


# 使用预训练的模型（如 HuBERT）对音频数据进行特征提取和量化（quantization），并将其用于 K-means 聚类
# 并使用KM_S模型对目标语音数据，利用预训练模型进行units化.
# [split] .tsv 存储id,text. txt存储id，time .km1000存储id,unit
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
    bash $PREPROCESS_ROOT/1.learn_KM_clustering_model.sh $lang
    echo 'finish 1.learn_KM_clustering_model.sh'
fi

# 正式构建S2ST的数据形式。如果目标是unit，不是
# 该阶段用于准备多语言数据集，可能是用于训练多语种的模型。
# 在其中，加载cv、covost、cvss，并对生成tsv文件，用以后续的表示.
if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then
    bash $PREPROCESS_ROOT/2.prep_cvss_c_multilingual_data.sh $lang
    echo 'finish 2.prep_cvss_c_multilingual_data.sh'
fi

# 构建S2TT的数据形式，置于tgt_unigram6000中，生成目标语音的spm表示。

if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
    bash $PREPROCESS_ROOT/3.prep_cvss_c_multitask_data.sh $lang
    echo 'finish 3.prep_cvss_c_multitask_data.sh'
fi

# 在fbank2unit目录下，将tsv中的src_text放到src文件下，将tgt_text放到txt，将tgt_audio放到unit中
if [ ${stage} -le 5 ] && [ ${stop_stage} -ge 5 ]; then
    echo 'start running 5.prep_cvss_c_ref_txt.sh'
    bash $PREPROCESS_ROOT/5.prep_cvss_c_ref_txt.sh $lang
    echo 'finish 5.prep_cvss_c_ref_txt.sh'
fi

# 用于提取用于模拟评估的数据。
# 从CVSS 数据集的 .tsv 文件中读取数据，在指定的输出目录中生成以下文件：	wav_list.txt：包含音频文件路径的列表。target.txt：包含目标文本的列表。
if [ ${stage} -le 6 ] && [ ${stop_stage} -ge 6 ]; then
    bash $PREPROCESS_ROOT/6.extract_simuleval_data.sh $lang
    echo 'finish 6.extract_simuleval_data.sh'
fi

#构建ASR的数据形式，到src_unigram6000目录下。
if [ ${stage} -le 7 ] && [ ${stop_stage} -ge 7 ]; then
    bash $PREPROCESS_ROOT/7.prep_cvss_c_multitask_asr_data.sh $lang
    echo 'finish 7.prep_cvss_c_multitask_asr_data.sh'
fi




# 继续处理上面的模拟评估数据
# 将给定语言，各集合中的数据列表wav_list，从tsv中获取对应A.源文本（src_text）B.目标音频（tgt_audio）的unit表示，写到scr、units中
if [ ${stage} -le 8 ] && [ ${stop_stage} -ge 8 ]; then
    bash $PREPROCESS_ROOT/8.prep_cvss_c_simuleval_unit.sh $lang
    bash $PREPROCESS_ROOT/8.prep_cvss_c_simuleval_src.sh $lang
    echo 'finish 8.prep_cvss_c_simuleval_unit.sh, 8.prep_cvss_c_simuleval_src.sh'
fi

# # only for s2tt training on CVSS-C
# bash $PREPROCESS_ROOT/9.prep_cvss_c_s2st_mtl_data.sh  $lang
# echo 'finish 9.prep_cvss_c_s2st_mtl_data.sh'