import pytest

from asr import ModelError, load_model, missing_model_files


def make_model(root, graph_files):
    for name in ["am/final.mdl", "conf/mfcc.conf", "conf/model.conf", *graph_files]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
    return root


def test_missing_directory(tmp_path):
    assert missing_model_files(tmp_path / "nope") == [str(tmp_path / "nope")]


def test_incomplete_model_like_the_old_committed_one(tmp_path):
    root = make_model(tmp_path, ["graph/disambig_tid.int"])
    assert missing_model_files(root) == ["graph/HCLG.fst or graph/HCLr.fst + graph/Gr.fst"]
    with pytest.raises(ModelError, match="download_model.sh"):
        load_model(root)


@pytest.mark.parametrize("graph", [["graph/HCLG.fst"], ["graph/HCLr.fst", "graph/Gr.fst"]])
def test_complete_layouts(tmp_path, graph):
    assert missing_model_files(make_model(tmp_path, graph)) == []
