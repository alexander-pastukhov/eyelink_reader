"""Utility functions used in the main entry points.
"""

import ctypes
import os
import platform

from tqdm import tqdm

from .edfdata import EDF_EDFFILE, EDF_EVENTS, EDF_EVENT_CODES, EDF_SAMPLE_TYPE, EDF_NO_PENDING_ITEMS, EDF_RECORDING_INFO, EDF_ALLF_DATA
from .edfdata_containers import Events, Samples, Recordings


class EDFFile:
    """Content of the EDF file.

    Parameters
    ----------
    filename : str
    consistency : {0, 1, 2}, default=2
        Consistency check control (for the time stamps of the start and end events, etc).

        - 0: no consistency check.
        - 1: check consistency and report.
        - 2: check consistency and fix.
    loadevents  : bool, default=True
        Load/skip loading events.
    loadsamples : bool, default=False
        Load/skip loading of samples.
    sample_fields : list or None
        List of fields that are included. All fields are imported then set to None.
        For the list of fields please refer to  :class:`FSAMPLE` or EDF API manual.
    start_marker_string : str, default="TRIALID"
        String that contains the marker for beginning of a trial.
    end_marker_string : str, default="TRIAL_RESULT"
        String that contains the marker for end of the trial.
    parse_events : str, list, or None, default="all"
        List of specific events to exract from events table. The supported
        event types include "saccades", "fixations", "blinks", "variables", "triggers",
        and "aois". By default, "all", will extract all supported event types.
    wide_variables : bool, default=True
        Whether to pivot variables table to wide, so that each row has all variables for
        a single trial. Relevant ony if parse_events == "all" or includes "variables".
    convert_variable_types : bool, default=True
        If variables are in wide format (`wide_variables=True)`, converts columns from
        string to the best-guess type via `pandas.DataFrame.convert_dtypes <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.convert_dtypes.html#pandas.DataFrame.convert_dtypes>`__
        function.
    trigger_marker : str, default="TRIGGER"
        Initial part of the message event that identifies it as a trigger event.
        Relevant only if parse_events == "all" or includes "triggers".
    verbose : bool, default=False
        Whether to print out a progress report.
    libpath : str, default=None
        Path to EDF API library.

    Attributes
    ----------
    preamble : str
        File preamble.
    events : pandas.DataFrame
        Table with `FEVENT <#events>`__ events.
    samples  : pandas.DataFrame
        Table with `FSAMPLE <#samples>`__  data.
    recordings : pandas.DataFrame
        Table with `RECORDINGS  <#recordings>`__ entries.
    """

    def __init__(self,
                 filename,
                 consistency=2,
                 loadevents=True,
                 loadsamples=False,
                 sample_fields=None,
                 start_marker_string="TRIALID",
                 end_marker_string="TRIAL_RESULT",
                 parse_events="all",
                 wide_variables=True,
                 trigger_marker="TRIGGER",
                 verbose=False,
                 libpath=None):
        # initialize library
        self._edfapi = None
        self._load_library(libpath)

        # open the file
        self._file = self._open_file(filename, consistency, loadevents, loadsamples)

        try:
            # read preamble
            self.preamble = self._get_preamble_text()

            # initalize containers for events, samples, and recordings
            _events = Events()
            _recordings = Recordings()
            _samples = Samples(sample_fields) if loadsamples else None

            # creating progress bar if used asked for verbose
            pbar = tqdm(total=self._edfapi.edf_get_element_count(self._file)) if verbose else None

            # loading events before the first trial,
            # as they should contain service information
            trial = 0
            in_trial = False
            data_type = self._edfapi.edf_get_next_data(self._file)
            while data_type != EDF_NO_PENDING_ITEMS:
                allf_data_ptr = self._edfapi.edf_get_float_data(self._file)
                if data_type in EDF_EVENT_CODES.keys():
                    # trial start
                    if data_type == EDF_EVENTS["MESSAGEEVENT"] and \
                       allf_data_ptr.contents.fe["message"].startswith(start_marker_string):
                            trial += 1
                            in_trial = True

                    # append the event
                    _events.append(allf_data_ptr.contents.fe, trial if in_trial else None)

                    # trial ends
                    if data_type == EDF_EVENTS["MESSAGEEVENT"] and \
                       allf_data_ptr.contents.fe["message"].startswith(end_marker_string):
                        in_trial = False
                elif data_type == EDF_SAMPLE_TYPE:
                    # sample
                    _samples.append(allf_data_ptr.contents.fs, trial if in_trial else None)
                elif data_type == EDF_RECORDING_INFO:
                    _recordings.append(allf_data_ptr.contents.rec, trial if in_trial else None)

                # get next data type
                data_type = self._edfapi.edf_get_next_data(self._file)
                if pbar:
                    pbar.update(1)
        except Exception as e:
            # close file and reraise the exception
            self._close_file()
            raise e

        if pbar:
            pbar.close()

        # --- recordings ---
        self.recordings = _recordings.DataFrame
        # figuring out starting time for each trial, so we can compute event/sample times relative to it
        self._trial_start_time = self.recordings[self.recordings.state == "START"][["trial", "time"]].rename(columns={"time":"trial_start_time"}).reset_index(drop=True)

        # --- events ---
        self.events = _events.DataFrame
        # add relative time
        self.events = self.events.join(self._trial_start_time.set_index('trial'), on="trial", how="outer")
        self.events.insert(self.events.columns.tolist().index("sttime") + 1, "sttime_rel", self.events.sttime - self.events.trial_start_time)
        self.events.insert(self.events.columns.tolist().index("entime") + 1, "entime_rel", self.events.entime - self.events.trial_start_time)
        self.events = self.events.sort_values(by=['sttime']).drop(["trial_start_time"], axis=1).reset_index(drop=True)
        
        # if required, parse individual events
        if parse_events == "all" or "saccades" in parse_events:
            self.saccades = self._parse_saccades()
        if parse_events == "all" or "fixations" in parse_events:
            self.fixations = self._parse_fixations()
        if parse_events == "all" or "blinks" in parse_events:
            self.blinks = self._parse_blinks()
        if parse_events == "all" or "variables" in parse_events:
            self.variables = self._parse_variables(wide_variables)
        if parse_events == "all" or "triggers" in parse_events:
            self.triggers = self._parse_triggers(trigger_marker)
        if parse_events == "all" or "aois" in parse_events:
            self.aois = self._parse_aois()

        # --- samples ---
        if loadsamples:
            self.samples = _samples.DataFrame
            # adding relative time
            self.samples = self.samples.join(self._trial_start_time.set_index('trial'), on="trial", how="outer")
            self.samples.insert(self.samples.columns.tolist().index("time") + 1, "time_rel", self.samples.time - self.samples.trial_start_time)
            self.samples = self.samples.sort_values(by=['time']).drop(["trial_start_time"], axis=1).reset_index(drop=True)

    def _parse_saccades(self):
        """Parse saccade events.

        Extract saccade events, simplify table structure.

        Returns
        -------
        pandas.DataFrame
            Table with only saccade events, with added duration column
            without irrelevant fields.

        :meta private:
        """
        saccades = self.events[self.events.type == "ENDSACC"]

        # add duration as a column after "entime"
        saccades.insert(saccades.columns.tolist().index("entime") + 1, "duration", saccades["entime"] - saccades["sttime"])

        # drop irrelevant columns
        saccades = saccades.drop(["time", "type", "read", "status", "flags", "input", "buttons", "parsedby", "message"], axis=1).reset_index(drop=True)
        return saccades
    
    def _parse_fixations(self):
        """Parse fixation events.

        Extract fixation events, simplify table structure.

        Returns
        -------
        pandas.DataFrame
            Table with only fixation events, with added duration column
            without irrelevant fields.
        """
        fixations = self.events[self.events.type == "ENDFIX"]

        # add duration as a column after "entime"
        fixations.insert(fixations.columns.tolist().index("entime") + 1, "duration", fixations["entime"] - fixations["sttime"]) 

        fixations = fixations.drop(["time", "type", "read", "status", "flags", "input", "buttons", "parsedby", "message"], axis=1).reset_index(drop=True)
        return fixations
    
    def _parse_blinks(self):
        """Parse blink events.

        Extract blink events, simplify table structure.

        Returns
        -------
        pandas.DataFrame
            Table with only blink events, with added duration column
            without irrelevant fields.
        """
        blinks = self.events[self.events.type == "ENDBLINK"]

        # add duration as a column after "entime"
        blinks.insert(blinks.columns.tolist().index("entime") + 1, "duration", blinks["entime"] - blinks["sttime"]) 
        return blinks[["trial", "sttime", "sttime_rel", "entime", "entime_rel", "duration", "eye"]].reset_index(drop=True)

    def _parse_variables(self, wide_variables):
        """Extract variables from TRIAL_VAR nessage events.

        Extract variables from TRIAL_VAR nessage events. Attempt to pivot
        wider to (trial, variable1, variable2, ...) format. If fails, return
        long (trial, variable, value) format.

        Parameters
        ----------
        wide_variables : bool
            Whether to pivot variables table to wide, so that each row has all variables for
            a single trial.
        Returns
        -------
        pandas.DataFrame
            Either wide format (trial, variable1, variable2, ...) or,
            if pivoting fails, a long one (trial, variable, value)
        """
        # get only messages with TRIAL_VAR in it
        var_messages = self.events[(self.events.type == "MESSAGEEVENT") & (self.events.message.str.contains("TRIAL_VAR"))][["trial", "message"]].reset_index(drop=True)

        # strip and split it into Variable and Value
        var_messages['message'] = var_messages['message'].str.replace(r"^\s*!V\s*TRIAL_VAR\s*", "", regex=True).str.strip()
        var_messages.insert(1, "variable", var_messages['message'].str.split(" ").str[0])
        var_messages.insert(2, "value", var_messages['message'].str.split(" ").str[1:].str.join(" "))
        var_messages = var_messages.drop(["message"], axis=1)

        variables = var_messages
        if wide_variables:
            # attempt to convert to wide (may fail if the long structure is not suitable
            try:
                variables = var_messages.pivot_table(index=["trial"], columns=["variable"], values=["value"], aggfunc="first")
                # drop the multiindex
                variables.columns = [col[1].strip() if isinstance(col, tuple) else col for col in variables.columns]
                variables['trial'] = variables.index
                variables.reset_index(drop=True, inplace=True)
                # set the chronological order of variables
                variables = variables[["trial"] + var_messages.variable.unique().tolist()]
            except Exception as _:
                # default to long format
                variables = var_messages

        return variables
    
    def _parse_triggers(self, trigger_marker):
        """
        Parse trigger events, which are messages that start with trigger_marker.

        Parameters
        ----------
        trigger_marker : str

        Returns
        -------
        pandas.DataFrame
            Table with fields "trial", "sttime", "sttime_rel", and "label".
        """
        triggers = self.events[self.events.message.str.startswith(trigger_marker)].reset_index(drop=True)
        triggers['label'] = triggers['message'].str.replace(trigger_marker, "").str.strip()
        return triggers[["trial", "sttime", "sttime_rel", "label"]]

    def _parse_aois(self):
        """Parse AOI events.
        
        Parse AOI events, which are messages in format 
        "!V IAREA RECTANGLE <aoi_index> <left> <top> <right> <bottom> <label>"

        Returns
        -------
        pandas.DataFrame
            Table with fields "trial", "sttime", "sttime_rel", "aoi_index", "label"
            "left". "top", "right", "bottom".
        """
        # extract relevant events
        aois = self.events[self.events.message.str.startswith("!V IAREA RECTANGLE")].reset_index(drop=True)
        
        # split text into chunks
        aoi_command = aois['message'].str.replace("!V IAREA RECTANGLE", "").str.strip().str.split(" ")
        
        # use individual chunks for columns
        aois["aoi_index"] = aoi_command.str[0].astype(float).astype(int)
        aois["left"] = aoi_command.str[1].astype(float).astype(int)
        aois["top"] = aoi_command.str[2].astype(float).astype(int)
        aois["right"] = aoi_command.str[3].astype(float).astype(int)
        aois["bottom"] = aoi_command.str[4].astype(float).astype(int)
        aois["label"] = aoi_command.str[5:].str.join(" ")

        return aois[["trial", "sttime", "sttime_rel", "aoi_index", "label", "left", "top", "right", "bottom"]]

    def _load_library(self, path=None):
        """
        Attempts to initialize the EDF API library. Uses following path in that order:
        1) from path parameter, 2) from a EDFAPI_LIB environment variable, if it exists,
        3) with no path, assuming that library folder is in PATH, 4) using a typical
        path for the OS.
        
        Parameters
        ----------
        path : str, default=None
            Path to EDF API library.

        Raises
        ------
        ImportError
            If library was not found or OS is unsupported.
        """
        # figuring out the name of the library, Win64 is a special case
        edfapi_filename = "edfapi"
        if platform.system() == "Windows" and platform.architecture()[0] == "64bit":
            edfapi_filename = "edfapi64"
        elif platform.system() == "Linux":
            edfapi_filename = "libedfapi.so"

        paths_to_try = []
        # 1) use path provided as a parameter
        if path is not None:
            paths_to_try.append(path)

        # 2) from EDFAPI_LIB environment varible, if it exists
        if "EDFAPI_LIB" in os.environ:
            paths_to_try.append(os.environ["EDFAPI_LIB"])

        # 3) No path, assumes that folder is in PATH
        paths_to_try.append("")

        # 4) A typical path for each library
        if platform.system() == "Windows":
            if platform.architecture()[0] == "64bit":
                paths_to_try.append("c:/Program Files (x86)/SR Research/EyeLink/libs/x64")
            else:
                paths_to_try.append("c:/Program Files (x86)/SR Research/EyeLink/libs")
        elif platform.system() == "Darwin":
            paths_to_try.append("/Library/Frameworks/")
        elif platform.system() == "Linux":
            paths_to_try.insert(0,"/usr/lib/x86_64-linux-gnu/")
        else:
            raise ImportError("EDF API libary is not available for this platform.")

        # test all paths and see whether we initialize the library
        self._edfapi = None
        for lib_path in paths_to_try:
            try:
                self._edfapi = ctypes.CDLL(os.path.join(lib_path, edfapi_filename))
                break # we only get here, if the exception was not raised, i.e., we've found it
            except FileNotFoundError:
                self._edfapi = None

        # raise exception, if we could not initialize the library
        if self._edfapi is None:
            raise ImportError("Could not load EDF API libary.")

        # define inputs and ouput for all relevant functions
        self._edfapi.edf_get_version.restype = ctypes.c_char_p

        self._edfapi.edf_open_file.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self._edfapi.edf_open_file.restype = ctypes.POINTER(EDF_EDFFILE)

        self._edfapi.edf_close_file.argtypes = [ctypes.POINTER(EDF_EDFFILE)]
        self._edfapi.edf_close_file.restype = ctypes.c_int

        self._edfapi.edf_get_preamble_text_length.argtypes = [ctypes.POINTER(EDF_EDFFILE)]
        self._edfapi.edf_get_preamble_text_length.restype = ctypes.c_int

        self._edfapi.edf_get_preamble_text.argtypes = [ctypes.POINTER(EDF_EDFFILE), ctypes.c_char_p, ctypes.c_int]
        self._edfapi.edf_get_preamble_text.restype = ctypes.c_int

        self._edfapi.edf_get_next_data.argtypes = [ctypes.POINTER(EDF_EDFFILE)]
        self._edfapi.edf_get_next_data.restype = ctypes.c_int

        self._edfapi.edf_get_float_data.argtypes = [ctypes.POINTER(EDF_EDFFILE)]
        self._edfapi.edf_get_float_data.restype = ctypes.POINTER(EDF_ALLF_DATA)

        self._edfapi.edf_get_element_count.argtypes = [ctypes.POINTER(EDF_EDFFILE)]
        self._edfapi.edf_get_element_count.restype = ctypes.c_uint

        self._edfapi.edf_set_trial_identifier.argtypes = [ctypes.POINTER(EDF_EDFFILE), ]

        self._edfapi.edf_get_trial_count.argtypes = [ctypes.POINTER(EDF_EDFFILE), ctypes.c_char_p, ctypes.c_char_p]
        self._edfapi.edf_get_trial_count.restype = ctypes.c_int

    @property
    def version(self):
        """str: EDF API library version.
        """
        return self._edfapi.edf_get_version().decode("utf-8")

    def _get_preamble_text(self):
        """Read preamble text.
        
        Returns
        -------
        str

        Raises
        ------
        ValueError
            If edf_get_preamble_text returned an error.
        """
        preamble_length = self._edfapi.edf_get_preamble_text_length(self._file)
        p_preamble = ctypes.create_string_buffer(preamble_length)
        errcode = self._edfapi.edf_get_preamble_text(self._file, p_preamble, preamble_length)
        if errcode != 0:
            raise ValueError(f"Cannot read preamble, error code {errcode}")
        return p_preamble.value.decode("UTF-8")

    def _open_file(self, filename, consistency, loadevents, loadsamples):
        """
        Open EDF file for reading

        Parameters
        ----------
        filename : str
        consistency : {0, 1, 2}
            Consistency check control (for the time stamps of the start and end events, etc).
            0, no consistency check.
            1,  check consistency and report.
            2,  check consistency and fix.
        loadevents  : bool
            Load/skip loading events.
        loadsamples : bool
            Load/skip loading of samples.

        Returns
        -------
        EDF_EDFFILE

        Raises
        ------
        FileNotFoundError
            If edf_open_file returns an error.
        ValueError
            If consistency value is invalid.
        """
        if consistency not in [0, 1, 2]:
            raise ValueError("Invalid value for consistency parameter, must be 0, 1, or 2.")
        
        errval = ctypes.c_int()
        edf_file = self._edfapi.edf_open_file(filename.encode(), consistency, int(loadevents), int(loadsamples), ctypes.byref(errval))
        if errval.value != 0:
            raise FileNotFoundError(f"Error opening file, error code:{errval}.")
        return edf_file

    def _close_file(self):
        """Close EDF file gracefully.

        Raises
        ------
        RuntimeError
            If edf_close_file returned an error.
        """
        errcode = self._edfapi.edf_close_file(self._file)
        if errcode != 0:
            raise RuntimeError(f"Failed to close the file, error code: {errcode}")
