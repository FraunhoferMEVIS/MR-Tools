import matplotlib.pyplot as plt
import numpy as np
import torch

from pypulseq.calc_rf_center import calc_rf_center
import math

import inspect

def who_called_me(_print=True):
    # inspect.stack()[0] is this frame, [1] is the caller
    caller_frame = inspect.stack()[2:6]
    if not _print:
        return caller_frame
    count = 0
    for c in caller_frame:
        caller_name  = c.function
        print(" "*count+f"I was called by: {caller_name}")
        count += 1

def flatten(matrix):
    return [item for row in matrix for item in row]

import numpy as np

def get_time_bounds(mr_data):
    """
    Returns (t_min, t_max) across all channels in mr_data.

    mr_data: dict of the form
      channel → { 't': np.ndarray, 'v': np.ndarray }
    """
    t_mins = []
    t_maxs = []
    for ch in mr_data.values():
        t = ch.get('t')
        if len(t):
            t_mins.append(min(t))
            t_maxs.append(max(t))

    if not t_mins:
        return 0,0,0
    _min,_max=min(t_mins), max(t_maxs)
    return _min,_max, _max-_min

def plot_kspace_trajectory(mrzeroseq, canvas,
                           plotting_dims: str = 'xy',
                           plot_timeline: bool = True, plot_trajectory: bool = True
                           ):
    """Plot the kspace trajectory produced by self.

    Parameters
    ----------
    kspace : list[Tensor]
        The kspace as produced by ``Sequence.get_full_kspace()``
    figsize : (float, float), optional
        The size of the plotted matplotlib figure.
    plotting_dims : string, optional
        String defining what is plotted on the x and y axis ('xy' 'zy' ...)
    plot_timeline : bool, optional
        Plot a second subfigure with the gradient components per-event.
    """
    assert len(plotting_dims) == 2
    assert plotting_dims[0] in ['x', 'y', 'z']
    assert plotting_dims[1] in ['x', 'y', 'z']
    dim_map = {'x': 0, 'y': 1, 'z': 2}

    # TODO: We could (optionally) plot which contrast a sample belongs to,
    # currently we only plot if it is measured or not

    kspace = mrzeroseq.get_full_kspace()
    adc_mask = [rep.adc_usage > 0 for rep in mrzeroseq]

    cmap = plt.get_cmap('rainbow')
    _ax = canvas.figure.subplots(1,plot_trajectory+plot_timeline)
    if (plot_trajectory^plot_timeline):
        _ax = [_ax]


    if plot_timeline:
        event = 0
        for i, rep_traj in enumerate(kspace):
            x = torch.arange(event, event + rep_traj.shape[0], 1)
            event += rep_traj.shape[0]

            if i == 0:
                _ax[0].plot(x, rep_traj[:, 0], c='r', label="$k_x$")
                _ax[0].plot(x, rep_traj[:, 1], c='g', label="$k_y$")
                _ax[0].plot(x, rep_traj[:, 2], c='b', label="$k_z$")
            else:
                _ax[0].plot(x, rep_traj[:, 0], c='r', label="_")
                _ax[0].plot(x, rep_traj[:, 1], c='g', label="_")
                _ax[0].plot(x, rep_traj[:, 2], c='b', label="_")
        _ax[0].set_xlabel("Event")
        _ax[0].set_ylabel("Gradient Moment")
        _ax[0].set_title("Gradient Moments over time")
        _ax[0].legend()
        _ax[0].grid()

    if plot_trajectory:
        for i, (rep_traj, mask) in enumerate(zip(kspace, adc_mask)):
            kx = rep_traj[:, dim_map[plotting_dims[0]]]
            ky = rep_traj[:, dim_map[plotting_dims[1]]]
    
            _ax[int(plot_timeline)].plot(kx, ky, c=cmap(i / len(kspace)))
            _ax[int(plot_timeline)].plot(kx[mask], ky[mask], 'r.')
            _ax[int(plot_timeline)].plot(kx[~mask], ky[~mask], 'k.')
        _ax[int(plot_timeline)].set_xlabel(f"$k_{plotting_dims[0]}$")
        _ax[int(plot_timeline)].set_ylabel(f"$k_{plotting_dims[1]}$")
        _ax[int(plot_timeline)].set_title("trajectory in k-space")
        _ax[int(plot_timeline)].grid()

    return _ax

