LANG=fr
DATA_ROOT=./dataset/cvss/cvss-c
DATA=$DATA_ROOT/${LANG}-en/fbank2unit
CHECKPOINT_DIR=./checkpoints/${LANG}-en/nmla_train
CKPT_PATH=${CHECKPOINT_DIR}/checkpoint_best.pt

CHUNK_SIZE=32  #This is an example, should be modified according to your model
OUT_ROOT=${CHECKPOINT_DIR}/test_out/units
NAST_DIR=./nast  #This is the path of our provided nast as a plugin to Fairseq
CONFIG_PATH=/workspace/yunlong/NAST-S2x/configs/nast/${LANG}-en

# 加载examples文件
FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

python nast/cli/generate_ctc_unit.py ${DATA} \
  --user-dir ${NAST_DIR} \
  --config-yaml ${CONFIG_PATH}/config_gcmvn.yaml --gen-subset test --task nat_speech_to_unit_ctc_modified --src-upsample-ratio 1 --unit-size 2 --hidden-upsample-ratio 6 --main-context ${CHUNK_SIZE} --right-context ${CHUNK_SIZE} \
  --path ${CKPT_PATH} \
  --iter-decode-max-iter 0 --iter-decode-eos-penalty 0 \
  --target-is-code --target-code-size 1000 \
  --batch-size 100 --beam 1 --scoring sacrebleu > ${OUT_ROOT} \
  --num-workers 10