import os.path
from functools import partial
from typing import List

import click
from huggingface_hub import hf_hub_download
from tqdm.auto import tqdm
from ultralytics import YOLO

from .onnx import export_yolo_to_onnx
from ..utils import GLOBAL_CONTEXT_SETTINGS
from ..utils import print_version as _origin_print_version

print_version = partial(_origin_print_version, 'zoo.web')


@click.group(context_settings={**GLOBAL_CONTEXT_SETTINGS})
@click.option('-v', '--version', is_flag=True,
              callback=print_version, expose_value=False, is_eager=True,
              help="Show version information.")
def cli():
    pass  # pragma: no cover


_KNOWN_CKPTS: List[str] = [
    'web_detect_best_m.pt',
    'web_detect_best_m_4x.pt',
    'web_detect_best_m_4x_150.pt',
    'web_detect_best_m_4x_600.pt',
]


@cli.command('export', help='Export all models as onnx.',
             context_settings={**GLOBAL_CONTEXT_SETTINGS})
@click.option('--output_dir', '-O', 'output_dir', type=click.Path(file_okay=False), required=True,
              help='Output directory of all models.', show_default=True)
def export(output_dir: str):
    for ckpt in tqdm(_KNOWN_CKPTS):
        yolo = YOLO(hf_hub_download('OpenDILabCommunity/webpage_element_detection', f'{ckpt}'))
        filebody, _ = os.path.splitext(ckpt)
        output_file = os.path.join(output_dir, f'{filebody}.onnx')
        export_yolo_to_onnx(yolo, output_file)


if __name__ == '__main__':
    cli()