import pypulseq as pp
import numpy as np

def convert_gradient_hz_per_m_to_mT_per_m(gradient_hz_per_m, gamma_hz_per_t=42.576e6):
    return (np.array(gradient_hz_per_m) / gamma_hz_per_t) * 1e4  # mT/m

def waveforms_export2(seq):
    # Extract time-resolved gradient data
    g = seq.get_gradients()
    waveform_dict = {
        'grx':  {'t': [], 'v': []},
        'gry':  {'t': [], 'v': []},
        'grz':  {'t': [], 'v': []},
        'rf':   {'t': [], 'v': []},
        'rf_am':{'t': [], 'v': []},
        'adc':  {'t': [], 'v': []},
    }

    g_max_t = 0
    # Gradient waveforms and common timebase
    for i, key in enumerate(['grx', 'gry', 'grz']):
        if g[i]:
            waveform_dict[key]['t'] = g[i].x
            waveform_dict[key]['v'] = convert_gradient_hz_per_m_to_mT_per_m(g[i](g[i].x))
            g_max_t = max(g_max_t,max(waveform_dict[key]['t']))

    # Re-simulate the sequence to find timed RF and ADC events
    t = 0.0
    for block_counter in range(len(seq.block_events)):
        block = seq.get_block(block_counter + 1)
        block_dur = seq.block_durations[block_counter+1]  # Accurate duration (accounts for gradients, rf, adc)

        # RF
        if hasattr(block, 'rf') and block.rf is not None and hasattr(block.rf, 'signal'):
            rf_signal = block.rf.signal
            n = len(rf_signal)
            dt = block.rf.t[1] - block.rf.t[0] if len(block.rf.t) > 1 else 1e-6  # safe fallback
            rf_time = np.arange(n) * dt + t
            waveform_dict['rf']['t'].extend(rf_time)
            waveform_dict['rf']['v'].extend(rf_signal)

        # ADC
        if hasattr(block, 'adc') and block.adc is not None:
            adc = block.adc
            n = adc.num_samples
            adc_time = np.arange(n) * adc.dwell + t + adc.delay
            waveform_dict['adc']['t'].extend(adc_time)
            waveform_dict['adc']['v'].extend([1.0] * n)

        t += block_dur  # move to time of next block

    # RF Amplitude
    waveform_dict['rf_am']['t'] = waveform_dict['rf']['t']
    waveform_dict['rf_am']['v'] = np.abs(waveform_dict['rf']['v'])
    
    # Convert to JSON-serializable lists
    return convert_ndarray_to_list(waveform_dict)

def waveforms_export(seq):
    gamma_hz_per_mt = 42.576e6  # Hz/T
    hz_per_m_to_mt_per_m = 1e6 / gamma_hz_per_mt  # Convert kHz/m → mT/m
    exported = seq.waveforms_export()
    
    def to_entry(t, v):
        return {'t': t.tolist(), 'v': v.tolist()}
    
    waveform_dict = {
        'grx': to_entry(exported['t_gx'], exported['gx'] * hz_per_m_to_mt_per_m),
        'gry': to_entry(exported['t_gy'], exported['gy'] * hz_per_m_to_mt_per_m),
        'grz': to_entry(exported['t_gz'], exported['gz'] * hz_per_m_to_mt_per_m),
        'rf':  to_entry(exported['t_rf'], exported['rf']),
        'rf_am': to_entry(exported['t_rf'], np.abs(exported['rf'])),
        'adc': to_entry(exported['t_adc'], exported['adc']),
    }

    return waveform_dict

