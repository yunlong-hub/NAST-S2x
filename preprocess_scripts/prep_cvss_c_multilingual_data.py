#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import argparse
import logging
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple

import pandas as pd
import torchaudio
import soundfile as sf  
# 设置默认后端为 FFmpeg（推荐）
torchaudio.set_audio_backend("soundfile")  # 或 "sox"

from torch import Tensor
from torch.utils.data import Dataset
from utils import download_url, extract_archive
from tqdm import tqdm
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)
import numpy as np

from fairseq.data.audio.audio_utils import convert_waveform
from examples.speech_synthesis.data_utils import extract_logmel_spectrogram
from examples.speech_to_speech.preprocessing.data_utils import (
    gen_config_yaml,
    load_units,
    process_units,
)
from examples.speech_to_text.data_utils import (
    create_zip,
    extract_fbank_features,
    get_zip_manifest,
    load_df_from_tsv,
    save_df_to_tsv,
    cal_gcmvn_stats,
)
from data_utils import gen_config_yaml as gen_config_yaml_gcmvn

log = logging.getLogger(__name__)


MANIFEST_COLUMNS = [
    "id",
    "src_audio",
    "src_n_frames",
    "src_text",
    "tgt_text",
    "tgt_audio",
    "tgt_n_frames",
]


class CoVoST(Dataset):
    """Create a Dataset for CoVoST (https://github.com/facebookresearch/covost).

    Args:
        root (str): root path to the dataset and generated manifests/features
        source_language (str): source (audio) language
        target_language (str, optional): target (text) language,
        None for no translation (default: None)
        version (int, optional): CoVoST version. (default: 2)
        download (bool, optional): Whether to download the dataset if it is not
        found at root path. (default: ``False``).
    """

    COVOST_URL_TEMPLATE = (
        "https://dl.fbaipublicfiles.com/covost/"
        "covost_v2.{src_lang}_{tgt_lang}.tsv.tar.gz"
    )

    VERSIONS = {2}
    SPLITS = ["train", "dev", "test"]
    # SPLITS = ["train"]

    XX_EN_LANGUAGES = {
        1: ["fr", "de", "nl", "ru", "es", "it", "tr", "fa", "sv-SE", "mn", "zh-CN"],
        2: [
            "fr",
            "de",
            "es",
            "ca",
            "it",
            "ru",
            "zh-CN",
            "pt",
            "fa",
            "et",
            "mn",
            "nl",
            "tr",
            "ar",
            "sv-SE",
            "lv",
            "sl",
            "ta",
            "ja",
            "id",
            "cy",
        ],
    }
    EN_XX_LANGUAGES = {
        1: [],
        2: [
            "de",
            "tr",
            "fa",
            "sv-SE",
            "mn",
            "zh-CN",
            "cy",
            "ca",
            "sl",
            "et",
            "id",
            "ar",
            "ta",
            "lv",
            "ja",
        ],
    }

    def __init__(
        self,
        root: str,
        split: str,
        source_language: str,
        target_language: Optional[str] = None,
        version: int = 2,
    ) -> None:
        assert version in self.VERSIONS and split in self.SPLITS
        assert source_language is not None
        self.no_translation = target_language is None
        if not self.no_translation:
            assert "en" in {source_language, target_language}
            if source_language == "en":
                assert target_language in self.EN_XX_LANGUAGES[version]
            else:
                assert source_language in self.XX_EN_LANGUAGES[version]
        else:
            # Hack here so that we can get "split" column from CoVoST TSV.
            # Note that we use CoVoST train split for ASR which is an extension
            # to Common Voice train split.
            target_language = "de" if source_language == "en" else "en"

        self.root: Path = Path(root)

        cv_tsv_path = self.root / "validated.tsv"
        assert cv_tsv_path.is_file()

        covost_url = self.COVOST_URL_TEMPLATE.format(
            src_lang=source_language, tgt_lang=target_language
        )
        covost_archive = self.root / Path(covost_url).name
        if not covost_archive.is_file():
            download_url(covost_url, self.root.as_posix(), hash_value=None)
        extract_archive(covost_archive.as_posix())

        cv_tsv = load_df_from_tsv(cv_tsv_path)
        covost_tsv = load_df_from_tsv(
            self.root / Path(covost_url).name.replace(".tar.gz", "")
        )
        df = pd.merge(
            left=cv_tsv[["path", "sentence", "client_id"]],
            right=covost_tsv[["path", "translation", "split"]],
            how="inner",
            on="path",
        )
        if split == "train":
            df = df[(df["split"] == split) | (df["split"] == f"{split}_covost")]
        else:
            df = df[df["split"] == split]
        data = df.to_dict(orient="index").items()
        data = [v for k, v in sorted(data, key=lambda x: x[0])]
        self.data = []
        print(f"正在检查cv-{split}集数据正常情况。")
        for e in tqdm(data):
            try:
                path = self.root / "clips" / e["path"]
                _ = torchaudio.info(path.as_posix())
                self.data.append(e)
            except RuntimeError:
                print(f"Failed to load: {path.as_posix()}")
                pass
            except Exception as ex:
                print(f"Error processing {e['path']}: {ex}")
                pass

    def __getitem__(
        self, n: int
    ) -> Tuple[Tensor, int, str, str, Optional[str], str, str]:
        """Load the n-th sample from the dataset.

        Args:
            n (int): The index of the sample to be loaded

        Returns:
            tuple: ``(waveform, sample_rate, sentence, translation, speaker_id,
            sample_id)``
        """
        data = self.data[n]
        path = self.root / "clips" / data["path"]
        waveform, sample_rate = torchaudio.load(path)
        sentence = data["sentence"]
        translation = None if self.no_translation else data["translation"]
        speaker_id = data["client_id"]
        _id = data["path"].replace(".mp3", "")
        return waveform, sample_rate, sentence, translation, speaker_id, _id

    def __len__(self) -> int:
        return len(self.data)


