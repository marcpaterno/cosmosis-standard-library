import cosmosis
import pytest

def build_camb_module(mode, **kwargs):
    camb_options = {
        "file": "boltzmann/camb/camb_interface.py",
        "mode": mode,
        "feedback": 0,
        "do_lensing": True,
        "do_reionization": True,
        "nonlinear": "both",
        "use_ppf_w": True,
    } | kwargs

    options = cosmosis.Inifile({"camb": camb_options})

    module = cosmosis.Module.from_options("camb", options)
    module.setup({"camb": camb_options})
    return module

def test_basic_camb():
    module = build_camb_module(mode="all")
    
    block = cosmosis.DataBlock()
    block["cosmological_parameters", "ombh2"] = 0.022
    block["cosmological_parameters", "omch2"] = 0.12
    block["cosmological_parameters", "h0"] = 0.675
    block["cosmological_parameters", "tau"] = 0.06
    block["cosmological_parameters", "n_s"] = 0.965
    block["cosmological_parameters", "A_s"] = 2.1e-9
    block["cosmological_parameters", "omega_k"] = 0.0

    module.execute(block)


def test_zmin_non_zero():
    module = build_camb_module(mode="all", zmin=0.2)
    
    block = cosmosis.DataBlock()
    block["cosmological_parameters", "ombh2"] = 0.022
    block["cosmological_parameters", "omch2"] = 0.12
    block["cosmological_parameters", "h0"] = 0.675
    block["cosmological_parameters", "tau"] = 0.06
    block["cosmological_parameters", "n_s"] = 0.965
    block["cosmological_parameters", "A_s"] = 2.1e-9
    block["cosmological_parameters", "omega_k"] = 0.0

    # Unless we explicily tell it not to, CAMB will still integrate down to z=0 to get sigma_8(0),
    # even if we set zmin>0.
    block1 = block.clone()
    module.execute(block1)
    assert block1.has_value("cosmological_parameters", "sigma_8")

    # We should get a warning about this
    with pytest.warns(UserWarning, match="You have set no_integrate_to_z_0 to avoid integrating to redshift zero"):
        module2 = build_camb_module(mode="all", zmin=0.2, no_integrate_to_z_0=True)
    block2 = block.clone()

    # this should give us a warning
    module2.execute(block2)
    # If we set no_integrate_to_z_0 then we won't have sigma_8
    assert not block2.has_value("cosmological_parameters", "sigma_8")

    # if we set zmin=0 but no_integrate_to_z_0 then we should still get sigma_8(0)
    # because it is available
    module3 = build_camb_module(mode="all", zmin=0.0, no_integrate_to_z_0=True)
    block3 = block.clone()
    module3.execute(block3)
    assert block3.has_value("cosmological_parameters", "sigma_8")