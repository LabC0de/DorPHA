import math
import tkinter as tk
from itertools import cycle
from tkinter import ttk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec
from sklearn.preprocessing import MinMaxScaler

from dfextractions import df_extractions
from dfgc import df_gc, df_gc_stat
from dfhplc import df_hplc_results
from dfsamples import df_samples

matplotlib.use('TkAgg')


class Dataset:
    dataframes = {}
    cat_columns = {}
    num_columns = {}

    @staticmethod
    def set_df(name, df):
        Dataset.num_columns[name] = list(df.select_dtypes(include=[np.number]).columns.values)
        Dataset.cat_columns[name] = list(df.select_dtypes(exclude=[np.number]).columns.values)
        Dataset.dataframes[name] = df

    def __init__(self):
        df_extractions_raw = df_extractions
        self.set_df('Extraktionen', df_extractions_raw)

        df_samples_raw = df_samples
        self.set_df('Analytikproben', df_samples_raw)

        df_gc_results_raw = df_gc
        self.set_df('GC Ergebnisse', df_gc_results_raw)

        df_gc_results = df_gc_stat
        self.set_df('GC Ergebnisse (Stat)', df_gc_results)

        df_hplc_results_raw = df_hplc_results
        self.set_df('HPLC Ergebnisse', df_hplc_results_raw)

    @staticmethod
    def get_columns(*args, **kwargs):
        dfs = {}
        for arg in args:
            if arg is None:
                continue
            df, col = arg.split(': ')
            if df in dfs.keys():
                dfs[df].append(col)
            else:
                dfs[df] = ['Inhalt', 'Versuch', col]
        prefilter = {'ex': {}, 'in': {}}
        if "filter" in kwargs.keys():
            incl, excl = kwargs['filter'].get_rule()
            for key, vals in incl.items():
                df, col = key.split(': ')
                if df in prefilter['in'].keys():
                    prefilter['in'][df][col] = vals
                else:
                    prefilter['in'][df] = {col: vals}
            for key, vals in excl.items():
                df, col = key.split(': ')
                if df in prefilter['ex'].keys():
                    prefilter['ex'][df][col] = vals
                else:
                    prefilter['ex'][df] = {col: vals}
        dfs = sorted(dfs.items(), key=lambda item: Dataset.dataframes[item[0]].shape[0], reverse=True)
        ret = Dataset.dataframes[dfs[0][0]]
        if dfs[0][0] in prefilter['in'].keys():
            for col, vals in prefilter['in'][dfs[0][0]]:
                ret = ret[ret[col].isin(vals)]
                prefilter['in'].pop(dfs[0][0], None)
        elif dfs[0][0] in prefilter['ex'].keys():
            for col, vals in prefilter['ex'][dfs[0][0]]:
                ret = ret[~ret[col].isin(vals)]
                prefilter['ex'].pop(dfs[0][0], None)
        ret = ret[dfs[0][1]].dropna().set_index(['Versuch', 'Inhalt'])
        ret.columns = [f"{dfs[0][0]}: {col}" for col in ret.columns]
        for df, cols in dfs[1:]:
            tmp = Dataset.dataframes[df]
            if df in prefilter['in'].keys():
                for col, vals in prefilter['in'][df].items():
                    tmp = tmp[tmp[col].isin(vals)]
                    prefilter['in'].pop(df, None)
            if df in prefilter['ex'].keys():
                for col, vals in prefilter['ex'][df].items():
                    tmp = tmp[~tmp[col].isin(vals)]
                    prefilter['ex'].pop(df, None)
            tmp = tmp[cols].dropna().set_index(['Versuch', 'Inhalt'])
            tmp.columns = [f"{df}: {cl}" for cl in tmp.columns]
            ret = ret.merge(tmp, left_index=True, right_index=True)
        ret = ret.reset_index()
        for df, info in prefilter['in'].items():
            tmp = Dataset.dataframes[df]
            for col, values in info.items():
                tmp = tmp[tmp[col].isin(values)]
            ret = tmp[['Versuch', 'Inhalt']].merge(ret, left_on=['Versuch', 'Inhalt'], right_on=['Versuch', 'Inhalt'])
        for df, info in prefilter['ex'].items():
            tmp = Dataset.dataframes[df]
            for col, values in info.items():
                tmp = tmp[~tmp[col].isin(values)]
            ret = tmp[['Versuch', 'Inhalt']].merge(ret, left_on=['Versuch', 'Inhalt'], right_on=['Versuch', 'Inhalt'])
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, "display.width", 400):
            print(ret)
        ret = [ret[arg] if arg is not None else None for arg in list(args) + ['Versuch', 'Inhalt']]
        return ret

    @staticmethod
    def dict_o_lists_to_str(dict):
        acc = []
        for dataframe, columns in dict.items():
            for column in columns:
                acc.append(f"{dataframe}: {column}")
        return acc

    @staticmethod
    def get_numerical_columns():
        return Dataset.dict_o_lists_to_str(Dataset.num_columns)

    @staticmethod
    def get_categorical_columns():
        return Dataset.dict_o_lists_to_str(Dataset.cat_columns)


