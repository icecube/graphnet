import numpy as np
import matplotlib.path as mpath
from typing import Tuple

from graphnet.data.extractors.i3extractor import I3Extractor
from graphnet.data.extractors.utilities import (
    frame_is_montecarlo,
    frame_is_noise,
)
from graphnet.utilities.logging import get_logger

logger = get_logger()

try:
    from icecube import (
        dataclasses,
        icetray,
        phys_services,
    )  # pyright: reportMissingImports=false
except ImportError:
    logger.info("icecube package not available.")


class I3TruthExtractor(I3Extractor):
    def __init__(self, name="truth", borders=None):
        super().__init__(name)
        if borders is None:
            border_xy = np.array(
                [
                    (-256.1400146484375, -521.0800170898438),
                    (-132.8000030517578, -501.45001220703125),
                    (-9.13000011444092, -481.739990234375),
                    (114.38999938964844, -461.989990234375),
                    (237.77999877929688, -442.4200134277344),
                    (361.0, -422.8299865722656),
                    (405.8299865722656, -306.3800048828125),
                    (443.6000061035156, -194.16000366210938),
                    (500.42999267578125, -58.45000076293945),
                    (544.0700073242188, 55.88999938964844),
                    (576.3699951171875, 170.9199981689453),
                    (505.2699890136719, 257.8800048828125),
                    (429.760009765625, 351.0199890136719),
                    (338.44000244140625, 463.7200012207031),
                    (224.5800018310547, 432.3500061035156),
                    (101.04000091552734, 412.7900085449219),
                    (22.11000061035156, 509.5),
                    (-101.05999755859375, 490.2200012207031),
                    (-224.08999633789062, 470.8599853515625),
                    (-347.8800048828125, 451.5199890136719),
                    (-392.3800048828125, 334.239990234375),
                    (-437.0400085449219, 217.8000030517578),
                    (-481.6000061035156, 101.38999938964844),
                    (-526.6300048828125, -15.60000038146973),
                    (-570.9000244140625, -125.13999938964844),
                    (-492.42999267578125, -230.16000366210938),
                    (-413.4599914550781, -327.2699890136719),
                    (-334.79998779296875, -424.5),
                ]
            )
            border_z = np.array([-512.82, 524.56])
            self._borders = [border_xy, border_z]
        else:
            self._borders = borders

    def __call__(self, frame, padding_value=-1) -> dict:
        """Extracts truth features."""
        is_mc = frame_is_montecarlo(frame)
        is_noise = frame_is_noise(frame)
        sim_type = self._find_data_type(is_mc, self._i3_file)

        output = {
            "energy": padding_value,
            "position_x": padding_value,
            "position_y": padding_value,
            "position_z": padding_value,
            "azimuth": padding_value,
            "zenith": padding_value,
            "pid": padding_value,
            "event_time": frame["I3EventHeader"].start_time.utc_daq_time,
            "sim_type": sim_type,
            "interaction_type": padding_value,
            "elasticity": padding_value,
            "RunID": frame["I3EventHeader"].run_id,
            "SubrunID": frame["I3EventHeader"].sub_run_id,
            "EventID": frame["I3EventHeader"].event_id,
            "SubEventID": frame["I3EventHeader"].sub_event_id,
            "dbang_decay_length": padding_value,
            "track_length": padding_value,
            "stopped_muon": padding_value,
            "energy_track": padding_value,
            "inelasticity": padding_value,
            "DeepCoreFilter_13": padding_value,
            "CascadeFilter_13": padding_value,
            "MuonFilter_13": padding_value,
            "OnlineL2Filter_17": padding_value,
            "L3_oscNext_bool": padding_value,
            "L4_oscNext_bool": padding_value,
            "L5_oscNext_bool": padding_value,
            "L6_oscNext_bool": padding_value,
            "L7_oscNext_bool": padding_value,
        }

        # Only InIceSplit P frames contain ML appropriate I3RecoPulseSeriesMap etc.
        # At low levels i3files contain several other P frame splits (e.g NullSplit),
        # we remove those here.
        if frame["I3EventHeader"].sub_event_stream != "InIceSplit":
            return output

        if "FilterMask" in frame:
            if "DeepCoreFilter_13" in frame["FilterMask"]:
                output["DeepCoreFilter_13"] = int(
                    frame["FilterMask"]["DeepCoreFilter_13"]
                )
            if "CascadeFilter_13" in frame["FilterMask"]:
                output["CascadeFilter_13"] = int(
                    frame["FilterMask"]["CascadeFilter_13"]
                )
            if "MuonFilter_13" in frame["FilterMask"]:
                output["MuonFilter_13"] = int(
                    frame["FilterMask"]["MuonFilter_13"]
                )
            if "OnlineL2Filter_17" in frame["FilterMask"]:
                output["OnlineL2Filter_17"] = int(
                    frame["FilterMask"]["OnlineL2Filter_17"]
                )

        elif "DeepCoreFilter_13" in frame:
            output["DeepCoreFilter_13"] = int(bool(frame["DeepCoreFilter_13"]))

        if "L3_oscNext_bool" in frame:
            output["L3_oscNext_bool"] = int(frame["L3_oscNext_bool"])

        if "L4_oscNext_bool" in frame:
            output["L4_oscNext_bool"] = int(frame["L4_oscNext_bool"])

        if "L5_oscNext_bool" in frame:
            output["L5_oscNext_bool"] = int(frame["L5_oscNext_bool"])

        if "L6_oscNext_bool" in frame:
            output["L6_oscNext_bool"] = int(frame["L6_oscNext_bool"])

        if "L7_oscNext_bool" in frame:
            output["L7_oscNext_bool"] = int(frame["L7_oscNext_bool"])

        if is_mc and (not is_noise):
            (
                MCInIcePrimary,
                interaction_type,
                elasticity,
            ) = self._get_primary_particle_interaction_type_and_elasticity(
                frame, sim_type
            )
            (
                energy_track,
                inelasticity,
            ) = self._get_primary_track_energy_and_inelasticity(frame)
            output.update(
                {
                    "energy": MCInIcePrimary.energy,
                    "position_x": MCInIcePrimary.pos.x,
                    "position_y": MCInIcePrimary.pos.y,
                    "position_z": MCInIcePrimary.pos.z,
                    "azimuth": MCInIcePrimary.dir.azimuth,
                    "zenith": MCInIcePrimary.dir.zenith,
                    "pid": MCInIcePrimary.pdg_encoding,
                    "interaction_type": interaction_type,
                    "elasticity": elasticity,
                    "dbang_decay_length": self._extract_dbang_decay_length(
                        frame, padding_value
                    ),
                    "energy_track": energy_track,
                    "inelasticity": inelasticity,
                }
            )
            if abs(output["pid"]) == 13:
                output.update(
                    {
                        "track_length": MCInIcePrimary.length,
                    }
                )
                muon_final = self._muon_stopped(output, self._borders)
                output.update(
                    {
                        "position_x": muon_final[
                            "x"
                        ],  # position_xyz has no meaning for muons. These will now be updated to muon final position, given track length/azimuth/zenith
                        "position_y": muon_final["y"],
                        "position_z": muon_final["z"],
                        "stopped_muon": muon_final["stopped"],
                    }
                )

        return output

    def _extract_dbang_decay_length(self, frame, padding_value):
        mctree = frame["I3MCTree"]
        try:
            p_true = mctree.primaries[0]
            p_daughters = mctree.get_daughters(p_true)
            if len(p_daughters) == 2:
                for p_daughter in p_daughters:
                    if p_daughter.type == dataclasses.I3Particle.Hadrons:
                        casc_0_true = p_daughter
                    else:
                        hnl_true = p_daughter
                hnl_daughters = mctree.get_daughters(hnl_true)
            else:
                decay_length = padding_value
                hnl_daughters = []

            if len(hnl_daughters) > 0:
                for count_hnl_daughters, hnl_daughter in enumerate(
                    hnl_daughters
                ):
                    if not count_hnl_daughters:
                        casc_1_true = hnl_daughter
                    else:
                        assert casc_1_true.pos == hnl_daughter.pos
                        casc_1_true.energy = (
                            casc_1_true.energy + hnl_daughter.energy
                        )
                decay_length = (
                    phys_services.I3Calculator.distance(
                        casc_0_true, casc_1_true
                    )
                    / icetray.I3Units.m
                )

            else:
                decay_length = padding_value
            return decay_length
        except:  # noqa: E722
            return padding_value

    def _muon_stopped(
        self, truth, borders, horizontal_pad=100.0, vertical_pad=100.0
    ):
        """
        Calculates where a simulated muon stops and if this is inside the detectors fiducial volume.
        IMPORTANT: The final position of the muon is saved in truth extractor/databases as position_x,position_y and position_z.
                This is analogoues to the neutrinos whose interaction vertex is saved under the same name.

        Args:
            truth (dict) : dictionary of already extracted values
            borders (tuple) : first entry xy outline, second z min/max depth. See I3TruthExtractor for hard-code example.
            horizontal_pad (float) : shrink xy plane further with exclusion zone
            vertical_pad (float) : further shrink detector depth with exclusion height

        Returns:
            dictionary (dict) : containing the x,y,z co-ordinates of final muon position and contained boolean (0 or 1)
        """
        # to do:remove hard-coded border coords and replace with GCD file contents using string no's
        border = mpath.Path(borders[0])

        start_pos = np.array(
            [truth["position_x"], truth["position_y"], truth["position_z"]]
        )

        travel_vec = -1 * np.array(
            [
                truth["track_length"]
                * np.cos(truth["azimuth"])
                * np.sin(truth["zenith"]),
                truth["track_length"]
                * np.sin(truth["azimuth"])
                * np.sin(truth["zenith"]),
                truth["track_length"] * np.cos(truth["zenith"]),
            ]
        )

        end_pos = start_pos + travel_vec

        stopped_xy = border.contains_point(
            (end_pos[0], end_pos[1]), radius=-horizontal_pad
        )
        stopped_z = (end_pos[2] > borders[1][0] + vertical_pad) * (
            end_pos[2] < borders[1][1] - vertical_pad
        )

        return {
            "x": end_pos[0],
            "y": end_pos[1],
            "z": end_pos[2],
            "stopped": (stopped_xy * stopped_z),
        }

    def _get_primary_particle_interaction_type_and_elasticity(
        self, frame, sim_type, padding_value=-1
    ):
        """ "Returns primary particle, interaction type, and elasticity.

        A case handler that does two things
            1) Catches issues related to determining the primary MC particle.
            2) Error handles cases where interaction type and elasticity doesnt exist

        Args:
            frame (i3 physics frame): ...
            sim_type (string): Simulation type
            padding_value (int | float): The value used for padding.

        Returns
            McInIcePrimary (?): The primary particle
            interaction_type (int): Either 1 (charged current), 2 (neutral current), 0 (neither)
            elasticity (float): In ]0,1[
        """
        if sim_type != "noise":
            try:
                MCInIcePrimary = frame["MCInIcePrimary"]
            except KeyError:
                MCInIcePrimary = frame["I3MCTree"][0]
            if (
                MCInIcePrimary.energy != MCInIcePrimary.energy
            ):  # This is a nan check. Only happens for some muons where second item in MCTree is primary. Weird!
                MCInIcePrimary = frame["I3MCTree"][
                    1
                ]  # For some strange reason the second entry is identical in all variables and has no nans (always muon)
        else:
            MCInIcePrimary = None
        try:
            interaction_type = frame["I3MCWeightDict"]["InteractionType"]
        except KeyError:
            interaction_type = padding_value

        try:
            elasticity = frame["I3GENIEResultDict"]["y"]
        except KeyError:
            elasticity = padding_value

        return MCInIcePrimary, interaction_type, elasticity

    def _get_primary_track_energy_and_inelasticity(
        self,
        frame: "icetray.I3Frame",
    ) -> Tuple[float, float]:
        """Get the total energy of tracks from primary, and corresponding inelasticity.

        Args:
            frame (icetray.I3Frame): Physics frame containing MC record.

        Returns:
            Tuple[float, float]: Energy of tracks from primary, and corresponding
                inelasticity.
        """
        mc_tree = frame["I3MCTree"]
        primary = mc_tree.primaries[0]
        daughters = mc_tree.get_daughters(primary)
        tracks = []
        for daughter in daughters:
            if (
                str(daughter.shape) == "StartingTrack"
                or str(daughter.shape) == "Dark"
            ):
                tracks.append(daughter)

        energy_total = primary.total_energy
        energy_track = sum(track.total_energy for track in tracks)
        inelasticity = 1.0 - energy_track / energy_total

        return energy_track, inelasticity

    # Utility methods
    def _find_data_type(self, mc, input_file):
        """Determines the data type

        Args:
            mc (boolean): is this montecarlo?
            input_file (str): path to i3 file

        Returns:
            str: the simulation/data type
        """
        # @TODO: Rewrite to make automaticallu infer `mc` from `input_file`?
        if not mc:
            sim_type = "data"
        else:
            sim_type = "NuGen"
        if "muon" in input_file:
            sim_type = "muongun"
        if "corsika" in input_file:
            sim_type = "corsika"
        if "genie" in input_file or "nu" in input_file.lower():
            sim_type = "genie"
        if "noise" in input_file:
            sim_type = "noise"
        if "L2" in input_file:  # not robust
            sim_type = "dbang"
        if sim_type == "lol":
            logger.info("SIM TYPE NOT FOUND!")
        return sim_type
