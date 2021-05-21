import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib.figure import Figure


def create_stim_artists(app):

    dots = mpl.patches.Circle(app.p.aperture_pos,
                              app.p.aperture_size / 2,
                              fc="firebrick", lw=0,
                              alpha=.5,
                              animated=True)

    return dict(dots=dots)


def initialize_trial_figure(app):

    # Note that we use mpl.figure.Figure, not pyplot.figure
    fig = Figure((5, 5), dpi=100, facecolor="white")
    axes = [fig.add_subplot(3, 1, i) for i in range(1, 4)]

    axes[0].set(ylim=(-.1, 1.1),
                yticks=[0, 1],
                yticklabels=["No", "Yes"],
                ylabel="Responded")

    axes[1].set(ylim=(-.1, 1.1),
                yticks=[0, 1],
                yticklabels=["No", "Yes"],
                ylabel="Correct")

    axes[2].set(ylim=(0, None),
                xlabel="RT (s)")

    fig.subplots_adjust(.15, .125, .95, .95)

    return fig, axes


def update_trial_figure(app, trial_data):

    trial_data = pd.read_json(trial_data, typ="series")

    app.trial_data.append(trial_data)
    trial_df = pd.DataFrame(app.trial_data)

    resp_ax, cor_ax, rt_ax = app.axes

    # We are taking the approach of creating new artists on each trial,
    # drawing them, then removing them before adding the next trial's data.
    # Another approach would be to keep around references to the artists
    # and update their data using the appropriate matplotlib methods.

    resp_line, = resp_ax.plot(trial_df.trial, trial_df.responded, "ko")
    resp_ax.set(xlim=(.5, trial_df.trial.max() + .5))

    # Draw correct and incorrect responses, color by signed coherence
    dir_sign = dict(zip(app.remote_app.p.dot_dir, [-1, +1]))
    signed_coh = trial_df.dot_coh * trial_df.dot_dir.map(dir_sign)
    max_coh = max(app.remote_app.p.dot_coh)
    cor_line = cor_ax.scatter(
        trial_df.trial, trial_df.correct, c=signed_coh,
        vmin=-max_coh, vmax=+max_coh, cmap="coolwarm",
        linewidth=.5, edgecolor=".1",
    )
    cor_ax.set(xlim=(.5, trial_df.trial.max() + .5))

    # Draw a histogram of RTs
    bins = np.arange(0, 5.2, .2)
    heights, bins = np.histogram(trial_df.rt.dropna(), bins)
    rt_bars = rt_ax.bar(bins[:-1], heights, .2,
                        facecolor=".1", edgecolor="w", linewidth=.5)
    rt_ax.set(ylim=(0, heights.max() + 1))

    # Draw the canvas to show the new data
    app.fig_canvas.draw()

    # By removing the stimulus artists after drawing the canvas,
    # we are in effect clearing before drawing the new data on
    # the *next* trial.
    resp_line.remove()
    cor_line.remove()
    rt_bars.remove()
