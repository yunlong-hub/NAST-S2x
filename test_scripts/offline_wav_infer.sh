CVSS_ROOT=/nas/yunlong/dataset/cvss/cvss-c/fr-en
IN_ROOT=/workspace/zyl/NAST-S2x/test_out/units  #This is the path of the output of scripts ``offline_s2u_infer.sh``
OUT_ROOT=/workspace/zyl/NAST-S2x/test_out/wav

VOCODER_CKPT=${CVSS_ROOT}/vocoder/mhubert_lyr11_km1000_en/g_00500000
VOCODER_CFG=${CVSS_ROOT}/vocoder/mhubert_lyr11_km1000_en/config.json

grep "^Unit\-" ${IN_ROOT} | \
  sed 's/^Unit-//ig' | sort -nk1 | cut -f3 \
  > ${IN_ROOT}.sort


# 加载examples文件
FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

python fairseq/examples/speech_to_speech/generate_waveform_from_code.py \
  --in-code-file ${IN_ROOT}.sort \
  --vocoder ${VOCODER_CKPT} --vocoder-cfg ${VOCODER_CFG} \
  --results-path ${OUT_ROOT} --dur-prediction