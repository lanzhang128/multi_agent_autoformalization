import os
from abc import ABC, abstractmethod


class DataSample:
    def __init__(self, dic):
        self.id = dic['id']
        self.source = dic['source']
        self.informal = dic['latex']
        self.isabelle = dic['isabelle'] if 'isabelle' in dic.keys() else None
        self.lean = dic['lean4'] if 'lean4' in dic.keys() else None

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'informal': self.informal,
            'isabelle': self.isabelle,
            'lean': self.lean
        }


class BaseDataset(ABC):
    description = 'Abstract class for datasets.'
    metadata_dir = os.path.join(os.path.dirname(__file__), 'metadata')

    def __init__(self,
                 name: str = 'BaseDataset'):
        self.name = name
        self.metadata = {}
        self.keys = []
        self.data = []
        self._fill_metadata()
        self._fill_data()

    def __getitem__(self, item):
        return self.data[item]

    @abstractmethod
    def _fill_metadata(self):
        pass

    def _fill_data(self):
        for key in self.metadata.keys():
            self.keys.append(key)
            self.data.append(DataSample(self.metadata[key]))
