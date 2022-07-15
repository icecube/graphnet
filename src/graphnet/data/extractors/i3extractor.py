from abc import ABC, abstractmethod
from typing import List

from graphnet.utilities.logging import LoggerMixin, get_logger

logger = get_logger()

try:
    from icecube import (
        icetray,
        dataio,
    )  # pyright: reportMissingImports=false
except ImportError:
    logger.warning("icecube package not available.")


class I3Extractor(ABC, LoggerMixin):
    """Extracts relevant information from physics frames."""

    def __init__(self, name):

        # Member variables
        self._i3_file = None
        self._gcd_file = None
        self._gcd_dict = None
        self._calibration = None
        self._name = name

    def set_files(self, i3_file, gcd_file):
        # @TODO: Is it necessary to set the `i3_file`? It is only used in one
        #        place in `I3TruthExtractor`, and there only in a way that might
        #        be solved another way.
        self._i3_file = i3_file
        self._gcd_file = gcd_file
        self._load_gcd_data()

    def _load_gcd_data(self):
        """Loads the geospatial information contained in the gcd-file."""
        gcd_file = dataio.I3File(self._gcd_file)
        g_frame = gcd_file.pop_frame(icetray.I3Frame.Geometry)
        c_frame = gcd_file.pop_frame(icetray.I3Frame.Calibration)
        self._gcd_dict = g_frame["I3Geometry"].omgeo
        self._calibration = c_frame["I3Calibration"]

    @abstractmethod
    def __call__(self, frame) -> dict:
        """Extracts relevant information from frame."""
        pass

    @property
    def name(self) -> str:
        return self._name


class I3ExtractorCollection(list):
    """Class to manage multiple I3Extractors."""

    def __init__(self, *extractors):
        # Check(s)
        for extractor in extractors:
            assert isinstance(extractor, I3Extractor)

        # Base class constructor
        super().__init__(extractors)

    def set_files(self, i3_file, gcd_file):
        for extractor in self:
            extractor.set_files(i3_file, gcd_file)

    def __call__(self, frame) -> List[dict]:
        return [extractor(frame) for extractor in self]
