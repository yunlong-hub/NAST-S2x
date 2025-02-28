# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import logging
import os
import tqdm
import random
import numpy as np

import joblib
from utils import (
    get_audio_files,
)
from hubert_feature_reader import HubertFeatureReader
from joblib import Parallel, delayed

def get_logger():
    log_format = "[%(asctime)s] [%(levelname)s]: %(message)s"
    logging.basicConfig(format=log_format, level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


def get_parser():
    parser = argparse.ArgumentParser(
        description="Quantize using K-means clustering over acoustic features."
    )
    parser.add_argument(
        "--feature_type",
        type=str,
        choices=["logmel", "hubert", "w2v2", "cpc"],
        default=None,
        required=True,
        help="Acoustic feature type",
    )
    parser.add_argument(
        "--acoustic_model_path", type=str, help="Pretrained acoustic model checkpoint"
    )
    parser.add_argument(
        "--layer",
        type=int,
        help="The layer of the pretrained model to extract features from",
        default=-1,
    )
    parser.add_argument(
        "--kmeans_model_path",
        type=str,
        required=True,
        help="K-means model file path to use for inference",
    )
    parser.add_argument(
        "--features_path",
        type=str,
        default=None,
        help="Features file path. You don't need to enter acoustic model details if you have dumped features",
    )
    parser.add_argument(
        "--manifest_path",
        type=str,
        default=None,
        help="Manifest file containing the root dir and file names",
    )
    parser.add_argument(
        "--out_quantized_file_path",
        required=True,
        type=str,
        help="File path of quantized output.",
    )
    parser.add_argument(
        "--extension", type=str, default=".flac", help="Features file path"
    )
    parser.add_argument(
        "--channel_id",
        choices=["1", "2"],
        help="The audio channel to extract the units in case of stereo file.",
        default=None,
    )
    parser.add_argument(
        "--hide-fname", action="store_true", help="Hide file names in the output file."
    )
    return parser


def get_feature_iterator(
    feature_type, checkpoint_path, layer, manifest_path, sample_pct, channel_id
):
    feature_reader_cls = HubertFeatureReader
    with open(manifest_path, "r") as fp:
        lines = fp.read().split("\n")
        root = lines.pop(0).strip()
        file_path_list = [
            os.path.join(root, line.split("\t")[0]) for line in lines if len(line) > 0
        ]
        if sample_pct < 1.0:
            file_path_list = random.sample(
                file_path_list, int(sample_pct * len(file_path_list))
            )
        num_files = len(file_path_list)
        reader = feature_reader_cls(checkpoint_path=checkpoint_path, layer=layer)

        def iterate():
            for file_path in file_path_list:
                feats = reader.get_feats(file_path, channel_id=channel_id)
                yield feats.cpu().numpy()

    return iterate, num_files


def process_file(i, feats, kmeans_models, fnames, args):
    # 选择模型的逻辑，例如根据文件索引选择模型
    model_index = i % len(kmeans_models)
    kmeans_model = kmeans_models[model_index]

    pred = kmeans_model.predict(feats)
    pred_str = " ".join(str(p) for p in pred)
    base_fname = os.path.basename(fnames[i]).rstrip(
        "." + args.extension.lstrip(".")
    )
    if args.channel_id is not None:
        base_fname = base_fname + f"-channel{args.channel_id}"
    if not args.hide_fname:
        return f"{base_fname}|{pred_str}\n"
    else:
        return f"{pred_str}\n"
    
    
def main(args, logger):
    # feature iterator
    generator, num_files = get_feature_iterator(
        feature_type=args.feature_type,
        checkpoint_path=args.acoustic_model_path,
        layer=args.layer,
        manifest_path=args.manifest_path,
        sample_pct=1.0,
        channel_id=int(args.channel_id) if args.channel_id else None,
    )
    iterator = generator()

    # 加载多个 K-means 模型
    kmeans_models = []
    for i in range(5):
        model_path = args.kmeans_model_path  # 假设所有模型路径相同
        logger.info(f"Loading K-means model from {model_path} ...")
        kmeans_model = joblib.load(open(model_path, "rb"))
        kmeans_model.verbose = False
        kmeans_models.append(kmeans_model)

    _, fnames, _ = get_audio_files(args.manifest_path)

    os.makedirs(os.path.dirname(args.out_quantized_file_path), exist_ok=True)
    print(f"Writing quantized predictions to {args.out_quantized_file_path}")

    # 使用 joblib 并行处理
    results = Parallel(n_jobs=5)(
        delayed(process_file)(i, feats, kmeans_models, fnames, args)
        for i, feats in tqdm.tqdm(enumerate(iterator), total=num_files)
    )

    with open(args.out_quantized_file_path, "w") as fout:
        for result in results:
            fout.write(result)


"""
这段代码主要实现了以下功能：
	1.	提取音频文件的特征（logmel、hubert 等）。
	2.	使用 K-means 聚类对提取的特征进行量化。
	3.	将量化的结果输出到文件中，便于后续使用。
"""
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    logger = get_logger()
    logger.info(args)
    main(args, logger)
