import logging
import openpnm.models as mods
from openpnm.geometry import GenericGeometry
from openpnm.utils import SettingsAttr, TypedList, Docorator


logger = logging.getLogger(__name__)
docstr = Docorator()


class ImportedSettings:
    r"""
    Brief explanation of 'ImportedSettings'.

    Parameters
    ----------
    pore_diameter : str, default is 'pore.extended_diameter'
        Key into the extracted data array to use as pore diameter in other
        geometry calculations. Use of 'pore.' is not required.
    throat_diameter : str, default is 'throat.equivalent_diameter'
        Key into the extracted data array to use as throat diameter in other
        geometry calculations. Use of 'throat.' is not required.
    pore_shape : str, default is 'sphere'
        Specifies which shape to assume when calculating dependent properties
        such as volume and surface area. Options are 'sphere' and 'cube'.
    throat_shape : str, default is 'cylinder'
        Specifies which shape to assume when calculating dependent properties
        such as volume and surface area. Options are 'cylinder' and 'cuboid'.

    """
    pore_diameter = 'extended_diameter'
    throat_diameter = 'inscribed_diameter'
    pore_shape = 'cone'
    throat_shape = 'cylinder'
    exclude_props = TypedList(types=[str])


@docstr.dedent
class Imported(GenericGeometry):
    r"""
    This geometry class extracts all numerical properites from the received
    network object and moves them to itself.

    This class is intended for use with networks imported from network
    extraction codes, where the geometry properties are included on the
    network itself.

    Parameters
    ----------
    exclude : list of strings
        A list of which network properties should *not* be transferred to
        new geometry object.  'pore.coords' and 'throat.conns' are *always*
        excluded.  Note that labels are not transferred, only properties.
    %(GenericGeometry.parameters)s

    Notes
    -----
    An error occurs when adding other geometries to a network that has
    geometrical properties such as 'pore.diameter'. This can occur when
    adding boundary pores or in more elaborate scenarios such as stitching
    networks together. The issue arises because OpenPNM prevents a property,
    such as 'pore.volume', from existing on both the network and also a
    geometry. Thus it is necessary to move the extracted network properties
    to this ``Imported`` class, then create new geometry objects for any
    added pores as needed.

    """

    def __init__(self, settings=None, **kwargs):
        self.settings = SettingsAttr(ImportedSettings, settings)
        if 'network' in kwargs.keys():
            network = kwargs.pop('network')
        elif 'project' in kwargs.keys():
            project = kwargs.pop('project')
            network = project.network
        super().__init__(network=network, pores=network.Ps, throats=network.Ts,
                         settings=self.settings, **kwargs)
        # Transfer all geometrical properties off of network
        exclude = self.settings['exclude_props']
        exclude.extend(['pore.coords', 'throat.conns', 'pore.region_label'])
        for item in network.props():
            if item not in exclude:
                self[item] = network.pop(item)

        # If the following 'essential' props are not already defined, then
        # they should be added using the specified values or models
        if 'pore.diameter' not in self.keys():
            pdia = 'pore.'+self.settings['pore_diameter'].split('pore.')[-1]
            try:
                self['pore.diameter'] = self[pdia]
            except KeyError:
                logger.error(pdia + " not found, can't assign 'pore.diameter'")

        # if 'pore.volume' not in self.keys():
        #     pore_shape = self.settings['pore_shape']
        #     m = getattr(mods.geometry.pore_volume, pore_shape)
        #     self.add_model(propname='pore.volume',
        #                    model=m, pore_diameter='pore.diameter')

        # if 'pore.area' not in self.keys():
        #     pore_shape = self.settings['pore_shape']
        #     m = getattr(mods.geometry.pore_area, pore_shape)
        #     self.add_model(propname='pore.area',
        #                    model=m)

        if 'throat.diameter' not in self.keys():
            tdia = 'throat.'+self.settings['throat_diameter'].split('throat.')[-1]
            try:
                self['throat.diameter'] = self[tdia]
            except KeyError:
                logger.error(tdia + " not found, can't assign 'throat.diameter'")

        t_shape = self.settings['throat_shape'] + 's'
        p_shape = self.settings['pore_shape'] + 's'
        if 'throat.length' not in self.keys():
            m = getattr(mods.geometry.throat_length, p_shape + '_and_' + t_shape)
            self.add_model(propname='throat.length',
                           model=m,
                           throat_diameter='throat.diameter',
                           pore_diameter='pore.diameter')

        if 'throat.volume' not in self.keys():
            shape = self.settings['throat_shape']
            m = getattr(mods.geometry.throat_volume, shape)
            self.add_model(propname='throat.volume',
                           model=m,
                           throat_length='throat.length',
                           throat_diameter='throat.diameter')
        m = getattr(mods.geometry.diffusive_size_factors, p_shape + '_and_' + t_shape)
        self.add_model(propname='throat.diffusive_size_factors', model=m)
        m = getattr(mods.geometry.hydraulic_size_factors, p_shape + '_and_' + t_shape)
        self.add_model(propname='throat.hydraulic_size_factors', model=m)