class CVSS_C(CoVoST):
    def __init__(
        self,
        cvss_root: str,
        covost_root: str,
        split: str,
        source_language: str,
        target_language: Optional[str] = None,
        version: int = 2,
    ) -> None:
        super().__init__(covost_root, split, source_language, target_language, version)

        self.cvss_root = cvss_root
        self.split = split
        with open(cvss_root / f"{split}.tsv", "r") as f:
            target_data = f.read().splitlines()
            target_data = [x.split("\t") for x in target_data]
            target_dict = {k: v for k, v in target_data}

        self.s2s_data = []
        for e in self.data:
            if e["path"] in target_dict:
                e["translation"] = target_dict[e["path"]]
                self.s2s_data.append(e)

    def __getitem__(
        self, n: int
    ) -> Tuple[Tensor, int, str, str, Optional[str], str, str]:
        """Load the n-th sample from the dataset.

        Args:
            n (int): The index of the sample to be loaded

        Returns:
            tuple: ``(waveform, sample_rate, sentence, translation, speaker_id,
            sample_id)``
        """
        data = self.s2s_data[n]
        src_path = self.root / "clips" / data["path"]
        src_waveform, src_sample_rate = torchaudio.load(src_path)
        tgt_path = self.cvss_root / self.split / f"{data['path']}.wav"
        tgt_waveform, tgt_sample_rate = torchaudio.load(tgt_path)
        sentence = data["sentence"]
        translation = data["translation"]
        speaker_id = data["client_id"]
        _id = data["path"].replace(".mp3", "")

        return (
            src_waveform,
            src_sample_rate,
            tgt_waveform,
            tgt_sample_rate,
            sentence,
            translation,
            speaker_id,
            _id,
        )

    def __len__(self) -> int:
        return len(self.s2s_data)


