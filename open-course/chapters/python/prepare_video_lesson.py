"""Acquire fixed, public MOT17 teaching material and a pinned OpenCV Zoo model.

Data/video and derivatives: CC BY-NC-SA 3.0, not the course code license.
OpenCV Zoo YOLOX wrapper/weights: Apache-2.0, copyright Megvii/OpenCV contributors.
No ground-truth video with painted boxes is used as detector input.
"""
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'chapters/data/video'
VENDOR = ROOT/'chapters/python/vendor/yolox'
COMMIT = '47534e27c9851bb1128ccc0102f1145e27f23f98'
RAW = f'https://raw.githubusercontent.com/opencv/opencv_zoo/{COMMIT}/models/object_detection_yolox/'
MODEL_SHA = 'c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063'
VIDEO_SHA = 'ab0d2fc03bce5e112abe9a173de7a2d70b39875c0af3eca49d6160c6e317e495'
LABELS_SHA = '0aa79322e91583369f42f17c4d79a0b145380d8732487bba59272048dc82b2b9'


def fetch(url, path, expected=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print('Downloading', url, flush=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            blob = response.read()
        path.write_bytes(blob)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and sha != expected:
        raise ValueError(f'Hash mismatch for {path}; remove the incomplete download and retry')
    return {'url':url,'sha256':sha,'bytes':path.stat().st_size}


def main():
    manifest = {}
    manifest['video'] = fetch('https://motchallenge.net/sequenceVideos/MOT17-04-FRCNN-raw.mp4',DATA/'mot17-04-raw.mp4',VIDEO_SHA)
    archive = ROOT/'outputs/video-downloads/MOT17Labels.zip'
    manifest['annotation_archive'] = fetch('https://motchallenge.net/data/MOT17Labels.zip',archive,LABELS_SHA)
    with zipfile.ZipFile(archive) as z:
        for name,target in [('gt/gt.txt','mot17-04-gt.txt'),('seqinfo.ini','mot17-04-seqinfo.ini')]:
            blob = z.read('train/MOT17-04-FRCNN/'+name)
            (DATA/target).write_bytes(blob)
            manifest[target] = {'archive_member':'train/MOT17-04-FRCNN/'+name,'sha256':hashlib.sha256(blob).hexdigest()}
    for name in ['yolox.py','LICENSE']:
        manifest[name] = fetch(RAW+name,VENDOR/name)
    wrapper = VENDOR/'yolox.py'
    code = wrapper.read_text(encoding='utf-8')
    if 'self.net = cv2.dnn.readNet(modelPath)' in code:
        code = code.replace('import cv2', 'import cv2\nfrom pathlib import Path\n# Course modification: load model bytes to support Unicode paths on Windows.', 1)
        code = code.replace('self.net = cv2.dnn.readNet(modelPath)', 'self.net = cv2.dnn.readNetFromONNX(np.frombuffer(Path(modelPath).read_bytes(), dtype=np.uint8))', 1)
        wrapper.write_text(code,encoding='utf-8')
    manifest['yolox.py']['course_modification'] = 'ONNX byte buffer loading for Windows Unicode paths; inference unchanged'
    manifest['yolox.py']['sha256'] = hashlib.sha256(wrapper.read_bytes()).hexdigest()
    manifest['yolox.py']['bytes'] = wrapper.stat().st_size
    model_url = f'https://media.githubusercontent.com/media/opencv/opencv_zoo/{COMMIT}/models/object_detection_yolox/object_detection_yolox_2022nov.onnx'
    manifest['model'] = fetch(model_url,ROOT/'outputs/video-models/yolox.onnx',MODEL_SHA)
    manifest.update(dataset='MOT17-04',dataset_license='CC BY-NC-SA 3.0',model_license='Apache-2.0',model_commit=COMMIT,
                    dataset_source='https://motchallenge.net/data/MOT17/',
                    license_documentation='https://trackers.roboflow.com/develop/learn/download/',
                    citation='Milan, Leal-Taixe, Reid, Roth, Schindler. MOT16: A Benchmark for Multi-Object Tracking, 2016; Dendorfer et al. MOTChallenge, IJCV 2021.')
    (DATA/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Fixed video, annotations, source code and model acquired; detector model is not bundled in the teaching ZIP.')


if __name__ == '__main__':
    main()