class Series:
    def __init__(self, title, master):
        self.master = master
        self.title = title
        self.row = 1
        self.frame = None
        self.button = None
        self.include = {}
        self.exclude = {}

    def get_rule(self):
        acc = {}
        exc = {}
        for flt in self.include.values():
            if flt[0] in acc.keys():
                acc[flt[0]].append(flt[1])
            else:
                acc[flt[0]] = [flt[1]]
        for flt in self.exclude.values():
            if flt[0] in exc.keys():
                exc[flt[0]].append(flt[1])
            else:
                exc[flt[0]] = [flt[1]]
        return acc, exc

    def set_filter(self, cb1, cb2, cb3):
        row = cb1.grid_info()['row']

        self.include.pop(row, None)
        self.exclude.pop(row, None)

        incl = cb1.get()
        dfcol = cb2.get()
        value = cb3.get()
        if len(incl) > 0 and len(dfcol) > 0 and len(value) > 0:
            if incl == 'inklusive':
                self.include[row] = (dfcol, value)
            elif incl == 'exklusive':
                self.exclude[row] = (dfcol, value)
            self.master.update()

    def load_options(self, event, cb1, cb2, cb3):
        df, col = event.widget.get().split(': ')
        cb3.set('')
        cb3.configure(values=list(Dataset.dataframes[df][col].unique()))
        self.set_filter(cb1, cb2, cb3)

    def __add_btn(self, frame, row):
        self.__add_filter(frame, row)
        self.row += 1

    def __add_filter(self, frame, row, include=None, dfcol=None, val=None):
        tk.Label(frame, text='Filter: ').grid(column=0, row=row, sticky='W')
        cb1 = ttk.Combobox(frame, values=['inklusive', 'exklusive', 'inaktiv'], width=8)
        cb1.grid(column=1, row=row)
        if include:
            cb1.set(include)
        cb3 = ttk.Combobox(frame, values=[], width=18)
        if val:
            cb3.set(val)
        cb3.grid(column=3, row=row)
        cb2 = ttk.Combobox(frame, values=Dataset.get_categorical_columns(), width=35)
        if dfcol:
            cb2.set(dfcol)
            df, col = dfcol.split(': ')
            cb3.configure(values=list(Dataset.dataframes[df][col].unique()))
        cb2.bind('<<ComboboxSelected>>', lambda event: self.load_options(event, cb1, cb2, cb3))
        cb2.grid(column=2, row=row)
        cb1.bind('<<ComboboxSelected>>', lambda event: self.set_filter(cb1, cb2, cb3))
        cb3.bind('<<ComboboxSelected>>', lambda event: self.set_filter(cb1, cb2, cb3))
        self.button.grid(column=0, row=self.row + 1, columnspan=4)

    def apply_gui(self, frame):
        self.frame = frame
        self.button = tk.Button(self.frame, width=50, text="+", command=lambda: self.__add_btn(self.frame, self.row))
        for i in range(self.row):
            if i in self.exclude.keys():
                dfcol, val = self.exclude[i]
                self.__add_filter(self.frame, i, 'exklusive', dfcol, val)
            elif i in self.include.keys():
                dfcol, val = self.include[i]
                self.__add_filter(self.frame, i, 'inklusive', dfcol, val)
            else:
                self.__add_filter(self.frame, i)


