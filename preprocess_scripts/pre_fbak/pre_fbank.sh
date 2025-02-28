covost2_data_root=/data04/Sxd_Grp/SxdStu96/zyl/dataset/cv
cvssc_data_root=/data04/Sxd_Grp/SxdStu96/zyl/dataset/cvss-c
output_root=/data04/Sxd_Grp/SxdStu96/zyl/dataset/cvss-c/fr-en

# python /data/yunlong/NAST-S2x/preprocessing/prep_fbank.py \
FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

# PYTHONPATH=$PYTHONPATH:/data04/Sxd_Grp/SxdStu96/zyl/NAST-S2x/fairseq/examples 
python /data04/Sxd_Grp/SxdStu96/zyl/NAST-S2x/preprocessing/prep_fbank.py \
    --covost-data-root $covost2_data_root \
    --cvss-data-root $cvssc_data_root \
    --output-root  $output_root \
    --cmvn-type global



