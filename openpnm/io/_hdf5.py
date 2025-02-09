import logging
from flatdict import FlatDict
from openpnm.io import Dict, GenericIO
logger = logging.getLogger(__name__)


class HDF5(GenericIO):
    r"""
    The HDF5 (Hierarchical Data Format) file is good for high-peformance, long
    term data storage
    """

    @classmethod
    def export_data(cls, network=None, phases=[], element=['pore', 'throat'],
                    filename='', interleave=True, flatten=False, categorize_by=[]):
        r"""
        Creates an HDF5 file containing data from the specified objects,
        and categorized according to the given arguments.

        Parameters
        ----------
        network : GenericNetwork
            The network containing the desired data

        phases : list[GenericPhase]s (optional, default is none)
            A list of phase objects whose data are to be included

        element : str or list[str]
            An indication of whether 'pore' and/or 'throat' data are desired.
            The default is both.

        interleave : bool (default is ``True``)
            When ``True`` (default) the data from all Geometry objects (and
            Physics objects if ``phases`` are given) is interleaved into
            a single array and stored as a network property (or Phase
            property for Physics data). When ``False``, the data for each
            object are stored under their own dictionary key, the structuring
            of which depends on the value of the ``flatten`` argument.

        flatten : bool (default is ``True``)
            When ``True``, all objects are accessible from the top level
            of the dictionary.  When ``False`` objects are nested under their
            parent object.  If ``interleave`` is ``True`` this argument is
            ignored.

        categorize_by : str or list[str]
            Indicates how the dictionaries should be organized.  The list can
            contain any, all or none of the following strings:

            **'objects'** : If specified the dictionary keys will be stored
            under a general level corresponding to their type (e.g.
            'network/net_01/pore.all'). If  ``interleave`` is ``True`` then
            only the only categories are *network* and *phase*, since
            *geometry* and *physics* data get stored under their respective
            *network* and *phase*.

            **'data'** : If specified the data arrays are additionally
            categorized by ``label`` and ``property`` to separate *boolean*
            from *numeric* data.

            **'elements'** : If specified the data arrays are additionally
            categorized by ``pore`` and ``throat``, meaning that the propnames
            are no longer prepended by a 'pore.' or 'throat.'

        """
        from h5py import File as hdfFile
        project, network, phases = cls._parse_args(network=network,
                                                   phases=phases)
        if filename == '':
            filename = project.name
        filename = cls._parse_filename(filename, ext='hdf')

        dct = Dict.to_dict(network=network, phases=phases, element=element,
                           interleave=interleave, flatten=flatten,
                           categorize_by=categorize_by)
        d = FlatDict(dct, delimiter='/')

        f = hdfFile(filename, "w")
        for item in d.keys():
            tempname = '_'.join(item.split('.'))
            arr = d[item]
            if d[item].dtype == 'O':
                logger.warning(item + ' has dtype object, will not write to file')
                del d[item]
            elif 'U' in str(arr[0].dtype):
                pass
            else:
                f.create_dataset(name='/'+tempname, shape=arr.shape,
                                 dtype=arr.dtype, data=arr)
        return f


def print_hdf5(f, flat=False):
    r"""
    Given an hdf5 file handle, prints to console in a human readable manner

    Parameters
    ----------
    f : file handle
        The hdf5 file to print
    flat : bool
        Flag to indicate if print should be nested or flat.  The default is
        ``flat==False`` resulting in a nested view.
    """
    if flat is False:
        def print_level(f, p='', indent='-'):
            for item in f.keys():
                if hasattr(f[item], 'keys'):
                    p = print_level(f[item], p=p, indent=indent + indent[0])
                elif indent[-1] != ' ':
                    indent = indent + ''
                p = indent + item + '\n' + p
            return(p)
        p = print_level(f)
        print(p)
    else:
        f.visit(print)


def to_hdf5(network=None, phases=[], element=['pore', 'throat'],
            filename='', interleave=True, flatten=False, categorize_by=[]):
    return HDF5.export_data(network=network, phases=phases, element=element,
                            filename=filename, interleave=interleave,
                            flatten=flatten, categorize_by=categorize_by)


to_hdf5.__doc__ = HDF5.export_data.__doc__
