"""Containers for EDF events, samples, and recordings.

Classes
----------
Events
    Container for EDF_FEVENT entries
Samples
    Container for EDF_FSAMPLE entries
Recordings
    Container for EDF_RECORDINGS entries
"""

from ctypes import POINTER, c_uint16, c_uint32, c_int16, c_float, c_ubyte, c_ulong, c_ushort, c_short, c_byte
import pandas as pd

from .edfdata import EDF_LSTRING, EDF_FEVENT, EDF_FSAMPLE, EDF_RECORDINGS, EDF_EVENT_CODES, EDF_EYE_CODES, EDF_MISSING_DATA
from .edfdata import EDF_RECORDING_STATE, EDF_RECORDING_RECORD_TYPE, EDF_RECORDING_PUPIL_TYPE, EDF_RECORDING_RECORDING_MODE, EDF_RECORDING_POS_TYPE, EDF_RECORDING_EYE


CTYPES_TO_PANDAS = {c_ubyte : "UInt8",
                    c_byte :"Int8",
                    c_ushort : "UInt16",
                    c_uint16 : "UInt16",
                    c_int16 : "Int16",
                    c_short : "Int16",
                    c_ulong : "UInt32",
                    c_uint32 : "UInt32",
                    c_float : "Float32",
                    POINTER(EDF_LSTRING) : "string",
                    c_float * 2 : "Float32",
                    c_int16 * 8 : "Int16"                    
                    }


def value_or_none(value, missing_data=EDF_MISSING_DATA):
    """Return value or None, if value==missing_data.

    Parameters
    ----------
    value : int, float
    missing_data : int, default=edfdata.EDF_MISSING_DATA
        Integer value that identifies missing data

    Returns
    ----------
    int, float, None
    """
    return value if value != missing_data else None


class Events:
    """Container for EDF_FEVENT events.

    A container to accumulate events and convert them into a pandas.DataFrame.
    """
    def __init__(self):
        # initialize using field names of FEVENT structure + trial
        self._entries = {field : [] for field in ["trial"] + EDF_FEVENT.fields_names}
        self._table_fields = {"trial" : "Int32"}
        for field in EDF_FEVENT.fields_names:
            self._table_fields[field] = CTYPES_TO_PANDAS[EDF_FEVENT.fields_types[field]]
        self._categorical = {"type" : EDF_EVENT_CODES,
                             "eye" : EDF_EYE_CODES}

    def append(self, event, trial=None):
        """Append current event.

        Parameters
        ----------
        event : FEVENT
        trial : int, optional
            Trial index, None means that event occured outside of the trial. 
        """
        self._entries["trial"].append(trial)
        for field in EDF_FEVENT.fields_names:
            self._entries[field].append(value_or_none(event[field]))

    @property
    def DataFrame(self):
        """Events table as pandas.DataFrame
        """
        # create table
        df = pd.DataFrame(self._entries, columns=self._table_fields.keys()).astype(self._table_fields)

        # categorical columns
        for col_name, col_dict in self._categorical.items():
            df[col_name] = df[col_name].astype("category").cat.rename_categories(col_dict)

        return df


class Samples:
    """Container for EDF_FSAMPLE samples.

    Container to accumulate samples and convert them into a pandas.DataFrame.
    """
    def __init__(self, selected_fields=None):
        """
        Parameters
        ----------
        selected_fields : list, optional
            List of EDF_FSAMPLE structure fields.

        Raises
        ----------
        ValueError
            If invalid field names are supplied.
        """
        # figure out which field names to copy
        if selected_fields is None:
            self._field_names = EDF_FSAMPLE.fields_names
        else:
            # check whether sample fields are part of the actual FSAMPLE
            valid_fields = set(EDF_FSAMPLE.fields_names).intersection(set(selected_fields))
            if set(selected_fields) != valid_fields:
                # some fields were invalid
                raise ValueError("Invalid sample field names.")
            self._field_names = selected_fields
            
        # create placeholders for data, including left/right eye
        self._entries = {"trial" : []}
        self._table_fields = {"trial": "Int32"}
        for field in self._field_names:
            if field == "hdata":
                # special case, 8 element array that must be diviced into 8 columns
                for i in range(8):
                    self._entries[field + str(i)] = []
                    self._table_fields[field + str(i)] = CTYPES_TO_PANDAS[EDF_FSAMPLE.fields_types[field]]
            elif EDF_FSAMPLE._is_binocular(field):
                # left/right eye data
                self._entries[field + "L"] = []
                self._entries[field + "R"] = []
                self._table_fields[field + "L"] = CTYPES_TO_PANDAS[EDF_FSAMPLE.fields_types[field]]
                self._table_fields[field + "R"] = CTYPES_TO_PANDAS[EDF_FSAMPLE.fields_types[field]]
            else:
                # single column data
                self._entries[field] = []
                self._table_fields[field] = CTYPES_TO_PANDAS[EDF_FSAMPLE.fields_types[field]]

    def append(self, sample, trial):
        """Append sample.

        Parameters
        ----------
        sample : FSAMPLE
        trial : int
        """
        self._entries["trial"].append(trial)
        for field in self._field_names:
            if field == "hdata":
                # 8 element array
                for i in range(8):
                    self._entries[field + str(i)].append(value_or_none(sample[field][i]))
            elif EDF_FSAMPLE._is_binocular(field):
                # 2 element array
                self._entries[field + "L"].append(value_or_none(sample[field][0]))
                self._entries[field + "R"].append(value_or_none(sample[field][1]))
            else:
                # single value
                self._entries[field].append(value_or_none(sample[field]))

    @property
    def DataFrame(self):
        """Samples table as pandas.DataFrame
        """
        return pd.DataFrame(self._entries, columns=self._table_fields.keys()).astype(self._table_fields)


class Recordings:
    """Container for EDF_RECORDINGS entries.

    A container to accumulate recordings and convert them into a pandas.DataFrame.
    """
    def __init__(self):
        # initialize using field names of FEVENT structure + trial
        self._entries = {field : [] for field in ["trial"] + EDF_RECORDINGS.fields_names}
        self._table_fields = {"trial" : "Int32"}
        for field in EDF_RECORDINGS.fields_names:
            self._table_fields[field] = CTYPES_TO_PANDAS[EDF_RECORDINGS.fields_types[field]]
        self._categorical = {"state" : EDF_RECORDING_STATE,
                             "record_type" : EDF_RECORDING_RECORD_TYPE,
                             "pupil_type" : EDF_RECORDING_PUPIL_TYPE,
                             "recording_mode" : EDF_RECORDING_RECORDING_MODE,
                             "pos_type" : EDF_RECORDING_POS_TYPE,
                             "eye" : EDF_RECORDING_EYE}

    def append(self, event, trial=None):
        """Append current event.

        Parameters
        ----------
        event : FEVENT
        trial : int, optional
            Trial index, None means that event occured outside of the trial. 
        """
        self._entries["trial"].append(trial)
        for field in EDF_RECORDINGS.fields_names:
            self._entries[field].append(value_or_none(event[field]))

    @property
    def DataFrame(self):
        """Events table as pandas.DataFrame.
        """
        df = pd.DataFrame(self._entries, columns=self._table_fields.keys()).astype(self._table_fields)

        # categorical columns
        for col_name, col_dict in self._categorical.items():
            df[col_name] = df[col_name].astype("category").cat.rename_categories(col_dict)

        return df
