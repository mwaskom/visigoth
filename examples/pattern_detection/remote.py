import matplotlib as mpl


def create_stim_artists(remote):

    noise_kws = dict(fc="k", lw=0, alpha=.25, animated=True)
    noise_l = mpl.patches.Circle(remote.p.stim_pos[0],
                                 remote.p.stim_size / 2,
                                 **noise_kws)
    noise_r = mpl.patches.Circle(remote.p.stim_pos[1],
                                 remote.p.stim_size / 2,
                                 **noise_kws)

    pattern = mpl.patches.Circle((0, 0),
                                 remote.p.stim_size / 2,
                                 fc="r", lw=0, animated=True)

    return dict(noise_l=noise_l, noise_r=noise_r, pattern=pattern)