def convert_ndarray_to_list(obj):
    if isinstance(obj, dict):
        return {k: convert_ndarray_to_list(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray_to_list(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        # Convert ndarray to list and recursively process each element
        return convert_ndarray_to_list(obj.tolist())
    elif isinstance(obj, complex) or isinstance(obj, np.complexfloating):
        return {'real': obj.real, 'imag': obj.imag}
    else:
        return obj

class SafeDict(dict):
    def __missing__(self, key):
        return f"<{key}>"

import json
def extract_parameters_form_pulseq(filename):
    """
    Read `filename`, find the lines between 
      "# PARAMETERS_JSON_START" and "# PARAMETERS_JSON_END",
    strip off the leading "# ", join them, and json.loads them.
    Returns a Python dict (e.g. {"parameters": { ... }}).
    """
    in_block = False
    json_lines = []

    with open(filename, 'r') as f:
        for raw in f:
            line = raw.rstrip("\n")

            # 1) Detect start marker
            if not in_block and line.strip() == "# PARAMETERS_JSON_START":
                in_block = True
                continue

            # 2) While inside, collect lines until the end marker
            if in_block:
                if line.strip() == "# PARAMETERS_JSON_END":
                    in_block = False
                    break
                # Each JSON line starts with "#". Remove that and any following space:
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    content = stripped[1:]
                    if content.startswith(" "):
                        content = content[1:]
                    json_lines.append(content)

    if not json_lines:
        return {}
    
    # Join into one JSON string
    json_text = "\n".join(json_lines)
    try:
        params = json.loads(json_text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON parameters: {e}")

    return params

import re
from pathlib import Path

def update_pulseqfile(infile: Path, outfile: Path, parameter_values: dict,systemInfo=None):
    """
    Reads a Pulseq .seq file, removes any PARAMETERS_JSON block,
    finds all placeholders enclosed in {…}, evaluates each placeholder
    expression with the given parameter_values, and writes the updated
    text to outfile.

    - infile: Path to the original .seq template.
    - outfile: Path where the filled .seq should be written.
    - parameter_values: dict mapping names → numeric values (or any types
      usable inside eval).
    """
    infile = Path(infile)
    outfile=Path(outfile)
    # 1) Read entire file as text
    text = infile.read_text(encoding="utf-8")

    # 2) Remove the PARAMETERS_JSON block
    lines = text.splitlines(keepends=True)
    cleaned_lines = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if not in_block and stripped == "# PARAMETERS_JSON_START":
            in_block = True
            continue
        if in_block and stripped == "# PARAMETERS_JSON_END":
            in_block = False
            continue
        if not in_block:
            cleaned_lines.append(line)
    cleaned_text = "".join(cleaned_lines)

    # 3) Replace each {placeholder} by eval(placeholder, {}, parameter_values)
    #    Using a regex substitution with a callback:
    pattern = re.compile(r"\{([^{}]+)\}")
    for k,v in parameter_values.items():
        parameter_values.update({k:eval(str(v), {}, parameter_values)})

    def repl(match):
        expr = match.group(1).strip()  # the text inside {…}, e.g. "gradZ" or "-2*gradZ"
        try:
            # Evaluate in a namespace where only parameter_values are available
            val = eval(expr, {}, parameter_values)
        except Exception as e:
            raise RuntimeError(f"Failed to evaluate '{{{expr}}}': {e}")
        return str(val)

    result_text = pattern.sub(repl, cleaned_text)

    # 4) Write the resulting text to outfile
    outfile.write_text(result_text, encoding="utf-8")
    outfile.with_name(str(parameter_values.get('delay',0))+'_'+str(outfile.name)).write_text(result_text, encoding="utf-8")
    if systemInfo is not None:
        _pulseq = pp.Sequence(systemInfo)
        _pulseq.read(outfile,detect_rf_use=False)
        return _pulseq
        
def make_icon(plot,name, data,value_dict,**kwargs):
    from Plot import Plot
    if not plot:
        plot = Plot(visMode='icon_mode', showModules=False, showGUI=False, width=kwargs.get('width',3), height=kwargs.get('height',2),
                                 autoUpdate=False, noContext=True, noLegend=True, noAxis=True)

    plot.setBackgroundColor(kwargs.get('_type',''))
    if kwargs.get('showInfoBlock') and len(value_dict):
        infoBlock = True
    else:
        infoBlock = False
    plot._update_canvas(data=data,fixRfScaling=40.0,fixGradientScaling=25.0,infoBlock=infoBlock)
    if value_dict.get('rf_amp'):
        plot.annotate_flip_phase(value_dict['rf_amp'], value_dict.get('rf_phase',0))
    else:
        plot.annotate_flip_phase()
    if value_dict.get('gradX_amp') or value_dict.get('gradY_amp') or value_dict.get('gradZ_amp'):
        plot.annotate_gradients((value_dict.get('gradX_amp',0),value_dict.get('gradY_amp',0),value_dict.get('gradZ_amp',0),))
    else:
        plot.annotate_gradients()
        
    fname = str(str(kwargs.get('_dir','temp/'))+'\\'+name)
    plot.saveFigure(fname)
    return fname+'.svg'
    
