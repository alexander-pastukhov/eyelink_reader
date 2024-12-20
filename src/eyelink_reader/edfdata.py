"""Python definitions of EDF API data structures. 
Original names of structures are prepended by EDF_ prefix.
Comments are taken from original library definitions.
"""

from ctypes import Structure, POINTER, c_uint16, c_uint32, c_int16, c_float, c_char, c_ubyte, Union

EDF_EYE_CODES = {0 : "LEFT", 1 : "RIGHT", 2: "BINOCULAR"}
EDF_RECORDING_STATE = {0 : "END", 1 : "START"}
EDF_RECORDING_RECORD_TYPE = {1 : "SAMPLES", 2 : "EVENTS", 3: "SAMPLES and EVENTS"}
EDF_RECORDING_PUPIL_TYPE = {0 : "AREA", 1 : "DIAMETER"}
EDF_RECORDING_RECORDING_MODE = {0 : "PUPIL", 1 : "CR"}
EDF_RECORDING_POS_TYPE = {0 : "GAZE", 1 : "HREF", 2 : "RAW"}
EDF_RECORDING_EYE = {1 : "LEFT", 2 : "RIGHT", 3 : "BINOCULAR"}

EDF_MISSING_DATA = -32768

# possible values returned by edf_get_next_data
EDF_NO_PENDING_ITEMS = 0
EDF_RECORDING_INFO = 30
EDF_SAMPLE_TYPE = 200

EDF_EVENTS = {
    # these only have time and eye data
    "STARTPARSE": 1,       
    "ENDPARSE": 2,
    "BREAKPARSE": 10,

    # EYE DATA: contents determined by evt_data and by "read" data item
    # all use IEVENT format
    "STARTBLINK": 3,
    "ENDBLINK": 4,
    "STARTSACC": 5,
    "ENDSACC": 6,
    "STARTFIX": 7,
    "ENDFIX": 8,
    "FIXUPDATE": 9,

    # buffer = (none, directly affects state), btype = CONTROL_BUFFER
    # control events: all put data into the EDF_FILE or ILINKDATA status
    "STARTSAMPLES": 15,    # start of samples in block
    "ENDSAMPLES": 16,      # end of samples in block
    "STARTEVENTS": 17,     # start of events in block
    "ENDEVENTS": 18,       # end of events in block

    # buffer = IMESSAGE, btype = IMESSAGE_BUFFER
    "MESSAGEEVENT": 24,    # user-definable text or data
    "BUTTONEVENT" : 25,
    "INPUTEVENT" : 28,

    "LOST_DATA_EVENT": 0x3F  # Event flags gap in data stream
}

EDF_EVENT_CODES = {event[1] : event[0] for event in EDF_EVENTS.items()}


class EDF_LSTRING(Structure):
    """String used by EDF API
    """
    _fields_ = [
        ("len", c_int16),  # length of the string
        ("c", c_char * 1024)      # character array
    ]


class EDF_EDFFILE(Structure):
    """A dummy structure that holds an EDF file handle.
    """
    pass


