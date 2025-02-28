CVSS_ROOT=/data04/Sxd_Grp/SxdStu96/zyl/dataset/cvss/cvss-c/fr-en

VOCODER_CKPT=${CVSS_ROOT}/vocoder/mhubert_lyr11_km1000_en/g_00500000
VOCODER_CFG=${CVSS_ROOT}/vocoder/mhubert_lyr11_km1000_en/config.json

CHUNK_SIZE=32  #This is an example, should be modified according to your model
CKPT_PATH=/data04/Sxd_Grp/SxdStu96/zyl/NAST-S2x/model/chunk_320ms.pt #This is the path to your checkpoint
OUT_ROOT=/data04/Sxd_Grp/SxdStu96/zyl/NAST-S2x/test_out/stream
NAST_DIR=/data04/Sxd_Grp/SxdStu96/zyl/NAST-S2x/nast  #This is the path of our provided nast as a plugin to Fairseq

SEGMENT_SIZE=${CHUNK_SIZE}0

# 加载examples文件
FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

simuleval \
    --data-bin ${CVSS_ROOT} \
    --source ${CVSS_ROOT}/test.wav_list --target ${CVSS_ROOT}/test.en \
    --model-path ${CKPT_PATH} \
    --config-yaml config.yaml --target-speech-lang en \
    --agent ${NAST_DIR}/agents/nast_speech2speech_agent_s2s.py \
    --wait-until 0 --main-context ${CHUNK_SIZE} --right-context ${CHUNK_SIZE} --sample-rate 48000 \
    --output ${OUT_ROOT} \
    --source-segment-size ${SEGMENT_SIZE} \
    --vocoder ${VOCODER_CKPT} --vocoder-cfg ${VOCODER_CFG} --dur-prediction \
    --quality-metrics ASR_BLEU  --latency-metrics AL LAAL AP DAL ATD NumChunks RTF StartOffset EndOffset \
    --device gpu --continue-unfinished