class SeriesManager:
    def __cb(self, exp):
        exp.destroy()
        self.is_open = False

    def __init__(self, master):
        self.master = master
        self.series = []
        self.options = Dataset.get_categorical_columns()
        self.is_open = False

    def add(self, title, tab_ctrl, is_new=True):
        tab1 = ttk.Frame(tab_ctrl)
        if is_new:
            if len(title) == 0:
                title = f"Reihe {len(self.series)}"
            self.series.append(Series(title, self.master))
            self.series[-1].apply_gui(tab1)
        else:
            title.apply_gui(tab1)
            title = title.title
        tab_ctrl.add(tab1, text=title)

    def open(self):
        if self.is_open:
            return
        exp = tk.Toplevel(self.master)
        exp.title(f"Reihenmanager {self.master.title}")
        exp.protocol("WM_DELETE_WINDOW", lambda: self.__cb(exp))
        exp.geometry("500x200")
        tab_ctrl = ttk.Notebook(exp)
        tab1 = ttk.Frame(tab_ctrl)
        tk.Label(tab1, text='Reihenname: ').grid(column=0, row=0, sticky='W')
        e1 = tk.Entry(tab1, width=30)
        e1.grid(column=1, row=0)
        tk.Label(tab1, text='Neuer Reihenfilter: ').grid(column=0, row=1, sticky='W')
        tk.Button(tab1, text="Add", width=28, command=lambda: self.add(e1.get(), tab_ctrl)).grid(column=1, row=1, sticky='W')
        tab_ctrl.add(tab1, text='+')
        for ser in self.series:
            self.add(ser, tab_ctrl, False)
        tab_ctrl.pack(expand=1, fill="both")
        self.is_open = True


