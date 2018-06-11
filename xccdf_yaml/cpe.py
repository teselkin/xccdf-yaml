import cpe

def get_affected_from_cpe(cpe_string):
    """ Returns string formatted for using in the platform -> affected
    in an oval definition metadata (SSG naming scheme).
    ...
    >>> print(get_affected_from_cpe('cpe:/o:canonical:ubuntu_linux:16.04'))
    >>> Ubuntu 1604

    >>> print(get_affected_from_cpe('cpe:/o:canonical:ubuntu_linux:14.04'))
    >>> Ubuntu 1404

    >>> print(get_affected_from_cpe('cpe:/o:debianproject:debian:8'))
    >>> Debian 8

    >>> print(get_affected_from_cpe('cpe:/o:fedoraproject:fedora:28'))
    >>> Fedora 28

    >>> print(get_affected_from_cpe('cpe:/o:novell:leap:42.0'))
    >>> OpenSUSE 420

    >>> print(get_affected_from_cpe('cpe:/o:redhat:enterprise_linux:6'))
    >>> Red Hat Enterprise Linux 6

    >>> print(get_affected_from_cpe('cpe:/o:suse:linux_enterprise_server:11'))
    >>> SUSE Linux Enterprise 11
    """
    __products_version_exclude__ = ['leap']
    __mapping__ = {
        'redhat': {
            'enterprise_linux': 'Red Hat Enterprise Linux',
        },
        'canonical': {
            'ubuntu_linux': 'Ubuntu',
        },
        'suse': {
            'linux_enterprise_server': 'SUSE Linux Enterprise',
        },
        'novell': {
            'leap': 'OpenSUSE',
        },
    }
    cpeobject = cpe.CPE(cpe_string)
    vendor = cpeobject.get_vendor()[0]
    product = cpeobject.get_product()[0]
    affected_string = __mapping__.get(vendor, {}).get(
                                      product, product.capitalize())
    if product in __products_version_exclude__:
        return affected_string
    version = cpeobject.get_version()[0].replace('.', '')
    affected_string = '{} {}'.format(affected_string, version)
    return affected_string