def process(args):
    output_root = Path(args.output_root)
    output_root.mkdir(exist_ok=True)
    src_type = "audio" if args.use_audio_input else "fbank"
    tgt_type = "spec" if args.target_type == "spec" else "unit"
    output_tsv_dir = output_root / f"{src_type}2{tgt_type}"
    output_tsv_dir.mkdir(exist_ok=True)

    source_root = output_root / ("src_flac" if args.use_audio_input else "src_fbank80")
    source_zip_path = output_root / f"{source_root.name}.zip"

    if args.src_lang == "all":
        src_lang_list = CoVoST.XX_EN_LANGUAGES[2]
    else:
        src_lang_list = [args.src_lang]

    if source_zip_path.exists():
        print(f"{source_zip_path} exists.")
    else:
        print("Extracting source audio/features...")
        source_root.mkdir(exist_ok=True)
        gcmvn_feature_list = []
        for src_lang in src_lang_list:
            covost_root = Path(args.covost_data_root) / src_lang
            cvss_root = Path(args.cvss_data_root) / f"{src_lang}-en"
            if not covost_root.is_dir():
                raise NotADirectoryError(f"{covost_root} does not exist")
            if not cvss_root.is_dir():
                raise NotADirectoryError(f"{cvss_root} does not exist")

            print(f"Extracting source audio/features for {src_lang}-en...")
            for split in CoVoST.SPLITS:
            # for split in [ "dev", "test"]:
                print(f"正在处理{split}集数据。")
                dataset = CVSS_C(cvss_root, covost_root, split, src_lang, "en")
                if args.use_audio_input:
                    for waveform, sample_rate, _, _, _, _, _, utt_id in tqdm(dataset):
                        src_sample_rate = 16_000
                        waveform, sample_rate = convert_waveform(
                            waveform,
                            sample_rate,
                            to_mono=True,
                            to_sample_rate=src_sample_rate,
                        )
                        sf.write(
                            (source_root / f"{utt_id}.flac").as_posix(),
                            waveform.T.numpy(),
                            sample_rate,
                        )
                else:
                    print(f"{split}集中有数据{len(dataset)}。")
                    for waveform, sample_rate, _, _, _, _, _, utt_id in tqdm(dataset):
                        src_sample_rate = 16_000
                        waveform, sample_rate = convert_waveform(
                            waveform,
                            sample_rate,
                            to_mono=True,
                            to_sample_rate=src_sample_rate,
                        )
                        features = extract_fbank_features(
                            waveform, sample_rate, source_root / f"{utt_id}.npy"
                        )
                        if split == "train" and args.cmvn_type == "global":
                            if len(gcmvn_feature_list) < args.gcmvn_max_num:
                                gcmvn_feature_list.append(features)
                            else:
                                break
                    
                    if split == "train" and args.cmvn_type == "global":
                        # Estimate and save cmv
                        stats = cal_gcmvn_stats(gcmvn_feature_list)
                        with open(output_root / "gcmvn.npz", "wb") as f:
                            np.savez(f, mean=stats["mean"], std=stats["std"])
                    
                    print(f"{split}集处理完成。")        
                    
        print("ZIPing source audios/features...")
        create_zip(source_root, source_zip_path)
        # shutil.rmtree(source_root)
    
    print("Fetching ZIP manifest...")
    src_audio_paths, src_audio_lengths = get_zip_manifest(
        source_zip_path,
        is_audio=args.use_audio_input,
    )

    if args.target_type == "spec":
        target_root = output_root / "tgt_logmelspec80"
        target_zip_path = output_root / f"{target_root.name}.zip"
        if target_zip_path.exists():
            print(f"{target_zip_path} exists.")
        else:
            print("Extracting target features...")
            target_root.mkdir(exist_ok=True)

            for src_lang in src_lang_list:
                covost_root = Path(args.covost_data_root) / src_lang
                cvss_root = Path(args.cvss_data_root) / f"{src_lang}-en"

                print(f"Extracting target audio/features for {src_lang}-en...")
                for split in CoVoST.SPLITS:
                    dataset = CVSS_C(cvss_root, covost_root, split, src_lang, "en")
                    for _, _, waveform, sample_rate, _, _, _, utt_id in tqdm(dataset):
                        waveform, sample_rate = convert_waveform(
                            waveform,
                            sample_rate,
                            normalize_volume=args.normalize_volume,
                            to_sample_rate=args.target_sample_rate,
                        )
                        extract_logmel_spectrogram(
                            waveform,
                            sample_rate,
                            target_root / f"{utt_id}.npy",
                            win_length=args.win_length,
                            hop_length=args.hop_length,
                            n_fft=args.n_fft,
                            n_mels=args.n_mels,
                            f_min=args.f_min,
                            f_max=args.f_max,
                        )

            print("ZIPing target features...")
            create_zip(target_root, target_zip_path)
            shutil.rmtree(target_root)

        tgt_audio_paths, tgt_audio_lengths = get_zip_manifest(target_zip_path)

        # Generate TSV manifest
        print("Generating manifest...")

        for split in CoVoST.SPLITS:
            manifest = {c: [] for c in MANIFEST_COLUMNS}
            for src_lang in src_lang_list:
                covost_root = Path(args.covost_data_root) / src_lang
                cvss_root = Path(args.cvss_data_root) / f"{src_lang}-en"
                dataset = CVSS_C(cvss_root, covost_root, split, src_lang, "en")
                for _, _, _, _, src_utt, tgt_utt, _, utt_id in tqdm(dataset):
                    manifest["id"].append(utt_id)
                    manifest["src_audio"].append(src_audio_paths[utt_id])
                    manifest["src_n_frames"].append(src_audio_lengths[utt_id])
                    manifest["src_text"].append(src_utt)
                    manifest["tgt_text"].append(tgt_utt)
                    manifest["tgt_audio"].append(tgt_audio_paths[utt_id])
                    manifest["tgt_n_frames"].append(tgt_audio_lengths[utt_id])

            df = pd.DataFrame.from_dict(manifest)
            save_df_to_tsv(df, output_tsv_dir / f"{split}.tsv")

        # Generate config YAML
        win_len_t = args.win_length / args.target_sample_rate
        hop_len_t = args.hop_length / args.target_sample_rate
        extra = {
            "features": {
                "type": "spectrogram+melscale+log",
                "sample_rate": args.target_sample_rate,
                "eps": 1e-5,
                "n_mels": args.n_mels,
                "n_fft": args.n_fft,
                "window_fn": "hann",
                "win_length": args.win_length,
                "hop_length": args.hop_length,
                "win_len_t": win_len_t,
                "hop_len_t": hop_len_t,
                "f_min": args.f_min,
                "f_max": args.f_max,
                "n_stft": args.n_fft // 2 + 1,
            }
        }
        if args.use_audio_input:
            extra["use_audio_input"] = True
            gen_config_yaml(
                output_tsv_dir,
                specaugment_policy=None,
                feature_transform=["utterance_cmvn", "delta_deltas"],
                extra=extra,
            )
        else:
            gen_config_yaml(
                output_tsv_dir,
                specaugment_policy="lb",
                feature_transform=["utterance_cmvn", "delta_deltas"],
                extra=extra,
            )
    else:
        # Generate TSV manifest
        print("Generating manifest...")
        for split in CoVoST.SPLITS:
            manifest = {c: [] for c in MANIFEST_COLUMNS}
            for src_lang in src_lang_list:
                covost_root = Path(args.covost_data_root) / src_lang
                cvss_root = Path(args.cvss_data_root) / f"{src_lang}-en"
                dataset = CVSS_C(cvss_root, covost_root, split, src_lang, "en")
                target_unit_data = load_units(cvss_root / f"{split}.{args.unit_type}")
                for _, _, _, _, src_utt, tgt_utt, _, utt_id in tqdm(dataset):
                    manifest["id"].append(utt_id)
                    manifest["src_audio"].append(src_audio_paths[utt_id])
                    manifest["src_n_frames"].append(src_audio_lengths[utt_id])
                    manifest["src_text"].append(src_utt)
                    manifest["tgt_text"].append(tgt_utt)
                    target_units = process_units(
                        target_unit_data[utt_id + ".mp3.wav"], args.reduce_unit
                    )
                    manifest["tgt_audio"].append(" ".join(target_units))
                    manifest["tgt_n_frames"].append(len(target_units))
            df = pd.DataFrame.from_dict(manifest)
            save_df_to_tsv(df, output_tsv_dir / f"{split}.tsv")

        # Generate config YAML
        if args.use_audio_input:
            gen_config_yaml(
                output_tsv_dir,
                specaugment_policy=None,
                feature_transform=["utterance_cmvn"],
                vocoder_type="code_hifigan",
                vocoder_checkpoint=args.vocoder_checkpoint,
                vocoder_cfg=args.vocoder_cfg,
                extra={"use_audio_input": True},
            )
        else:
            if args.cmvn_type == "global":
                gen_config_yaml_gcmvn(
                    output_tsv_dir,
                    yaml_filename="config_gcmvn.yaml",
                    specaugment_policy="lb",
                    cmvn_type=args.cmvn_type,
                    gcmvn_path=(
                        output_root / "gcmvn.npz"
                        if args.cmvn_type == "global"
                        else None
                    ),
                    vocoder_type="code_hifigan",
                    vocoder_checkpoint=args.vocoder_checkpoint,
                    vocoder_cfg=args.vocoder_cfg,
                )
            else:
                gen_config_yaml(
                    output_tsv_dir,
                    specaugment_policy="lb",
                    feature_transform=["utterance_cmvn"],
                    vocoder_type="code_hifigan",
                    vocoder_checkpoint=args.vocoder_checkpoint,
                    vocoder_cfg=args.vocoder_cfg,
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cvss-data-root",
        required=True,
        type=str,
        help="data root of cvss-c",
    )
    parser.add_argument(
        "--covost-data-root",
        required=True,
        type=str,
        help="data root of covost2",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=str,
        help="output root",
    )
    parser.add_argument("--use-audio-input", action="store_true")
    parser.add_argument(
        "--target-type",
        default="spec",
        choices=["unit", "spec"],
        help="type of target speech",
    )
    parser.add_argument(
        "--src-lang",
        default="all",
        choices=[
            "fr",
            "de",
            "es",
            "ca",
            "it",
            "ru",
            "zh-CN",
            "pt",
            "fa",
            "et",
            "mn",
            "nl",
            "tr",
            "ar",
            "sv-SE",
            "lv",
            "sl",
            "ta",
            "ja",
            "id",
            "cy",
            "all",
        ],
        help="filter source language",
    )
    parser.add_argument(
        "--cmvn-type",
        default="global",
        choices=["global", "utterance"],
        help="The type of cepstral mean and variance normalization",
    )
    parser.add_argument(
        "--gcmvn-max-num",
        default=9999999,
        type=int,
        help="Maximum number of sentences to use to estimate global mean and "
        "variance",
    )
    # s2spect args
    parser.add_argument("--win-length", type=int, default=1024)
    parser.add_argument("--hop-length", type=int, default=256)
    parser.add_argument("--n-fft", type=int, default=1024)
    parser.add_argument("--n-mels", type=int, default=80)
    parser.add_argument("--f-min", type=int, default=20)
    parser.add_argument("--f-max", type=int, default=8000)
    parser.add_argument("--target-sample-rate", type=int, default=22050)
    parser.add_argument("--normalize-volume", "-n", action="store_true")
    # s2ut args
    parser.add_argument(
        "--unit-type",
        default="km100",
        choices=["km100", "km1000", "sn", "bip"],
        help="type of target units; km: kmeans, sn: speaker normalization (Lee et al., 2022b), bip: biliteral perturbation (Huang et al., 2023).",
    )
    parser.add_argument(
        "--reduce-unit",
        action="store_true",
        help="reduce a target unit sequence to a unique unit sequence, i.e. '1 1 1 2 2' -> '1 2'",
    )
    parser.add_argument(
        "--vocoder-checkpoint", default=None, type=str, help="vocoder checkpoint"
    )
    parser.add_argument(
        "--vocoder-cfg", default=None, type=str, help="vocoder config file"
    )

    args = parser.parse_args()

    process(args)


if __name__ == "__main__":
    main()