class EDF_FSAMPLE(Structure):
    """`samples` attribute of `EDFFile` class is based on the content of  FSAMPLE structure
    that holds information for a sample in the EDF file. This structure is corresponds to a
    single row in pandas.DataFrame table. Which columns are present depends on `sample_fields`
    parameter of EDFFile. Depending on the recording options set for the recording session,
    some of the fields may be empty.

    Binocular fields, e.g., `px`, `py`, `hx`, `hy`, etc. that are represented in the
    structure as two-element arrays are split into two columns with suffixes
    L and R, so that `pxL = px[0]` and `pxR = px[1]`, `pyL = py[0]`, `pyR = py[1]`, 
    etc. The field `hdata`, which is an array of eight elements is split into eight
    columns `hdata0`, `hadata1`, ..., `hdata7`. Columns `trial` and `time_rel` are
    not part of the original `FSAMPLE` structure.

    Attributes
    ----------
    trial : uint32
        Trial index, not part of the original `FSAMPLE` structure.
    time : uint32
        Time stamp of the sample.
    time_rel : uint32
        Time stamp of the sample relative to the beginning of recording.
        Not part of the original `FSAMPLE` structure.
    px : float[2]
        Pupil x coordinates, split into pxL and pxR columns.
    py : float[2]
        Pupil y coordinates, split into pyL and pyR columns.
    hx : float[2]
        Head reference x coordinates, split into hxL and hxR columns.
    hy : float[2]
        Head reference y coordinates, split into hyL and hyR columns.
    pa : float[2]
        Pupil size or area, split into paL and paR columns.
    gx : float[2]
        Gaze x coordinates on the screen, split into gxL and gxR columns.
    gy : float[2]
        Gaze y coordinates on the screen, split into gyL and gyR columns.
    rx : float
        Screen pixels per degree in the x direction.
    ry : float
        Screen pixels per degree in the y direction.
    gxvel : float[2]
        Gaze x velocity, split into gxvelL and gxvelR columns.
    gyvel : float[2]
        Gaze y velocity, split into gyvelL and gyvelR columns.
    hxvel : float[2]
        Head reference x velocity, split into hxvelL and hxvelR columns.
    hyvel : float[2]
        Head reference y velocity, split into hyvelL and hyvelR columns.
    rxvel : float[2]
        Raw x velocity, split into rxvelL and rxvelR columns.
    rxvel : float[2]
        Raw y velocity, split into rxvelL and rxvelR columns.
    fgxvel : float[2]
        Fast gaze x velocity, split into fgxvelL and fgxvelR columns.
    fgyvel : float[2]
        Fast gaze y velocity, split into fgyvelL and fgyvelR columns.
    fhxvel : float[2]
        Fast head reference x velocity, split into fhxvelL and fhxvelR columns.
    fhyvel : float[2]
        Fast head reference y velocity, split into fhyvelL and fhyvelR columns.
    frxvel : float[2]
        Fast raw x velocity, split into frxvelL and frxvelR columns.
    fryvel : float[2]
        Fast raw y velocity, split into fryvelL and fryvelR columns.
    hdata : int16[8]
        Head-tracker data (array of eight integers). Split into columns
        hdata0, hdata1, ..., hdata7.
    flags : uint16
        Flags to indicate contents of the sample.
    input : uint16
        Extra input word.
    buttons : uint16
        Button state and changes.
    htype : int16
        Head-tracker data type (0 = none).
    errors : uint16
        Process error flags.
    """
    _fields_ = [
        ("time", c_uint32),  # time stamp of sample
        # ("type", c_int16),  # always SAMPLE_TYPE

        ("px", c_float * 2),  # pupil x
        ("py", c_float * 2),  # pupil y
        ("hx", c_float * 2),  # headref x
        ("hy", c_float * 2),  # headref y
        ("pa", c_float * 2),  # pupil size or area

        ("gx", c_float * 2),  # screen gaze x
        ("gy", c_float * 2),  # screen gaze y
        ("rx", c_float),      # screen pixels per degree (x)
        ("ry", c_float),      # screen pixels per degree (y)

        ("gxvel", c_float * 2),  # gaze x velocity
        ("gyvel", c_float * 2),  # gaze y velocity
        ("hxvel", c_float * 2),  # headref x velocity
        ("hyvel", c_float * 2),  # headref y velocity
        ("rxvel", c_float * 2),  # raw x velocity
        ("ryvel", c_float * 2),  # raw y velocity

        ("fgxvel", c_float * 2),  # fast gaze x velocity
        ("fgyvel", c_float * 2),  # fast gaze y velocity
        ("fhxvel", c_float * 2),  # fast headref x velocity
        ("fhyvel", c_float * 2),  # fast headref y velocity
        ("frxvel", c_float * 2),  # fast raw x velocity
        ("fryvel", c_float * 2),  # fast raw y velocity

        ("hdata", c_int16 * 8),   # head-tracker data (not pre-scaled)
        ("flags", c_uint16),      # flags to indicate contents

        # ("status", c_uint16),   # tracker status flags (commented out)
        ("input", c_uint16),      # extra (input word)
        ("buttons", c_uint16),    # button state & changes

        ("htype", c_int16),       # head-tracker data type (0=none)

        ("errors", c_uint16)      # process error flags
    ]
    fields_names = [field[0] for field in _fields_]
    fields_types = {field[0] : field[1] for field in _fields_}

    # which columns DO NOT contain binocular information
    @staticmethod
    def _is_binocular(field_name):
        """
        Is field binocular (requires two containers) or monocular?

        Parameters
        ----------
        field_name : str

        Returns
        ----------
        bool

        Raises
        ----------
        KeyError
            If fieldname is invalid.
        """
        if field_name not in EDF_FSAMPLE.fields_names:
            raise KeyError("Invalid field name")

        return field_name not in ["time", "rx", "ry", "hdata", "flags", "input", "buttons", "htype", "errors"]

    def __getitem__(self, field_name):
        """Return value of the corresponding field given its types.

        Parameters
        ----------
        field_name : str
    
        Returns
        ----------
        object
            integeter, float, or array depending on the field

        Raises
        ----------
        KeyError
            If field_name is not valid.
        """
        if field_name not in self.fields_names:
            raise KeyError("Invalid field name.")

        return getattr(self, field_name)


