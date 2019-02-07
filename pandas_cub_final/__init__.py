import numpy as np

__version__ = '0.0.1'


DTYPE_NAME = {'O': 'string', 'i': 'int', 'f': 'float', 'b': 'bool'}


class DataFrame:

    def __init__(self, data):
        """
        A DataFrame holds two-dimensional heterogeneous data. Create it by
        passing a dictionary of NumPy arrays to the values parameter

        Parameters
        ----------
        values: dict
            A dictionary of strings mapped to NumPy arrays. The key will
            become the column name.
        """

        # Holds the data
        self._data = data

        # check for correct input types
        self._check_input_types()

        # check for equal array lengths
        self._check_array_lengths()

        # convert unicode arrays to object
        self._convert_unicode_to_object()

        # Allow for special methods for strings
        self.str = StringMethods(self)
        self._add_docs()

    def _check_input_types(self):
        if not isinstance(self._data, dict):
            raise TypeError("`data` must be a dictionary of 1-D NumPy arrays")

        for col_name, values in self._data.items():
            if not isinstance(col_name, str):
                raise TypeError('All column names must be a string')
            if not isinstance(values, np.ndarray):
                raise TypeError('All values must be a 1-D NumPy array')
            else:
                if values.ndim != 1:
                    raise ValueError('Each value must be a 1-D NumPy array')
    
    def _check_array_lengths(self):
        for i, values in enumerate(self._data.values()):
            if i == 0:
                length = len(values)
            if length != len(values):
                raise ValueError('All values must be the same length')

    def _convert_unicode_to_object(self):
        for col_name, values in self._data.items():
            if values.dtype.kind == 'U':
                self._data[col_name] = values.astype('O')

    def __len__(self):
        """
        Make the builtin len function work with our dataframe

        Returns
        -------
        int: the number of rows in the dataframe
        """
        return len(next(iter(self._data.values())))

    @property
    def columns(self):
        """
        _data holds column names mapped to arrays
        take advantage of internal ordering of dictionaries to
        put columns in correct order in list. Only works in 3.6+

        Returns
        -------
        list of column names
        """
        return list(self._data)

    @columns.setter
    def columns(self, columns):
        """
        Must supply a list of columns as strings the same length
        as the current DataFrame

        Parameters
        ----------
        columns: list of strings

        Returns
        -------
        Nones
        """
        if not isinstance(columns, list):
            raise TypeError('New columns must be a list')
        if len(columns) != len(self.columns):
            raise ValueError(f'New column length must be {len(self.columns)}')
        else:
            for col in columns:
                if not isinstance(col, str):
                    raise TypeError('New column names must be strings')
        if len(columns) != len(set(columns)):
            raise ValueError('Column names must be unique')

        new_data = {}
        # code here
        for col, values in zip(columns, self._data.values()):
            new_data[col] = values

        self._data = new_data

    @property
    def shape(self):
        """

        Returns
        -------
        two-item tuple of number of rows and columns
        """
        return len(self), len(self.columns)

    def _repr_html_(self):
        """
        Used to create a string of HTML to nicely display the DataFrame
        in a Jupyter Notebook. Different string formatting is used for
        different data types.

        The structure of the HTML is as follows:
        <table>
            <thead>
                <tr>
                    <th>data</th>
                    ...
                    <th>data</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>{i}</strong></td>
                    <td>data</td>
                    ...
                    <td>data</td>
                </tr>
                ...
                <tr>
                    <td><strong>{i}</strong></td>
                    <td>data</td>
                    ...
                    <td>data</td>
                </tr>
            </tbody>
        <table>
        """
        html = '<table><thead><tr><th></th>'
        for col in self.columns:
            html += f"<th>{col:10}</th>"

        html += '</tr></thead>'
        html += "<tbody>"

        only_head = False
        num_head = 10
        num_tail = 10
        if len(self) <= 20:
            only_head = True
            num_head = len(self)

        for i in range(num_head):
            html += f'<tr><td><strong>{i}</strong></td>'
            for col, values in self._data.items():
                kind = values.dtype.kind
                if kind == 'f':
                    html += f'<td>{values[i]:10.3f}</td>'
                elif kind == 'b':
                    html += f'<td>{values[i]}</td>'
                elif kind == 'O':
                    v = values[i]
                    if v is None:
                        v = 'None'
                    html += f'<td>{v:10}</td>'
                else:
                    html += f'<td>{values[i]:10}</td>'
            html += '</tr>'

        if not only_head:
            html += '<tr><strong><td>...</td></strong>'
            for i in range(len(self.columns)):
                html += '<td>...</td>'
            html += '</tr>'
            for i in range(-num_tail, 0):
                html += f'<tr><td><strong>{len(self) + i}</strong></td>'
                for col, values in self._data.items():
                    kind = values.dtype.kind
                    if kind == 'f':
                        html += f'<td>{values[i]:10.3f}</td>'
                    elif kind == 'b':
                        html += f'<td>{values[i]}</td>'
                    elif kind == 'O':
                        v = values[i]
                        if v is None:
                            v = 'None'
                        html += f'<td>{v:10}</td>'
                    else:
                        html += f'<td>{values[i]:10}</td>'
                html += '</tr>'

            html += '</tbody></table>'
        return html

    @property
    def values(self):
        """
        Returns
        -------
        A single 2D NumPy array of the underlying data
        """
        return np.column_stack(self._data.values())

    @property
    def dtypes(self):
        """
        Returns
        -------
        A two-column DataFrame of column names in a column and
        their data type in the other
        """
        col_arr = np.array(self.columns)
        dtypes = []
        for values in self._data.values():
            kind = values.dtype.kind
            dtype = DTYPE_NAME[kind]
            dtypes.append(dtype)

        return DataFrame({'Column Name': col_arr, 'Data Type': np.array(dtypes)})

    def __getitem__(self, item):
        """
        Use the brackets operator to simultaneously select rows and columns

        A single string selects one column -> df['colname']
        A list of strings selects multiple columns -> df[['colname1', 'colname2']]
        A one column DataFrame of booleans that filters rows -> df[df_bool]

        Row and column selection simultaneously -> df[rs, cs]
            where cs and rs can be integers, slices, or a list of integers
            rs can also be a one-column boolean DataFrame

        Returns
        -------
        A subset of the original DataFrame
        """
        # select a single column -> df['colname']
        if isinstance(item, str):
            return DataFrame({item: self._data[item]})

        # select multiple columns -> df[['colname1', 'colname2']]
        if isinstance(item, list):
            return DataFrame({col: self._data[col] for col in item})

        # boolean selection
        if isinstance(item, DataFrame):
            if item.shape[1] != 1:
                raise ValueError('Can only pass a one column DataFrame for selection')

            bool_arr = next(iter(item._data.values()))
            if bool_arr.dtype.kind != 'b':
                raise TypeError('DataFrame must be a boolean')

            new_data = {}
            for col, values in self._data.items():
                new_data[col] = values[bool_arr]
            return DataFrame(new_data)

        if isinstance(item, tuple):
            return self._getitem_tuple(item)
        else:
            raise TypeError('Select with either a string, a list, or a row and column '
                            'simultaneous selection')

    def _getitem_tuple(self, item):
        # simultaneous selection of rows and cols -> df[rs, cs]
        if len(item) != 2:
            raise ValueError('Pass either a single string or a two-item tuple inside the '
                                'selection operator.')
        row_selection = item[0]
        col_selection = item[1]
        if isinstance(row_selection, int):
            row_selection = [row_selection]
        elif isinstance(row_selection, DataFrame):
            if row_selection.shape[1] != 1:
                raise ValueError('Can only pass a one column DataFrame for selection')
            row_selection = next(iter(row_selection._data.values()))
            if row_selection.dtype.kind != 'b':
                raise TypeError('DataFrame must be a boolean')
        elif not isinstance(row_selection, (list, slice)):
            raise TypeError('Row selection must be either an int, slice, list, or DataFrame')

        if isinstance(col_selection, int):
            col_selection = [self.columns[col_selection]]
        elif isinstance(col_selection, str):
            col_selection = [col_selection]
        elif isinstance(col_selection, list):
            new_col_selction = []
            for col in col_selection:
                if isinstance(col, int):
                    new_col_selction.append(self.columns[col])
                else:
                    new_col_selction.append(col)
            col_selection = new_col_selction
        elif isinstance(col_selection, slice):
            start = col_selection.start
            stop = col_selection.stop
            step = col_selection.step
            if isinstance(start, str):
                start = self.columns.index(col_selection.start)
            if isinstance(stop, str):
                stop = self.columns.index(col_selection.stop) + 1

            col_selection = self.columns[start:stop:step]
        else:
            raise TypeError('Column selection must be either an int, string, list, or slice')

        new_data = {}
        for col in col_selection:
            new_data[col] = self._data[col][row_selection]
        return DataFrame(new_data)


    def _ipython_key_completions_(self):
        # allows for tab completion when doing df['c
        return self.columns

    def __setitem__(self, key, value):
        # adds a new column or a overwrites an old column
        if not isinstance(key, str):
            raise NotImplementedError('Only able to set a single column')

        if isinstance(value, np.ndarray):
            if value.ndim != 1:
                raise ValueError('Setting array must be 1D')
            if len(value) != len(self):
                raise ValueError('Setting array must be same length as DataFrame')
        elif isinstance(value, DataFrame):
            if value.shape[1] != 1:
                raise ValueError('Setting DataFrame must be one column')
            if len(value) != len(self):
                raise ValueError('Setting and Calling DataFrames must be the same length')
            value = next(iter(value._values))
        elif isinstance(value, (int, str, float, bool)):
            value = np.repeat(value, len(self))
        else:
            raise TypeError('Setting value must either be a numpy array, '
                            'DataFrame, integer, string, float, or boolean')

        if value.dtype.kind == 'U':
            value = value.astype('O')

        self._data[key] = value

    def head(self, n=5):
        """
        Return the first n rows

        Parameters
        ----------
        n: int

        Returns
        -------
        DataFrame
        """
        return self[:n, :]

    def tail(self, n=5):
        """
        Return the last n rows

        Parameters
        ----------
        n: int

        Returns
        -------
        DataFrame
        """
        return self[-n:, :]

    #### AGGREGATION FUNCTIONS ####

    def min(self):
        return self._agg(np.min)

    def max(self):
        return self._agg(np.max)

    def mean(self):
        return self._agg(np.mean)

    def median(self):
        return self._agg(np.median)

    def sum(self):
        return self._agg(np.sum)

    def var(self):
        return self._agg(np.var)

    def std(self):
        return self._agg(np.std)

    def all(self):
        return self._agg(np.all)

    def any(self):
        return self._agg(np.any)

    def argmax(self):
        return self._agg(np.argmax)

    def argmin(self):
        return self._agg(np.argmin)

    def _agg(self, aggfunc):
        """
        Generic aggregation function that applies the
        aggregation to each column

        Parameters
        ----------
        aggfunc: str of the aggregation function name in NumPy

        Returns
        -------
        A DataFrame
        """
        new_data = {}
        for col, values in self._data.items():
            try:
                val = aggfunc(values)
            except TypeError:
                continue
            new_data[col] = np.array([val])
        return DataFrame(new_data)

    def isna(self):
        """
        Determines whether each value in the DataFrame is missing or not

        Returns
        -------
        A DataFrame of booleans the same size as the calling DataFrame
        """
        new_data = {}
        for col, values in self._data.items():
            kind = values.dtype.kind
            if kind == 'O':
                new_data[col] = values == None
            else:
                new_data[col] = np.isnan(values)
        return DataFrame(new_data)

    def count(self):
        """
        Counts the number of non-missing values per column

        Returns
        -------
        A DataFrame
        """
        new_data = {}
        df = self.isna()
        length = len(self)
        for col, values in df._data.items():
            val = length - values.sum()
            new_data[col] = np.array([val])
        return DataFrame(new_data)

    def unique(self):
        """
        Finds the unique values of each column

        Returns
        -------
        A list of one-column DataFrames
        """
        dfs = []
        for col, values in self._data.items():
            uniques = np.unique(values)
            dfs.append(DataFrame({col: uniques}))
        if len(dfs) == 1:
            return dfs[0]
        return dfs

    def nunique(self):
        """
        Find the number of unique values in each column

        Returns
        -------
        A DataFrame
        """
        dfs = self.unique()
        if isinstance(dfs, DataFrame):
            dfs = [dfs]

        new_data = {}
        for df, col in zip(dfs, self.columns):
            new_data[col] = np.array([len(df)])

        return DataFrame(new_data)

    def value_counts(self, normalize=False):
        """
        Returns the frequency of each unique value for each column

        Parameters
        ----------
        normalize: bool
            If True, returns the relative frequencies (percent)

        Returns
        -------
        A list of DataFrames or a single DataFrame if one column
        """
        dfs = []
        for col, values in self._data.items():
            keys, raw_counts = np.unique(values, return_counts=True)
            
            order = np.argsort(-raw_counts)
            keys = keys[order]
            raw_counts = raw_counts[order]

            if normalize:
                raw_counts = raw_counts / raw_counts.sum()
            df = DataFrame({col: keys, 'count': raw_counts})
            dfs.append(df)
        if len(dfs) == 1:
            return dfs[0]
        return dfs

    def rename(self, columns):
        """
        Renames columns in the DataFrame

        Parameters
        ----------
        columns: dict
            A dictionary mapping the old column name to the new column name

        Returns
        -------
        A DataFrame

        """
        if not isinstance(columns, dict):
            raise TypeError('`columns` must be a dictionary')

        new_data = {}
        for col, values in self._data.items():
            new_data[columns.get(col, col)] = values
        return DataFrame(new_data)

    def drop(self, columns):
        """
        Drops one or more columns from a DataFrame

        Parameters
        ----------
        columns: str or list of strings

        Returns
        -------
        A DataFrame
        """
        if isinstance(columns, str):
            columns = [columns]
        elif not isinstance(columns, list):
            raise TypeError('`columns` must be either a string or a list')
        new_data = {}
        for col, values in self._data.items():
            if col not in columns:
                new_data[col] = values
        return DataFrame(new_data)

    ### non-aggregation methods

    def abs(self):
        """
        Takes the absolute value of each value in the DataFrame

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.abs)

    def cummin(self):
        """
        Finds cumulative minimum by column

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.minimum.accumulate)

    def cummax(self):
        """
        Finds cumulative maximum by column

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.maximum.accumulate)

    def cumsum(self):
        """
        Finds cumulative sum by column

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.cumsum)

    def clip(self, lower=None, upper=None):
        """
        All values less than lower will be set to lower
        All values greater than upper will be set to upper

        Parameters
        ----------
        lower: number or None
        upper: number or None

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.clip, a_min=lower, a_max=upper)

    def round(self, n):
        """
        Rounds values to the nearest n decimals

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.round, decimals=n)

    def copy(self):
        """
        Copies the DataFrame

        Returns
        -------
        A DataFrame
        """
        return self._non_agg(np.copy)

    def _non_agg(self, func, **kwargs):
        """
        Generic non-aggregation function that applies
        each

        Parameters
        ----------
        funcname: str of NumPy name
        args: extra arguments for certain functions

        Returns
        -------
        A DataFrame
        """
        new_data = {}
        for col, values in self._data.items():
            try:
                val = func(values, **kwargs)
            except TypeError:
                continue
            new_data[col] = val
        return DataFrame(new_data)

    def diff(self, n=1):
        """
        Take the difference between the current value and
        the nth value below it. The top n rows of the DataFrame
        are not returned

        Parameters
        ----------
        n: int

        Returns
        -------
        A DataFrame
        """
        new_data = {}
        for col, values in self._data.items():
            try:
                val = values - np.roll(values, n)
                val = val.astype('float')
                if n >= 0:
                    val[:n] = np.NAN
                else:
                    val[n:] = np.NAN
            except TypeError:
                continue
            new_data[col] = val
        return DataFrame(new_data)

    def pct_change(self, n):
        """
        Take the percentage difference between the current value and
        the nth value below it. The top n rows of the DataFrame
        are not returned

        Parameters
        ----------
        n: int

        Returns
        -------
        A DataFrame
        """
        df = self.diff()
        new_data = {}
        for col, values in df._data.items():
            try:
                val = values / np.roll(self._data[col], n)
            except TypeError:
                continue
            new_data[col] = val
        return DataFrame(new_data)

    #### ARITHMETIC AND COMPARISON OPERATORS ####

    def __add__(self, other):
        return self._oper('__add__', other)

    def __radd__(self, other):
        return self._oper('__radd__', other)

    def __sub__(self, other):
        return self._oper('__sub__', other)

    def __rsub__(self, other):
        return self._oper('__rsub__', other)

    def __mul__(self, other):
        return self._oper('__mul__', other)

    def __rmul__(self, other):
        return self._oper('__rmul__', other)

    def __truediv__(self, other):
        return self._oper('__truediv__', other)

    def __rtruediv__(self, other):
        return self._oper('__rtruediv__', other)

    def __floordiv__(self, other):
        return self._oper('__floordiv__', other)

    def __rfloordiv__(self, other):
        return self._oper('__rfloordiv__', other)

    def __pow__(self, other):
        return self._oper('__pow__', other)

    def __rpow__(self, other):
        return self._oper('__rpow__', other)

    def __gt__(self, other):
        return self._oper('__gt__', other)

    def __lt__(self, other):
        return self._oper('__lt__', other)

    def __ge__(self, other):
        return self._oper('__ge__', other)

    def __le__(self, other):
        return self._oper('__le__', other)

    def __ne__(self, other):
        return self._oper('__ne__', other)

    def __eq__(self, other):
        return self._oper('__eq__', other)

    def _oper(self, op, other):
        """
        Generic operator function

        Parameters
        ----------
        op: str name of special method
        other: the other object being operated on

        Returns
        -------
        A DataFrame
        """
        if isinstance(other, DataFrame):
            other = other.values
        new_data = {}
        for col, values in self._data.items():
            new_data[col] = getattr(values, op)(other)
        return DataFrame(new_data)

    def sort_values(self, by, asc=True):
        """
        Sort the DataFrame by one or more values

        Parameters
        ----------
        by: str or list of column names
        asc: boolean of sorting order

        Returns
        -------
        A DataFrame
        """
        if isinstance(by, str):
            order = np.argsort(self._data[by]).tolist()
        elif isinstance(by, list):
            cols = [self._data[col] for col in by[::-1]]
            order = np.lexsort(cols).tolist()
        else:
            raise TypeError('`by` must be a str or a list')

        if not asc:
            order = order[::-1]
        return self[order, :]

    def sample(self, n=None, frac=None, replace=False, seed=None):
        """
        Randomly samples rows the DataFrame

        Parameters
        ----------
        n: int
            number of rows to return
        frac: float
            Proportion of the data to sample
        replace: bool
            Whether or not to sample with replacement

        Returns
        -------
        A DataFrame
        """
        if seed:
            np.random.seed(seed)
        if frac is not None:
            if frac <= 0:
                raise ValueError('`frac` must be positive')
            n = int(frac * len(self))
        if n is not None:
            if not isinstance(n, int):
                raise TypeError('`n` must be an int')
            rows = np.random.choice(np.arange(len(self)), size=n, replace=replace).tolist()
        return self[rows, :]

    def pivot_table(self, rows=None, columns=None, values=None, aggfunc=None):
        """
        Grouping

        Parameters
        ----------
        rows: str of column name to group by
            Optional
        columns: str of column name to group by
            Optional
        values: str of column name to aggregate
            Required
        aggfunc: str of aggregation function

        Returns
        -------
        A DataFrame
        """
        if values is None:
            aggfunc = 'size'
        if rows is None and columns is None:
            raise ValueError('At least one of `rows` or `columns` must not be None')
        aggfunc_name = aggfunc
        if aggfunc in [None, 'size']:
            aggfunc = '__len__'
            aggfunc_name = 'size'

        def get_groups_one(group_values):
            group_values = np.sort(self._data[group_values])
            diff = group_values != np.roll(group_values, 1)

            # always keep first value as a group
            diff[0] = True
            groups = group_values[diff]

            # Use the diff variable as the group number, so the first value is always 0
            diff[0] = False
            group_labels = diff.cumsum()
            return groups, group_labels

        def group_multiple(rows, columns):
            row_values = self._data[rows]
            col_values = self._data[columns]
            order = np.lexsort([col_values, row_values])
            values_sorted = np.column_stack([row_values[order], col_values[order]])
            diff = values_sorted != np.roll(values_sorted, 1, axis=0)
            diff_final = np.any(diff, axis=1)
            diff_final[0] = True
            groups = values_sorted[diff_final]

            diff_final[0] = False
            group_labels = diff_final.cumsum()
            return groups, group_labels, order

        if values:
            agg_col = self._data[values]
        else:
            agg_col = np.empty(len(self))

        # group by one variable
        if columns is None:
            groups, group_labels = get_groups_one(rows)
            new_data = {rows: np.array(groups)}
            agg_values = []
            for i, group in enumerate(groups):
                agg_values.append(getattr(agg_col[group_labels == i], aggfunc)())
            new_data[aggfunc_name] = np.array(agg_values)

        elif rows is None:
            groups, group_labels = get_groups_one(columns)
            new_data = {}
            for i, group in enumerate(groups):
                new_val = getattr(agg_col[group_labels == i], aggfunc)()
                new_data[group] = np.array([new_val])
        else:
            groups, group_labels, order = group_multiple(rows, columns)
            num_groups = len(groups)
            unique_rows = np.unique(groups[:, 0])
            unique_cols = np.unique(groups[:, 1])
            new_data = {rows: unique_rows}
            for col in unique_cols:
                new_data[columns + '_' + col] = np.full(len(unique_rows), np.nan)
            row_position = {}
            for i, row in enumerate(unique_rows):
                row_position[row] = i

            agg_col = agg_col[order]
            for i in range(num_groups):
                cur_row, cur_col = groups[i, 0], groups[i, 1]
                cur_agg = getattr(agg_col[group_labels == i], aggfunc)()
                cur_row_pos = row_position[cur_row]
                new_data[columns + '_' + cur_col][cur_row_pos] = cur_agg

        return DataFrame(new_data)

    def _add_docs(self):
        agg_names = ['min', 'max', 'mean', 'median', 'sum', 'var',
                     'std', 'any', 'all', 'argmax', 'argmin']
        agg_doc = \
        """
        Find the {} of each column

        Returns
        -------
        DataFrame
        """
        for name in agg_names:
            getattr(DataFrame, name).__doc__ = agg_doc.format(name)


