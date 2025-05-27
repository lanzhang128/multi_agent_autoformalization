import os
import json
from .abstract import BaseDataset


class MiniF2F(BaseDataset):
    description = 'Class for miniF2F dataset.'

    def __init__(self,
                 name: str = 'MiniF2F',
                 split: str = 'test'):
        self.split = split
        super().__init__(name)

    def _fill_metadata(self):
        with open(os.path.join(self.metadata_dir, f'minif2f_{self.split}.json'), 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
