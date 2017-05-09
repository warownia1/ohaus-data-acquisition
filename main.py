import tkinter as tk
from data_reader import DataAcquisition


INDICATOR_FONT = ("Consolas", 25)
BUTTON_FONT = ("sans-serif", 20)


class FormatVar(tk.StringVar):

    def __init__(self, strf, *args, **kwargs):
        """
        :param str strf: string with placeholders 
        :param args: args passed to the StringVar
        :param kwargs: kwargs passed to the StringVar
        """
        super(FormatVar, self).__init__(*args, **kwargs)
        self._strf = strf

    def format(self, *args, **kwargs):
        """
        Sets the value of the variable to a nwe text with new format variables.
        :param args: args passed to the str.format function  
        :param kwargs: kwargs passed to the str.format function
        """
        self.set(self._strf.format(*args, **kwargs))


class Application(tk.Frame):

    def __init__(self, master):
        super(Application, self).__init__(master, padx=50, pady=25, width=1000)

        self._reading_var = FormatVar('Current: {:.4f}')
        self._reading_var.set('Current Reading')
        self._mean_var = FormatVar('Mean: {:.4f}')
        self._mean_var.set('Mean Value')
        self._std_var = FormatVar('St. Dev.: {:.4g}')
        self._std_var.set('Standard Dev.')
        self._len_var = FormatVar('No. samples: {:n}')
        self._len_var.set('No. of Samples')

        self._reading_label = tk.Label(
            self, textvariable=self._reading_var, font=INDICATOR_FONT, width=20
        )
        self._mean_label = tk.Label(
            self, textvariable=self._mean_var, font=INDICATOR_FONT, width=20
        )
        self._std_label = tk.Label(
            self, textvariable=self._std_var, font=INDICATOR_FONT, width=20
        )
        self._len_label = tk.Label(
            self, textvariable=self._len_var, font=INDICATOR_FONT, width=20
        )

        button_frame = tk.Frame(self, pady=15)
        self._start_button = tk.Button(
            button_frame, text='start', command=self._start_collectiong_evt,
            font=BUTTON_FONT
        )
        self._pause_button = tk.Button(
            button_frame, text='pause', command=self._pause_collecting_evt,
            font=BUTTON_FONT, state=tk.DISABLED
        )
        self._start_button.pack(side=tk.LEFT, expand=True, fill='x')
        self._pause_button.pack(side=tk.LEFT, expand=True, fill='x')

        self._reading_label.pack()
        self._mean_label.pack()
        self._std_label.pack()
        self._len_label.pack()
        button_frame.pack(fill='x')

        self._update_sched = None
        self._data_acq = DataAcquisition()

        self.pack()

    def _start_collectiong_evt(self):
        self._start_button.config(command=self._stop_collecting_evt, text='stop')
        self._pause_button.config(state=tk.NORMAL, text='pause',
                                  command=self._pause_collecting_evt)
        self._data_acq.start()
        if self._update_sched is None:
            self._update()

    def _stop_collecting_evt(self):
        self._start_button.config(command=self._start_collectiong_evt, text='start')
        self._pause_button.config(state=tk.DISABLED, text='pause',
                                  command=self._pause_collecting_evt)
        self._data_acq.pause()

    def _pause_collecting_evt(self):
        self._pause_button.config(command=self._resume_collecting_evt, text='resume')
        self._data_acq.pause()

    def _resume_collecting_evt(self):
        self._pause_button.config(command=self._pause_collecting_evt, text='pause')
        self._data_acq.resume()
        if self._update_sched is None:
            self._update()

    def _update(self):
        if not self._data_acq.is_running():
            self._update_sched = None
            return
        self._reading_var.format(self._data_acq.last_value)
        self._mean_var.format(self._data_acq.get_mean())
        self._std_var.format(self._data_acq.get_std())
        self._len_var.format(self._data_acq.len)
        self._update_sched = self.after(200, self._update)

    def cleanup(self):
        self._data_acq.dispose()


if __name__ == '__main__':
    root = tk.Tk()
    frame = Application(root)
    root.mainloop()
    frame.cleanup()
    try:
        root.destroy()
    except tk.TclError:
        pass