class StringMethods:

    def __init__(self, df):
        self._df = df

    def capitalize(self, col):
        return self._str_method('capitalize', col)

    def center(self, col, width, fillchar=None):
        if fillchar is None:
            fillchar = ' '
        return self._str_method('center', col, width, fillchar)

    def count(self, col, sub, start=None, stop=None):
        return self._str_method('count', col, sub, start, stop)

    def endswith(self, col, suffix, start=None, stop=None):
        return self._str_method('endswith', col, suffix, start, stop)

    def startswith(self, col, suffix, start=None, stop=None):
        return self._str_method('startswith', col, suffix, start, stop)

    def find(self, col, sub, start=None, stop=None):
        return self._str_method('find', col, sub, start, stop)

    def len(self, col):
        return self._str_method('__len__', col)

    def get(self, col, item):
        return self._str_method('__getitem__', col, item)

    def index(self, col, sub, start=None, stop=None):
        return self._str_method('index', col, sub, start, stop)

    def isalnum(self, col):
        return self._str_method('isalnum', col)

    def isalpha(self, col):
        return self._str_method('isalpha', col)

    def isdecimal(self, col):
        return self._str_method('isdecimal', col)

    def islower(self, col):
        return self._str_method('islower', col)

    def isnumeric(self, col):
        return self._str_method('isnumeric', col)

    def isspace(self, col):
        return self._str_method('isspace', col)

    def istitle(self, col):
        return self._str_method('istitle', col)

    def isupper(self, col):
        return self._str_method('isupper', col)

    def lstrip(self, col, chars):
        return self._str_method('lstrip', col, chars)

    def rstrip(self, col, chars):
        return self._str_method('rstrip', col, chars)

    def strip(self, col, chars):
        return self._str_method('strip', col, chars)

    def replace(self, col, old, new, count=None):
        if count is None:
            count = -1
        return self._str_method('replace', col, old, new, count)

    def swapcase(self, col):
        return self._str_method('swapcase', col)

    def title(self, col):
        return self._str_method('title', col)

    def upper(self, col):
        return self._str_method('upper', col)

    def zfill(self, col, width):
        return self._str_method('zfill', col, width)

    def encode(self, col, encoding='utf-8', errors='strict'):
        return self._str_method(col, encoding, errors)

    def _str_method(self, method, col, *args):
        old_values = self._df._data[col]
        new_values = []
        for val in old_values:
            if val is None:
                new_values.append(val)
            else:
                new_val = getattr(val, method)(*args)
                new_values.append(new_val)
        arr = np.array(new_values)
        if arr.dtype.kind == 'U':
            arr = arr.astype('O')
        return DataFrame({col: arr})


def read_csv(fn):
    values = {}
    with open(fn) as f:
        header = f.readline()
        column_names = header.strip('\n').split(',')
        for name in column_names:
            values[name] = []
        for line in f.readlines():
            for val, name in zip(line.strip('\n').split(','), column_names):
                values[name].append(val)
    new_data = {}
    for col, vals in values.items():
        try:
            new_data[col] = np.array(vals, dtype='int')
        except ValueError:
            try:
                new_data[col] = np.array(vals, dtype='float')
            except ValueError:
                new_data[col] = np.array(vals, dtype='O')
    return DataFrame(new_data)