class Scatter3DWindow(tk.Frame):
    scaler = MinMaxScaler((0, 20))
    c_scaler = MinMaxScaler((0, 1))

    def __get_filters(self):
        if len(self.series.series):
            return self.series.series
        return [None]

    def __get_columns(self, ser=None):
        if ser:
            return Dataset.get_columns(self.x_vals, self.y_vals, self.z_vals, self.c_vals, self.s_vals, filter=ser)
        return Dataset.get_columns(self.x_vals, self.y_vals, self.z_vals, self.c_vals, self.s_vals)

    def update(self):
        if self.x_vals and self.y_vals and self.z_vals:
            self.ax.cla()
            self.ax.set_xlabel(self.x_vals)
            self.ax.set_ylabel(self.y_vals)
            self.ax.set_zlabel(self.z_vals)
            self.ax._custom_label_data = {}
            markers = ['o', 'v', '^', '<', '>', '1', '2', '3', '4', '*', 'P', 'p', 's', 'X', 'D']
            if self.s_vals:
                s = Dataset.get_columns(self.s_vals)[0]
                self.scaler.fit(s.to_numpy().reshape(-1,1))
            for ser, marker in zip(self.__get_filters(), cycle(markers)):
                x, y, z, c, s, v, i = self.__get_columns(ser)
                title = "All"
                if ser:
                    title = ser.title
                if c is not None:
                    c = self.c_scaler.fit_transform(c.to_numpy().reshape(-1,1))
                if self.s_vals:
                    col = self.ax.scatter(xs=x, ys=y, zs=z, c=c, s=self.scaler.transform(s.to_numpy().reshape(-1, 1)), marker=marker, label=title)
                else:
                    col = self.ax.scatter(xs=x, ys=y, zs=z, c=c, marker=marker, label=title)
                self.ax._custom_label_data[col] = (v, i)
            self.ax.legend()
            self.ax.set_title(self.title)
            plt.show(block=False)

    def x_changed(self, event):
        self.x_vals = event.widget.get()
        self.update()

    def y_changed(self, event):
        self.y_vals = event.widget.get()
        self.update()

    def z_changed(self, event):
        self.z_vals = event.widget.get()
        self.update()

    def color_changed(self, event):
        self.c_vals = event.widget.get()
        if self.c_vals == 'None':
            self.c_vals = None
        self.update()

    def scale_changed(self, event):
        self.s_vals = event.widget.get()
        if self.s_vals == 'None':
            self.s_vals = None
        self.update()

    def err_changed(self, event):
        self.e_vals = event.widget.get()
        if self.e_vals == 'None':
            self.e_vals = None
        self.update()

    def __init__(self, parent, p_ax, title):
        tk.Frame.__init__(self, parent)
        self.ax = p_ax
        self.title = title
        self.x_vals = None
        self.y_vals = None
        self.z_vals = None
        self.c_vals = None
        self.s_vals = None
        self.e_vals = None
        self.series = SeriesManager(self)

        ttk.Label(self, text="X Parameter: ").grid(column=0, row=0, sticky='W')
        cb1 = ttk.Combobox(self, values=Dataset.get_numerical_columns(), width=30)
        cb1.bind('<<ComboboxSelected>>', self.x_changed)
        cb1.grid(column=1, row=0)

        ttk.Label(self, text="Y Parameter: ").grid(column=0, row=1, sticky='W')
        cb2 = ttk.Combobox(self, values=Dataset.get_numerical_columns(), width=30)
        cb2.bind('<<ComboboxSelected>>', self.y_changed)
        cb2.grid(column=1, row=1)

        ttk.Label(self, text="Z Ergebnis: ").grid(column=0, row=2, sticky='W')
        cb3 = ttk.Combobox(self, values=Dataset.get_numerical_columns(), width=30)
        cb3.bind('<<ComboboxSelected>>', self.z_changed)
        cb3.grid(column=1, row=2)

        ttk.Label(self, text="Fehlerbalken: ").grid(column=0, row=3, sticky='W')
        cb_4 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb_4.bind('<<ComboboxSelected>>', self.err_changed)
        cb_4.set('None')
        cb_4.grid(column=1, row=3)

        ttk.Label(self, text="Farbwert: ").grid(column=0, row=4, sticky='W')
        cb5 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb5.bind('<<ComboboxSelected>>', self.color_changed)
        cb5.set('None')
        cb5.grid(column=1, row=4)

        ttk.Label(self, text="Größenwert: ").grid(column=0, row=5, sticky='W')
        cb6 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb6.bind('<<ComboboxSelected>>', self.scale_changed)
        cb6.set('None')
        cb6.grid(column=1, row=5)

        ttk.Label(self, text="Reihenmanager: ").grid(column=0, row=6, sticky='W')
        tk.Button(self, text="Datenfilter", width=28, command=lambda: self.series.open()).grid(column=1, row=6)


