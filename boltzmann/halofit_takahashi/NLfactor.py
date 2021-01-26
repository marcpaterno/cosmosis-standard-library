from cosmosis.datablock import option_section, names
from scipy.interpolate import interp1d
from numpy import zeros_like, zeros


def setup(options):
    lin = options.get_string(option_section, 'linear_section', names.matter_power_lin)
    nonlin = options.get_string(option_section, 'nonlinear_section', names.matter_power_nl)
    target = options.get_string(option_section, 'target_section', 'weyl_curvature_spectrum')
    rescale_weyl = options.get_bool(option_section, 'rescale_weyl', False)
    return lin, nonlin, target, rescale_weyl


def execute(block, config):
    lin, nonlin, target, rescale_weyl = config

    # Need to get things at the same wavenumbers for ratio
    z_lin,k_lin,p_k_lin = (block.get_grid(lin, "z","k_h", "P_k"))
    z_nl,k_nl,p_k_nl = (block.get_grid(nonlin, "z", "k_h","P_k"))
    z_t,k_t,p_k_t = (block.get_grid(target, "z","k_h", "P_k"))

    p_k_lin_at_nlk = zeros_like(p_k_nl)
    # assuming _cosmosis_order_p_k = u'z_cosmosis_order_k_h'
    # assuming same z array

    for zi in range(0, len(z_nl)):
        p_k_lin_at_nlk[zi,:] = interp1d(k_lin, p_k_lin[zi,:])(block[nonlin, 'k_h'])

        

    R = p_k_nl / p_k_lin_at_nlk

    # The nonlin pk doesn't go to as small k, so we have to truncate the target k_h for the nl case.
    if min(k_t)<min(k_nl):
        mink = next(j[0] for j in enumerate(k_t) if j[1]>min(k_nl))
    else:
        mink = 0
    if max(k_t)>max(k_nl):
        maxk = next(j[0] for j in enumerate(k_t) if j[1]>max(k_nl))
    else:
        maxk=len(k_t)
    ratio_at_wk = zeros((len(z_nl), len(k_t[mink:maxk])))
    for zi in range(0, len(z_nl)):
        ratio_at_wk[zi,:] = interp1d(k_nl, R[zi,:])(k_t[mink:maxk])

    #block[target+"_nl", 'k_h'] = block[target, 'k_h'][mink:maxk]
    
    # Apply ratio to target spectrum
    weyl_nl = zeros_like(ratio_at_wk)
    for zi in range(0, len(z_nl)):
        weyl_nl[zi,:] = ratio_at_wk[zi,:]*p_k_t[zi,:][mink:maxk]   
    
    # rescale weyl power by the relationship in equation (7.7) dodelson
    if rescale_weyl:
        c_kms = 299792.4580
        omega_m = block[names.cosmological_parameters, "omega_m"]
        h0 = block[names.cosmological_parameters, "h0"]
        scale_factor = 1.5 * (100.0*100.0)/(c_kms*c_kms) * omega_m *h0**2
        for zi,z in enumerate(z_t):
            weyl_nl[zi] = weyl_nl[zi]/scale_factor**2/(1+z)**2
        block.put_grid(target+"_nl_scaled","z",z_nl,"k_h",k_t[mink:maxk],"P_k",weyl_nl)
        print('Rescaling nonlinear weyl potential power spectum by (1.5 * (100.0*100.0)/(c_kms*c_kms) * omega_m *h0**2*(z+1))**(-2), in preparation for 2d projection')
    else:
    # Save to block
        block.put_grid(target+"_nl","z",z_nl,"k_h",k_t[mink:maxk],"P_k",weyl_nl)

    return 0
