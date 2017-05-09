import tkinter as tk
from data_reader import DataAcquisition


INDICATOR_FONT = ("Consolas", 38)
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
        self._len_var = FormatVar('No.: {:n}')
        self._len_var.set('No. of Samples')

        self._reading_label = tk.Label(
            self, textvariable=self._reading_var, font=INDICATOR_FONT, width=15
        )
        self._mean_label = tk.Label(
            self, textvariable=self._mean_var, font=INDICATOR_FONT, width=15
        )
        self._std_label = tk.Label(
            self, textvariable=self._std_var, font=INDICATOR_FONT, width=15
        )
        self._len_label = tk.Label(
            self, textvariable=self._len_var, font=INDICATOR_FONT, width=15
        )

        button_frame = tk.Frame(self, pady=20)
        self._start_button = tk.Button(
            button_frame, text='start', command=self._start_collectiong_evt,
            font=BUTTON_FONT
        )
        self._pause_button = tk.Button(
            button_frame, text='pause', command=self._pause_collecting_evt,
            font=BUTTON_FONT
        )

        self._update_sched = None

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


    def cleanup(self):
        pass



root = None
data_acq = DataAcquisition()
mean_disp = None
value_disp = None
std_disp = None
len_disp = None
scheduled_update_id = None


def update():
    global scheduled_update_id
    if not data_reader.is_running():
        scheduled_update_id = None
        return
    val = data_reader.get_last_value()
    value_disp.config(text='Current: %.4f' % val)
    mean = data_reader.get_mean()
    mean_disp.config(text='Mean: %.4f' % mean)
    std = data_reader.get_std()
    std_disp.config(text='Std: %.4g' % std)
    len_disp.config(text='N = %u' % data_reader.len)
    scheduled_update_id = root.after(500, update)


def main():
    global root, mean_disp, value_disp, std_disp, len_disp, stop_button
    root = tk.Tk()
    frame = tk.Frame(root, padx=50, pady=25, width=1000)
    frame.pack()

    value_disp = tk.Label(
        frame, text='Current Value', font=("Consolas", 38), width=15
    )
    value_disp.pack(fill=None, expand=False)

    mean_disp = tk.Label(
        frame, text='Mean Value', font=("Consolas", 38), width=15
    )
    mean_disp.pack(fill=None, expand=False)

    std_disp = tk.Label(
        frame, text='Std Value', font=("Consolas", 38), width=15
    )
    std_disp.pack(fill=None, expand=False)

    
    len_disp = tk.Label(
        frame, text='N = 0', font=("Consolas", 38), width=15
    )
    len_disp.pack(fill=None, expand=False)

    button_frame = tk.Frame(frame, pady=20)


    def start_collecting():
        start_button.config(command=stop_collecting, text='stop')
        pause_button.config(state=tk.NORMAL, text='pause', command=pause_collecting)
        data_reader.start_new()
        if scheduled_update_id is None:
            update()

    def stop_collecting():
        start_button.config(command=start_collecting, text='start')
        pause_button.config(state=tk.DISABLED, text='pause', command=pause_collecting)
        data_reader.stop()
                          
    start_button = tk.Button(
        button_frame, text='start', command=start_collecting,
        font=("sans-serif", 20)
    )
    start_button.pack(side=tk.LEFT, expand=True, fill='x')

    def pause_collecting():
        pause_button.config(command=resume_collecting, text='resume')
        data_reader.pause()

    def resume_collecting():
        pause_button.config(command=pause_collecting, text='pause')
        data_reader.resume()
        if scheduled_update_id is None:
            update()

    pause_button = tk.Button(
        button_frame, text='pause', command=pause_collecting,
        font=("sans-serif", 20), state=tk.DISABLED
    )
    pause_button.pack(side=tk.LEFT, expand=True, fill='x')
    button_frame.pack(fill='x', expand=True)

    root.mainloop()
    if scheduled_update_id is not None:
        root.after_cancel(scheduled_update_id)
    data_reader.stop()
    try: root.destroy()
    except tk.TclError: pass

main()