class Scatter2DWindow(tk.Frame):
    scaler = MinMaxScaler((0, 20))

    def __get_filters(self):
        if len(self.series.series):
            return self.series.series
        return [None]

    def __get_columns(self, ser=None):
        if ser:
            return Dataset.get_columns(self.x_vals, self.y_vals, self.c_vals, self.s_vals, filter=ser)
        return Dataset.get_columns(self.x_vals, self.y_vals, self.c_vals, self.s_vals)

    def update(self):
        if self.x_vals and self.y_vals:
            self.ax.cla()
            self.ax.set_xlabel(self.x_vals)
            self.ax.set_ylabel(self.y_vals)
            self.ax._custom_label_data = {}
            markers = ['o', 'v', '^', '<', '>', '1', '2', '3', '4', '*', 'P', 'p', 's', 'X', 'D']
            if self.s_vals:
                s = Dataset.get_columns(self.s_vals)[0]
                self.scaler.fit(s.to_numpy().reshape(-1,1))
            for ser, marker in zip(self.__get_filters(), cycle(markers)):
                x, y, c, s, v, i = self.__get_columns(ser)
                title = "All"
                if ser:
                    title = ser.title
                if self.s_vals:
                    col = self.ax.scatter(x=x, y=y, c=c, s=self.scaler.transform(s.to_numpy().reshape(-1, 1)), marker=marker, label=title)
                else:
                    col = self.ax.scatter(x=x, y=y, c=c, marker=marker, label=title)
                self.ax._custom_label_data[col] = (v, i)
            self.ax.legend()
            self.ax.set_title(self.title)
            plt.show(block=False)

    def x_changed(self, event):
        self.x_vals = event.widget.get()
        self.update()

    def y_changed(self, event):
        self.y_vals = event.widget.get()
        self.update()

    def color_changed(self, event):
        self.c_vals = event.widget.get()
        if self.c_vals == 'None':
            self.c_vals = None
        self.update()

    def scale_changed(self, event):
        self.s_vals = event.widget.get()
        if self.s_vals == 'None':
            self.s_vals = None
        self.update()

    def err_changed(self, event):
        self.e_vals = event.widget.get()
        if self.e_vals == 'None':
            self.e_vals = None
        self.update()

    def __init__(self, parent, p_ax, title):
        tk.Frame.__init__(self, parent)
        self.ax = p_ax
        self.title = title
        self.x_vals = None
        self.y_vals = None
        self.c_vals = None
        self.s_vals = None
        self.e_vals = None
        self.series = SeriesManager(self)

        ttk.Label(self, text="X Parameter: ").grid(column=0, row=0, sticky='W')
        cb1 = ttk.Combobox(self, values=Dataset.get_numerical_columns() + Dataset.get_categorical_columns(), width=30)
        cb1.bind('<<ComboboxSelected>>', self.x_changed)
        cb1.grid(column=1, row=0)

        ttk.Label(self, text="Y Parameter: ").grid(column=0, row=1, sticky='W')
        cb2 = ttk.Combobox(self, values=Dataset.get_numerical_columns(), width=30)
        cb2.bind('<<ComboboxSelected>>', self.y_changed)
        cb2.grid(column=1, row=1)

        ttk.Label(self, text="Fehlerbalken: ").grid(column=0, row=2, sticky='W')
        cb_4 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb_4.bind('<<ComboboxSelected>>', self.err_changed)
        cb_4.set('None')
        cb_4.grid(column=1, row=2)

        ttk.Label(self, text="Farbwert: ").grid(column=0, row=3, sticky='W')
        cb5 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb5.bind('<<ComboboxSelected>>', self.color_changed)
        cb5.set('None')
        cb5.grid(column=1, row=3)

        ttk.Label(self, text="Größenwert: ").grid(column=0, row=4, sticky='W')
        cb6 = ttk.Combobox(self, values=['None'] + Dataset.get_numerical_columns(), width=30)
        cb6.bind('<<ComboboxSelected>>', self.scale_changed)
        cb6.set('None')
        cb6.grid(column=1, row=4)

        ttk.Label(self, text="Reihenmanager: ").grid(column=0, row=5, sticky='W')
        tk.Button(self, text="Datenfilter", width=28, command=lambda: self.series.open()).grid(column=1, row=5)


class HistogramWindow:
    def __init__(self):
        pass


class BarPlotWindow:
    def __init__(self):
        pass


