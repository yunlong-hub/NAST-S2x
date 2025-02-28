lang=$1

CVSS_ROOT=/workspace/zyl/NAST-S2x/dataset/cvss/cvss-c
COVOST2_ROOT=/workspace/zyl/NAST-S2x/dataset/cv
ROOT=/workspace/zyl/NAST-S2x

PYTHONPATH=$ROOT/fairseq python $ROOT/preprocess_scripts/extract_simuleval_data.py \
    --cvss-dir $CVSS_ROOT/${lang}-en \
    --covost2-dir $COVOST2_ROOT/${lang} \
    --out-dir $CVSS_ROOT/${lang}-en/simuleval 