class EDF_FEVENT(Structure):
    """
    `events` attribute of `EDFFile` class is based on the content
    of FEVENT structure that holds information for an event in the EDF file.
    This structure is corresponds to a single row in pandas.DataFrame table.
    Depending on the recording options set for the recording session and the event type, 
    some of the fields may be empty.

    Attributes
    ----------
    trial : uint32
        Trial index, not part of the original FEVENT structure.
    time : uint32
        Effective time of the event.
    type : int16
        The type of the event.
    read : uint16
        Flags indicating which items were included in the event.
    sttime : uint32
        Start time of the event.
    sttime_rel : uint32
        Start time of the event relative to the start of recording.
        Not part of the original FEVENT structure.
    entime : uint32
        End time of the event.
    entime_rel: uint32
        End time of the event  relative to the start of recording.
        Not part of the original FEVENT structure.
    duration : uint32
        Duration of the event, only defined for non-empty values
        for `sttime` and `entime`.
    hstx : float
        Starting point of head reference (x-axis).
    hsty : float
        Starting point of head reference (y-axis).
    gstx : float
        Starting point of gaze (x-axis).
    gsty : float
        Starting point of gaze (y-axis).
    sta : float
        Pupil size at the start of the event.
    henx : float
        Ending point of head reference (x-axis).
    heny : float
        Ending point of head reference (y-axis).
    genx : float
        Ending point of gaze (x-axis).
    geny : float
        Ending point of gaze (y-axis).
    ena : float
        Pupil size at the end of the event.
    havx : float
        Average head reference (x-axis).
    havy : float
        Average head reference (y-axis).
    gavx : float
        Average gaze (x-axis).
    gavy : float
        Average gaze (y-axis).
    ava : float
        Average pupil size.
    avel : float
        Accumulated average velocity.
    pvel : float
        Accumulated peak velocity.
    svel : float
        Start velocity.
    evel : float
        End velocity.
    supd_x : float
        Start units-per-degree on the x-axis.
    eupd_x : float
        End units-per-degree on the x-axis.
    supd_y : float
        Start units-per-degree on the y-axis.
    eupd_y : float
        End units-per-degree on the y-axis.
    eye : int16
        Eye indicator (0 = left, 1 = right).
    status : uint16
        Error or warning flags for the event.
    flags : uint16
        Additional flags for the event.
    input : uint16
        Input data for the event.
    buttons : uint16
        Button state and changes.
    parsedby : uint16
        7 bits of flags representing the PARSEDBY codes.
    message : str
        Message associated with the event.
    """
    _fields_ = [
        ("time", c_uint32),       # effective time of event
        ("type", c_int16),        # event type
        ("read", c_uint16),       # flags which items were included

        ("sttime", c_uint32),     # start time of the event
        ("entime", c_uint32),     # end time of the event

        ("hstx", c_float),        # headref starting points (x)
        ("hsty", c_float),        # headref starting points (y)
        ("gstx", c_float),        # gaze starting points (x)
        ("gsty", c_float),        # gaze starting points (y)

        ("sta", c_float),         # pupil size at start

        ("henx", c_float),        # headref ending points (x)
        ("heny", c_float),        # headref ending points (y)
        ("genx", c_float),        # gaze ending points (x)
        ("geny", c_float),        # gaze ending points (y)

        ("ena", c_float),         # pupil size at end

        ("havx", c_float),        # headref averages (x)
        ("havy", c_float),        # headref averages (y)
        ("gavx", c_float),        # gaze averages (x)
        ("gavy", c_float),        # gaze averages (y)

        ("ava", c_float),         # average pupil size
        ("avel", c_float),        # accumulated average velocity
        ("pvel", c_float),        # accumulated peak velocity
        ("svel", c_float),        # start velocity
        ("evel", c_float),        # end velocity

        ("supd_x", c_float),      # start units-per-degree (x)
        ("eupd_x", c_float),      # end units-per-degree (x)
        ("supd_y", c_float),      # start units-per-degree (y)
        ("eupd_y", c_float),      # end units-per-degree (y)

        ("eye", c_int16),         # eye: 0=left, 1=right
        ("status", c_uint16),     # error, warning flags
        ("flags", c_uint16),      # error, warning flags
        ("input", c_uint16),      # input
        ("buttons", c_uint16),    # buttons
        ("parsedby", c_uint16),   # 7 bits of flags: PARSEDBY codes

        ("message", POINTER(EDF_LSTRING))  # pointer to LSTRING
    ]

    fields_names = [field[0] for field in _fields_]
    fields_types = {field[0] : field[1] for field in _fields_}

    def __getitem__(self, field_name):
        """Return value of the corresponding field given its types.

        Parameters
        ----------
        field_name : str
    
        Returns
        ----------
        object
            integeter, float, or str depending on the field

        Raises
        ----------
        KeyError
            If field_name is not valid.
        """
        if field_name not in self.fields_names:
            raise KeyError("Invalid field name.")

        if field_name == "message":
            # special case of LSTRING
            if getattr(self, field_name) and getattr(self, field_name).contents.len > 0 and len(getattr(self, field_name).contents.c) > 0:
                try:
                    message_str = getattr(self, field_name).contents.c.decode("latin-1")
                except UnicodeDecodeError:
                    message_str = ""
                return message_str
            else:
                # NULL pointer
                return ""
        else:
            return getattr(self, field_name)


