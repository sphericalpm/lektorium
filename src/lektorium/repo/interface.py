import abc


class Repo:
    @property
    @abc.abstractmethod
    def sites(self):
        pass
