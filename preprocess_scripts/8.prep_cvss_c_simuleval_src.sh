lang=$1

CVSS_ROOT=/workspace/zyl/NAST-S2x/dataset/cvss/cvss-c
ROOT=/workspace/zyl/NAST-S2x

for split in train dev test
do
    PYTHONPATH=$ROOT/fairseq python $ROOT/preprocess_scripts/extract_simuleval_src.py \
        --input-tsv $CVSS_ROOT/${lang}-en/fbank2unit/$split.tsv \
        --wav-list $CVSS_ROOT/${lang}-en/simuleval/$split/wav_list.txt \
        --output-src $CVSS_ROOT/${lang}-en/simuleval/$split/src.txt
done
