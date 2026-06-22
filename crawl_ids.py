import os

from waifuc.action.tagging import DanbooruMetaProcessAction
from waifuc.export.base import BaseExporter
from waifuc.source import DanbooruSource

class DoNothingExporter(BaseExporter):
    def __init__(self):
        BaseExporter.__init__(self, ignore_error_when_export=True)
        self._tag_file = None
        self._tag_writer = None

    def pre_export(self):
         self._tag_file = None

    def export_item(self, something):
         self._tag_file = None

    def post_export(self):
         self._tag_file = None

    def reset(self):
         self._tag_file = None

def process_file_ids(file_path, output_dir):
    try:
        with open(file_path, 'r') as f:
            file_ids = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    chunk_size = 100
    for i in range(0, len(file_ids), chunk_size):
        batch = file_ids[i:i + chunk_size]
        id_string = ",".join(batch)
        
        print(f"Processing batch {i // chunk_size + 1}: {len(batch)} items...")
        s = DanbooruSource([f"id:{id_string}"], 0, True)
        
        s.attach(
            DanbooruMetaProcessAction([], output_dir),
        ).export(
            DoNothingExporter()
        )

if __name__ == '__main__':
    input_file = './0_missing_meta_list.txt'
    output_dir = '/data/0_danbooru_meta'
    
    os.makedirs(output_dir, exist_ok=True)
    
    process_file_ids(input_file, output_dir)
