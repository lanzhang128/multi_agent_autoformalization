import os
import json
from .abstract import BaseDataset


class ProofNet(BaseDataset):
    description = 'Class for ProofNet dataset.'

    def __init__(self,
                 name: str = 'ProofNet',
                 split: str = 'test'):
        self.split = split
        super().__init__(name)

    def _fill_metadata(self):
        with open(os.path.join(self.metadata_dir, f'proofnet_{self.split}.json'), 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
