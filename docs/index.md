# eyelink_reader
[![DOI](https://zenodo.org/badge/882465451.svg)](https://doi.org/10.5281/zenodo.14262527)

**eyelink_reader** is a Python library to import eye tracking recording from  EDF-files generated by [SR Research](https://www.sr-research.com) EyeLink eye tracker. It includes options to import events and/or recorded samples and pasring of individual events such as saccades, fixations, blinks, recorded variables, triggers, and areas-of-interest.

# Installation

Please note that these instructions may be outdate, i.e., if SR Research changes its software. If that is the case, please [raise an issue](https://github.com/alexander-pastukhov/eyelink_reader/issues).

## Install SR Research EyeLink Developers Kit

This package relies on _edfapi_ library that is as part of the *EyeLink Developers Kit*, which can be downloaded from [www.sr-research.com/support](https://www.sr-research.com/support) website. Note that you need to register and wait for your account to be activated. Next, follow instructions to install *EyeLink Developers Kit* for your platform. The forum thread should be under _SR Support Forum › Downloads › EyeLink Developers Kit / API › Download: EyeLink Developers Kit / API Downloads (Windows, macOS, Linux)_.

**Please note that this package will not work without Eyelink Developers Kit!**

## Specify location of the *edfapi* library

The package looks for _edfapi_ either in the global environment (i.e., the folder is added to the `PATH`) or in a typical path for the OS. The typical locations are:

* For Windows: `c:/Program Files (x86)/SR Research/EyeLink/libs/x64`
* For Mac OSX: `/Library/Frameworks`
* For Linux: `edpapi` library is install in `/usr/lib`, so is in the global path.

If you installed _EyeLink Developers Kit_ using defaults, the typical paths should work. However, you may have used a different folder for installation (relevant primarily for Windows) or it is possible that SR Research changed the defaults. In this case, you can specify path to the library as a parameter or set `EDFAPI_LIB` environment variable.

## Install package via pip
```
pip install eyelink_reader
```

# Usage

All the functionality in encapsulated in the [EDFFile](#edffile-class) class. The minimal call that imports events but not samples and parses all possible events is
```python
from eyelink_reader import EDFFile

gaze = EDFFile("test.edf")
```

## Importing samples

To import samples with all fields use
```python
gaze = EDFFile("test.edf", loadsamples=True)
```

In most cases, you probably only want a subset of fields, which you can specify via `sample_fields` parameter (for the list of fields see [Samples](#samples)). For example, you can only import sample time and eye position in screen coordinates, as shown below. For binocular fields, such as `gx` that are split into `gxL` and `gxR` in [Samples](#samples) table, you only need to specify the common name `gx`.
```python
gaze = EDFFile("test.edf", loadsamples=True, sample_fields=["time", "gx", "gy"])
```

## Specifying custom trial start and end messages
By default, the library assumes that trial start and end are marked by standard messages `"TRIALID"` and `"TRIAL_RESULT"`, respectively. However, you can pass custom messages via `start_marker_string` and `end_marker_string` parameters.
```python
gaze = EDFFile("test.edf", start_marker_string="TRIALID", end_marker_string="TRIAL_RESULT")
```

## Verbose loading
For large files loading may take some seconds. If you want to monitor the process, you can enable a progress bar via `verbose=True`:
```python
gaze = EDFFile("test.edf", loadsamples=True, verbose=True)
```

## Specifying _edfapi_ library path
As described in the [section above](#specify-location-of-the-edfapi-library), [EDFFile](#edffile-class) searches for _edfapi_ library in the global path, path in `EDFAPI_LIB` environtment library, and a typical path for the OS. However, you can also pass the path via `libpath` parameter:
```python
gaze = EDFFile("test.edf", libpath="c:/Program Files (x86)/SR Research/EyeLink/libs/x64")
```

## Parsing specific events
The [events](#Events) attrbiute of [EDFFile](#edffile-class) is a table that contains all recorded events. For convenience, they can be parsed into

* [saccades](#saccades)
* [fixations](#fixations)
* [blinks](#blinks)
* [variables](#variables), see also [Parsing variables](#parsing-variables) section for details.
* [triggers](#triggers), see also [Parsing triggers](#parsing-triggers) section for details.
* [aois](#aois) (areas-of-interest), see also [Parsing AOIs](#parsing-aois) section for details.

A specific set of events to be parsed and extract is specified via `parse_events` parameter. Use `parse_events="all"` to extract all event types (default behavior) and `parse_events=None`, if you do not want events to be parsed. If you only want a subset of events to be parse, pass their names as a list.
```python
# does not parse any event
gaze = EDFFile("test.edf", parse_events=None)

# parses all events
gaze = EDFFile("test.edf", parse_events="all")

# also parses all events, as default is parse_events="all"
gaze = EDFFile("test.edf")


# also parses all events, as all are included in the list
gaze = EDFFile("test.edf",
    parse_events=("saccades", "fixations", "blinks", "variables", "triggers", "aois"))

# only extracts gaze events: saccades, fixations, and blinks
gaze = EDFFile("test.edf", parse_events=("saccades", "fixations", "blinks"))
```

## Parsing variables
Trial variabels are recorded using messages in `!V TRIAL_VAR <variable> <value>` format. Note that _value_ can contain white spaces, but variable name cannot. For example, message `!V TRIAL_VAR Filename Face 01.png` will be parsed into `Filename="Face 01.png"`. If `wide_variables=True` (default), the library pivots table, so that each trial corrresponds to a single row with column `trial` and one column per variable. Note that the library does not attempt to guess column types, so all values are represented as strings. If `wide_variables=False` or there was an exception generated by pivot opeation, the table is in the long format with columns `trial`, `variable`, and `value`. 

## Parsing triggers
Triggers are custom messages with format `<trigger-marker> <label>`. The marker can be specified via `trigger_marker` parameter and its default value is `"TRIGGER"`. 

```python
gaze = EDFFile("test.edf", trigger_marker="TRIGGER")
```

The label can contain white space but marker cannot, so the label for the message `"TRIGGER Initial exposure"` will be `"Initial exposure"`. The triggers are stored in a table with columns `trial`,  `sttime`, `sttime_rel`, and `label`, see also [triggers](#triggers) output table.

## Parsing AOIs
Rectangular areas of interest are described via a message with format `"!V IAREA RECTANGLE <aoi_index> <left> <top> <right> <bottom> <label>"`, the `label` can contain white spaces. For output table details see [areas-of-interest](#areas-of-interest) table.


# EDFFile class

```{eval-rst}
.. autoclass:: eyelink_reader.EDFFile
   :members:
   :undoc-members:
   :inherited-members:
```

# Output tables

## Events
```{eval-rst}
.. autoclass:: eyelink_reader.edfdata.EDF_FEVENT
   :members:
   :noindex:
```

## Samples
```{eval-rst}
.. autoclass:: eyelink_reader.edfdata.EDF_FSAMPLE
   :members:
   :noindex:
```

## Recordings
```{eval-rst}
.. autoclass:: eyelink_reader.edfdata.EDF_RECORDINGS
   :members:
   :noindex:
```
## Saccades
Pandas table with following columns (see [Events](#events) for details on individual fields)

* **trial** : trial index
* **sttime** : saccade start time
* **sttime_rel** : saccade start time relative to the recording start
* **entime** : saccade end time
* **entime_rel** : saccade end time relative to the recording start
* **duration** : saccade duration
* **hstx** : Starting point of head reference (x-axis).
* **hsty**: Starting point of head reference (y-axis).
* **gstx** : Starting point of gaze (x-axis).
* **gsty** : Starting point of gaze (y-axis).
* **sta** : Pupil size at the start of the event.
* **henx** : Ending point of head reference (x-axis).
* **heny** : Ending point of head reference (y-axis).
* **genx** : Ending point of gaze (x-axis).
* **geny** : Ending point of gaze (x-axis).
* **ena** : Pupil size at the end of the event.
* **havx** : Average head reference (x-axis).
* **havy** : Average head reference (y-axis).
* **gavx** : Average gaze (x-axis).
* **gavy** : Average gaze (y-axis).
* **ava** : Average pupil size.
* **avel** : Accumulated average velocity.
* **pvel** : Accumulated peak velocity.
* **svel** : Start velocity.
* **evel** : End velocity.
* **supd_x** : Start units-per-degree on the x-axis.
* **eupd_x** : End units-per-degree on the x-axis.
* **supd_y** : Start units-per-degree on the y-axis.
* **eupd_y** : End units-per-degree on the y-axis.
* **eye** : Eye LEFT (0) or RIGHT (1)

## Fixations
Pandas table with following columns (see [Events](#events) for details on individual fields)

* **trial** : trial index
* **sttime** : fixation start time
* **sttime_rel** : fixation start time relative to the recording start
* **entime** : fixation end time
* **entime_rel** : fixation end time relative to the recording start
* **duration** : fixation duration
* **hstx** : Starting point of head reference (x-axis).
* **hsty**: Starting point of head reference (y-axis).
* **gstx** : Starting point of gaze (x-axis).
* **gsty** : Starting point of gaze (y-axis).
* **sta** : Pupil size at the start of the event.
* **henx** : Ending point of head reference (x-axis).
* **heny** : Ending point of head reference (y-axis).
* **genx** : Ending point of gaze (x-axis).
* **geny** : Ending point of gaze (x-axis).
* **ena** : Pupil size at the end of the event.
* **havx** : Average head reference (x-axis).
* **havy** : Average head reference (y-axis).
* **gavx** : Average gaze (x-axis).
* **gavy** : Average gaze (y-axis).
* **ava** : Average pupil size.
* **avel** : Accumulated average velocity.
* **pvel** : Accumulated peak velocity.
* **svel** : Start velocity.
* **evel** : End velocity.
* **supd_x** : Start units-per-degree on the x-axis.
* **eupd_x** : End units-per-degree on the x-axis.
* **supd_y** : Start units-per-degree on the y-axis.
* **eupd_y** : End units-per-degree on the y-axis.
* **eye** : Eye LEFT (0) or RIGHT (1)

## Blinks
Pandas table with following columns (see [Events](#events) for details on individual fields)

* **trial** : trial index
* **sttime** : blink start time
* **sttime_rel** : blink start time relative to the recording start
* **entime** : blink end time
* **entime_rel** : blink end time relative to the recording start
* **duration** : blink duration
* **eye** : Eye LEFT (0) or RIGHT (1)

## Variables
If `wide_variables=True` a Pandas table with columns `trial` and one column per variable. Note that the library does not attempt to guess column types, so all values are represented as strings. If `wide_variables=False` or there was an exception generated by pivot opeation, the table is in the long format with columns 

* **trial** : trial index
* **variable** : variable name
* **value** : value as string

## Triggers
Pandas table with columns

* **trial** : trial index
* **sttime** : trigger onset time time
* **sttime_rel** : trigger onset time relative to the recording start
* **label** : trigger label

## Areas-of-interest
Pandas table with columns

* **trial** : trial index
* **sttime** : saccade start time
* **sttime_rel** : saccade start time relative to the recording start
* **aoi_index** : AOI index
* **label** : AOI label
* **left** : left edge in screen coordinates
* **top** : top edge in screen coordinates
* **right** : right edge in screen coordinates
* **bottom** : bottom edge in screen coordinates