class Filtertool:
    figures = []

    def __hover(self, evnt):
        if evnt.inaxes is None:
            return
        text = ""
        for idx, col in enumerate(evnt.inaxes.collections):
            cont, ind = col.contains(evnt)
            if cont:
                tup = evnt.inaxes._custom_label_data[col]
                text += str(pd.concat([tup[0], tup[1]], axis=1).iloc[ind['ind']])
        if text == "":
            return
        print(text)

    def __cb(self):
        pass

    def add_2d_scatter(self, notebook, title):
        n = len(self.figure.axes)
        x = (math.floor(math.sqrt(n))+1)
        gs = gridspec.GridSpec(nrows=x, ncols=x, figure=self.figure)
        for i, ax in enumerate(self.figure.axes):
            pos = gs[i // x, i % x].get_position(self.figure)
            ax.set_position(pos)
            ax.set_subplotspec(gs[i])
        ax = self.figure.add_subplot(gs[n // x, n % x])
        if len(title) == 0:
            title = "2D Scatter"
        title = f"{title} {len(Filtertool.figures)}"
        tab = Scatter2DWindow(notebook, ax, title)
        Filtertool.figures.append(tab)
        notebook.add(tab, text=title)
        plt.show()

    def add_3d_scatter(self, notebook, title):
        n = len(self.figure.axes)
        x = (math.floor(math.sqrt(n))+1)
        gs = gridspec.GridSpec(nrows=x, ncols=x, figure=self.figure)
        for i, ax in enumerate(self.figure.axes):
            pos = gs[i // x, i % x].get_position(self.figure)
            ax.set_position(pos)
            ax.set_subplotspec(gs[i])
        ax = self.figure.add_subplot(gs[n // x, n % x], projection='3d')
        if len(title) == 0:
            title = "3D Scatter"
        title = f"{title} {len(Filtertool.figures)}"
        tab = Scatter3DWindow(notebook, ax, title)
        Filtertool.figures.append(tab)
        notebook.add(tab, text=title)
        plt.show()

    def __init__(self, fig):
        self.figure = fig
        # fig.canvas.mpl_connect("motion_notify_event", self.__hover)

        self.exp = tk.Toplevel(self.figure.canvas.get_tk_widget())
        self.exp.title("Dora the Explorer")
        self.exp.geometry("300x200")
        self.exp.protocol("WM_DELETE_WINDOW", self.__cb)
        tab_ctrl = ttk.Notebook(self.exp)
        for tab in Filtertool.figures:
            print(tab.title)

        tab1 = ttk.Frame(tab_ctrl)
        tk.Label(tab1, text='Titel: ').grid(column=0, row=0, sticky='W')
        e1 = tk.Entry(tab1, width=30)

        tk.Label(tab1, text='2D Scatter Plot: ').grid(column=0, row=1, sticky='W')
        b0 = tk.Button(tab1, text="Add", width=30, command=lambda: self.add_2d_scatter(tab_ctrl, e1.get()))
        b0.grid(column=1, row=1, sticky='W')

        tk.Label(tab1, text='3D Scatter Plot: ').grid(column=0, row=2, sticky='W')
        b1 = tk.Button(tab1, text="Add", width=30, command=lambda: self.add_3d_scatter(tab_ctrl, e1.get()))
        b1.grid(column=1, row=2, sticky='W')

        tk.Label(tab1, text='Histogram: ').grid(column=0, row=3, sticky='W')
        tk.Button(tab1, text="Add", width=30).grid(column=1, row=3, sticky='W')

        tk.Label(tab1, text='Bar Plot: ').grid(column=0, row=4, sticky='W')
        tk.Button(tab1, text="Add", width=30).grid(column=1, row=4, sticky='W')

        tk.Label(tab1, text='Boxplot: ').grid(column=0, row=5, sticky='W')
        tk.Button(tab1, text="Add", width=30).grid(column=1, row=5, sticky='W')

        e1.grid(column=1, row=0)

        tab_ctrl.add(tab1, text='+')
        tab_ctrl.pack(expand=1, fill="both")


if __name__ == '__main__':
    fig = plt.figure(constrained_layout=True)
    data = Dataset()
    controll_panel = Filtertool(fig)
    plt.show()