class EDF_RECORDINGS(Structure):
    """
    `recordings` attribute of `EDFFile` class  is based on     
    `RECORDINGS` structure, which is present at the start and end of a recording. 
    It contains metadata about the recording options and state, conceptually 
    similar to the START and END lines in an EyeLink ASC file.

    Attributes
    ----------
    time : uint32
        The start or end time of the recording block.
    sample_rate : float
        The sampling rate during the recording, typically 250, 500, or 1000 Hz.
    eflags : uint16
        Extra information about the events in the recording.
    sflags : uint16
        Extra information about the samples in the recording.
    state : pandas.categorical
        Indicates whether this is the START (1) or END (0) of a recording block.
    record_type : pandas.categorical
        Specifies what was recorded: 1 for SAMPLES, 2 for EVENTS, 3 for both (SAMPLES and EVENTS).
    pupil_type : pandas.categorical
        The type of pupil data: 0 for AREA, 1 for DIAMETER.
    recording_mode : pandas.categorical
        The recording mode: 0 for PUPIL, 1 for CORNEAL REFLECTION (CR).
    filter_type : byte
        The filter type applied to the data, usually 1, 2, or 3.
    pos_type : pandas.categorical
        Specifies the position type: 0 for GAZE, 1 for HREF, 2 for RAW.
    eye : pandas.categorical
        Indicates which eye was recorded: 1 for LEFT, 2 for RIGHT, 3 for BINOCULAR.
    """
    _fields_ = [
        ("time", c_uint32),        # start time or end time of the recording block
        ("sample_rate", c_float),  # sampling rate (e.g., 250, 500, 1000 Hz)
        ("eflags", c_uint16),      # extra information about events
        ("sflags", c_uint16),      # extra information about samples
        ("state", c_ubyte),        # 0 = END, 1 = START
        ("record_type", c_ubyte),  # 1 = SAMPLES, 2 = EVENTS, 3 = BOTH
        ("pupil_type", c_ubyte),   # 0 = AREA, 1 = DIAMETER
        ("recording_mode", c_ubyte),  # 0 = PUPIL, 1 = CR (corneal reflection)
        ("filter_type", c_ubyte),  # filter type (1, 2, or 3)
        ("pos_type", c_ubyte),     # position type: 0 = GAZE, 1 = HREF, 2 = RAW
        ("eye", c_ubyte)           # eye: 1 = LEFT, 2 = RIGHT, 3 = BOTH
    ]

    fields_names = [field[0] for field in _fields_]
    fields_types = {field[0] : field[1] for field in _fields_}

    def __getitem__(self, field_name):
        """Return value of the corresponding field given its types.

        Parameters
        ----------
        field_name : str
    
        Returns
        ----------
        object
            integer, float, or byte depending on the field

        Raises
        ----------
        KeyError
            If field_name is not valid.
        """
        if field_name not in self.fields_names:
            raise KeyError("Invalid field name.")
        return getattr(self, field_name)


