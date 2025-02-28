CVSS_ROOT=./dataset/cvss/cvss-c/fr-en/fbank2unit
CKPT_PATH=./model/Offline.pt  #This is the path to your checkpoint
CHUNK_SIZE=32  #This is an example, should be modified according to your model
OUT_ROOT=./test_out/units
NAST_DIR=./nast  #This is the path of our provided nast as a plugin to Fairseq


# 加载examples文件
FAIRSEQ_DIR=$(pip list -v | grep 'fairseq' | awk '{print $3}')
export PYTHONPATH=$PYTHONPATH:$FAIRSEQ_DIR

python nast/cli/generate_ctc_unit.py ${CVSS_ROOT} \
  --user-dir ${NAST_DIR} \
  --config-yaml config.yaml --gen-subset test --task nat_speech_to_unit_ctc_modified --src-upsample-ratio 1 --unit-size 2 --hidden-upsample-ratio 6 --main-context ${CHUNK_SIZE} --right-context ${CHUNK_SIZE} \
  --path ${CKPT_PATH} \
  --iter-decode-max-iter 0 --iter-decode-eos-penalty 0 \
  --target-is-code --target-code-size 1000 \
  --batch-size 100 --beam 1 --scoring sacrebleu > ${OUT_ROOT} \
  --num-workers 10