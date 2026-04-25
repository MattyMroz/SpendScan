from __future__ import annotations

from spendscan.ocr.qianfan import MMPROJ_FILENAME, QIANFAN_HF_REPO, qianfan_download_url, required_qianfan_files


def test_qianfan_download_url_uses_reza2kn_hugging_face_repo() -> None:
    url = qianfan_download_url("qianfan-ocr-q4-k-m.gguf")

    assert QIANFAN_HF_REPO == "Reza2kn/Qianfan-OCR-GGUF"
    assert url == "https://huggingface.co/Reza2kn/Qianfan-OCR-GGUF/resolve/main/qianfan-ocr-q4-k-m.gguf"


def test_required_qianfan_files_include_model_and_mmproj() -> None:
    files = required_qianfan_files("q4_k_m")

    assert files == ("qianfan-ocr-q4-k-m.gguf", MMPROJ_FILENAME)