class EDF_IMESSAGE(Structure):
    """
    Represents a message event structure, typically used for logging messages.

    Attributes
    ----------
    time : ctypes.c_uint32
        Time when the message was logged.
    type : ctypes.c_int16
        Event type, usually MESSAGEEVENT.
    length : ctypes.c_uint16
        Length of the message.
    text : ctypes.c_ubyte * 260
        Message content (maximum length 255).

    :exclude-members: _fields_
    """
    _fields_ = [
        ("time", c_uint32),       # time message logged
        ("type", c_int16),        # event type, usually MESSAGEEVENT
        ("length", c_uint16),     # length of message
        ("text", c_ubyte * 260)   # message contents (max length 255)
    ]

    fields_names = [field[0] for field in _fields_]

    def __getitem__(self, field_name):
        """Return value of the corresponding field given its types.

        Parameters
        ----------
        field_name : str
    
        Returns
        ----------
        object
            integer, float, or byte depending on the field

        Raises
        ----------
        KeyError
            If field_name is not valid.
        """
        if field_name not in self.fields_names:
            raise KeyError("Invalid field name.")
        return getattr(self, field_name)

class EDF_IOEVENT(Structure):
    """
    A structure representing an IO event.

    Attributes
    ----------
    time : ctypes.c_uint32
        The time when the event was logged.
    type : ctypes.c_int16
        The event type.
    data : ctypes.c_uint16
        Coded event data.
    """
    _fields_ = [
        ("time", c_uint32),    # time logged
        ("type", c_int16),     # event type
        ("data", c_uint16)     # coded event data
    ]

    fields_names = [field[0] for field in _fields_]

    def __getitem__(self, field_name):
        """Return value of the corresponding field given its types.

        Parameters
        ----------
        field_name : str
    
        Returns
        ----------
        object
            integer, float, or byte depending on the field

        Raises
        ----------
        KeyError
            If field_name is not valid.
        """
        if field_name not in self.fields_names:
            raise KeyError("Invalid field name.")
        return getattr(self, field_name)

class EDF_ALLF_DATA(Union):
    """
    A union representing one of the following data types: FEVENT, IMESSAGE, IOEVENT, FSAMPLE, or RECORDINGS.

    Attributes
    ----------
    fe : FEVENT
    im : IMESSAGE
    io : IOEVENT
    fs : FSAMPLE
    rec : RECORDINGS
    """
    _fields_ = [
        ("fe", EDF_FEVENT),
        ("im", EDF_IMESSAGE),
        ("io", EDF_IOEVENT),
        ("fs", EDF_FSAMPLE),
        ("rec", EDF_RECORDINGS)
    ]

