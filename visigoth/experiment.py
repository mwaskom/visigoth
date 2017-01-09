

class Experiment(object):

    def __init__(self):

        self.p = None
        self.s = None
        self.win = None
        self.tracker = None
        self.server = None

        self.trial_data = []

    def run(self):

        # Everything is wrapped in a try-block so that errors will exit out
        # properly and not destroy data or leave hanging connections.

        try:

            # Experiment initialization

            self.create_output_directory()
            self.load_params()
            self.initialize_server()
            self.initialize_eyetracker()
            self.open_window()
            self.create_stimuli()

            # Main experimental loop

            for trial_info in self.generate_trials():

                trial_info = self.run_trial(trial_info)
                self.trial_data.append(trial_info)
                self.update_client(trial_info)

        finally:

            # Experiment shutdown

            self.shutdown_server()
            self.shutdown_eyetracker()
            self.save_data()
            self.close_window()

    # ==== Study-specific functions ====

    def create_stimuli(self):
        """Initialize study-specific stimulus objects.

        This method must be defined for each study.

        It should return a dictionary that maps stimulus names to the objects
        themselves. The objects can be anything that follow the basic stimulus
        API--namely, they need to define a ``draw`` method. They will end up
        in the Experiment.s namespace. Some stimuli (e.g. the fixation point)
        have default objects but can be overloaded here.

        """
        raise NotImplementedError

    def generate_trials(self):
        """Generator that yields data for each trial.

        This method must be defined for each study.

        It should be written as a generator, which allows flexibility as to
        whether the trial information will be fully defined before the run
        or on the fly.

        It should yield an object that provides trial-specific parameters.
        This will typically be a pandas Series, but other datatypes are fine
        as long as the ``run_trial`` method knows how to handle it.

        The generator is iterated between each trial, so if it is going to do
        substantial computation, you will need to be mindful to specify a
        sufficient ITI distribution.

        """
        raise NotImplementedError

    def run_trial(self, trial_info):
        """Execute an individual trial of the experiment.

        This method must be defined for each study.

        It should accept a trial_info argument and return the object, possibly
        with updated values or additional data. This can be any type of object
        but it should be coordinated with the other methods. Specifically, the
        handling of the input should correspond with what is yielded by the
        ``generate_trials`` method, and the output should be something that the
        ``update_client`` and ``save_data`` methods knows how to handle. It is
        easiest for this to be a pandas Series, so that those methods do not
        need to be overloaded, but this is not strictly required to allow for
        more complicated designs.

        """
        raise NotImplementedError

    def update_client(self, trial_info):
        """Send the trial results to the experiment client.

        If the object returned by ``run_trial`` is a pandas Series, it's not
        necessary to overload this function. Howver, it can be defined for each
        study to allow for more complicated data structures.

        """
        raise NotImplementedError

    def save_data(self):
        """Write out data files at the end of the run.

        If the object returned by ``run_trial`` is a pandas Series and you
        don't want to do anything special at the end of the experiment, it's
        not necessary to overload this function. Howver, it can be defined for
        each study to allow for more complicated data structures or exit logic.

        """
        raise NotImplementedError

    # ==== Initialization functions ====

    def load_params(self):
        """Determine parameters for this run of the experiment."""
        pass

    def create_output_directory(self):
        """Ensure that the outputs can be written."""
        pass

    def initialize_server(self):
        """Start a server in an independent thread for experiment control."""
        pass

    def initialize_eyetracker(self):
        """Connect to and calibrate eyetracker."""
        pass

    def open_window(self):
        """Open the PsychoPy window to begin the experiment."""
        pass

    # ==== Shutdown functions ====

    def shutdown_server(self):
        """Cleanly close down the experiment server process."""
        if self.server is None:
            return

    def shutdown_eyetracker(self):
        """End Eyetracker recording and transfer EDF file."""
        if self.tracker is None:
            return

    def close_window(self):
        """Cleanly exit out of the psychopy window."""
        pass
