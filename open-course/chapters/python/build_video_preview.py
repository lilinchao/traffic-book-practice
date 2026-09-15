"""Make a browser-compatible H.264 preview without changing frame order or size."""
import hashlib
import json
import subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'chapters/data/video'
source=DATA/'mot17-04-raw.mp4'
target=DATA/'mot17-04-web.mp4'
command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-i',str(source),'-an',
         '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
subprocess.run(command,check=True)
manifest={'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
          'frames':1050,'fps':30,'width':960,'height':540,'license':'CC BY-NC-SA 3.0',
          'modification':'MPEG-4 Part 2 to H.264 CRF18 for browser playback, no crop, resize, trim or overlays. Detection uses the original source file.',
          'ffmpeg':subprocess.check_output([imageio_ffmpeg.get_ffmpeg_exe(),'-version'],text=True).splitlines()[0]}
(DATA/'preview.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(target.name,target.stat().st_size,'bytes')
