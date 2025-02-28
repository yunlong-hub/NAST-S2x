covost2_data_root=/data/yunlong/dataset/cv
cvssc_data_root=/data/yunlong/dataset/cvss
output_root=/data/yunlong/dataset/cvss/fr-en

# python /data/yunlong/NAST-S2x/preprocessing/prep_fbank.py \

PYTHONPATH=$PYTHONPATH:/data/yunlong/NAST-S2x/fairseq python /data/yunlong/NAST-S2x/preprocessing/prep_fbank.py \
    --covost-data-root $covost2_data_root \
    --cvss-data-root $cvssc_data_root \
    --output-root  $output_root \
    --cmvn-type global



# FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
# export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR