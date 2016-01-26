from cosmosis.datablock import names, option_section
import numpy as np
import scipy.interpolate
try:
    import astropy.io.fits as pyfits
except ImportError:
    try:
        import pyfits
    except ImportError:
        raise RuntimeError("You need astropy installed to use the module load_nz_fits; try running: pip install astropy.")


def ensure_starts_at_zero(z, nz):
    nbin = nz.shape[0]
    if z[0]>0.00000001:
        z_new=np.zeros(len(z)+1)
        z_new[1:]=z
        nz_new=np.zeros((nbin,len(z)+1))
        nz_new[:,1:]=nz
        print "        Putting n(0) = 0 at the start of the n(z)"
    else:
        z_new = z
        nz_new = nz
    return z_new, nz_new


def load_histogram_form(ext):
    #Load the various z columns.
    #The cosmosis code is expecting something it can spline
    #so  we need to give it more points than this - we will
    #give it the intermediate z values (which just look like a step
    #function)
    zlow = ext.data['Z_LOW']
    zhigh = ext.data['Z_HIGH']

    upsampling = 10
    z = np.linspace(zlow[0], zhigh[-1], len(zlow)*upsampling)
    sample_bin = np.digitize(z, zlow)-1

    #First bin.
    i=1
    bin_name = 'BIN{0}'.format(i)

    #Load the n(z) columns, bin1, bin2, ...
    nz = []
    while bin_name in ext.data.names:
        col = ext.data[bin_name][sample_bin]
        nz.append(col)
        i+=1
        bin_name = 'BIN{0}'.format(i)

    nbin = len(nz)
    print "        Found {0} bins".format(nbin)
    nz = np.array(nz)
    z, nz = ensure_starts_at_zero(z, nz)
    for col in nz:
        norm = np.trapz(col, z)
        col/=norm
    return z, nz


def setup(options):
    nz_file = options.get_string(option_section, "nz_file")
    data_sets = options.get_string(option_section, "data_sets")
    data_sets = data_sets.split()
    if not data_sets:
        raise RuntimeError("Option data_sets empty; please set the option data_sets=name1 name2 etc and I will search the fits file for nz_name2, nz_name2, etc.")
    
    print "Loading number density data from {0}:".format(nz_file)
    F = pyfits.open(nz_file)
    data = {}
    for data_set in data_sets:
        name = "NZ_"+data_set.upper()
        print "    Looking at FITS extension {0}:".format(name)
        ext = F[name]
        z, nz = load_histogram_form(ext)
        data[name] = (z, nz)
    return data


def execute(block, config):
    data_sets = config
    for name,data in config.items():
        z, nz = data
        nbin = len(nz)
        ns = len(z)
        block[name, "nbin"] = nbin
        block[name, "nz"] = ns
        block[name, "z"] = z
        for i, n in enumerate(nz):
            block[name, "bin_{0}".format(i+1)] = n
    return 0
