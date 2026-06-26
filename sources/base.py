from abc import ABC, abstractmethod

#development safety net, ensures all of my potential sources will need these two methods

class stream(ABC):   

    @abstractmethod
    def read(self):
        pass   


    @abstractmethod
    def close(self):
        pass

    @property
    def fps(self):
        pass

    @property
    def frame_sz(self):
        pass

