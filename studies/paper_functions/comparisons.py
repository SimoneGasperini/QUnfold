import sys, os
import ROOT
import numpy as np
import pylab as plt
from QUnfold import QUnfoldQUBO
from QUnfold.utility import (
    TH1_to_array,
    TH2_to_array,
    normalize_response,
    compute_chi2,
    TMatrix_to_array,
)

# RooUnfold settings
loaded_RooUnfold = ROOT.gSystem.Load("HEP_deps/RooUnfold/libRooUnfold.so")
if not loaded_RooUnfold == 0:
    print("RooUnfold not found!")
    sys.exit(0)


def make_plots(
    SA_info, HYB_info, IBU_info, MI_info, truth, measured, binning, var, quantum
):
    # Divide into subplots
    fig = plt.figure(figsize=(8.0, 6.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    marker_size = 3.5
    binwidths = np.diff(binning)
    bin_midpoints = binning[:-1] + binwidths / 2

    # Plot truth
    truth_steps = np.append(truth, [truth[-1]])
    ax1.step(
        binning,
        truth_steps,
        label=r"Truth ($\mathtt{Madgraph}$)",
        where="post",
        color="tab:blue",
    )
    ax1.fill_between(binning, truth_steps, step="post", alpha=0.3, color="tab:blue")
    ax2.axhline(y=1, color="tab:blue")

    # Plot measured
    meas_steps = np.append(measured, [measured[-1]])
    ax1.step(
        binning,
        meas_steps,
        label=r"Measured ($\mathtt{Delphes}$)",
        where="post",
        color="tab:orange",
    )
    ax1.fill_between(binning, meas_steps, step="post", alpha=0.3, color="tab:orange")

    # Plot MI
    MI_chi2 = MI_info["chi2"]
    label = r"{} ($\chi^2 = {:.2f}$)".format(r"$\mathtt{RooUnfold}$ (MI)", MI_chi2)
    ax1.errorbar(
        x=bin_midpoints,
        y=MI_info["mean"],
        yerr=MI_info["std"],
        label=label,
        marker="s",
        ms=marker_size,
        c="green",
        linestyle="None",
    )

    ax2.errorbar(
        x=bin_midpoints,
        y=MI_info["mean"] / truth,
        yerr=MI_info["std"] / truth,
        ms=marker_size,
        fmt="s",
        color="green",
    )

    # Plot IBU
    IBU_chi2 = IBU_info["chi2"]
    label = r"{} ($\chi^2 = {:.2f}$)".format(r"$\mathtt{RooUnfold}$ (IBU)", IBU_chi2)
    ax1.errorbar(
        x=bin_midpoints,
        y=IBU_info["mean"],
        yerr=IBU_info["std"],
        label=label,
        marker="o",
        ms=marker_size,
        c="red",
        linestyle="None",
    )

    ax2.errorbar(
        x=bin_midpoints,
        y=IBU_info["mean"] / truth,
        yerr=IBU_info["std"] / truth,
        ms=marker_size,
        fmt="o",
        color="red",
    )

    # Plot SA
    SA_chi2 = SA_info["chi2"]
    label = r"{} ($\chi^2 = {:.2f}$)".format(r"$\mathtt{QUnfold}$ (SIM)", SA_chi2)
    ax1.errorbar(
        x=bin_midpoints,
        y=SA_info["mean"],
        yerr=SA_info["std"],
        label=label,
        marker="*",
        ms=marker_size,
        c="purple",
        linestyle="None",
    )

    ax2.errorbar(
        x=bin_midpoints,
        y=SA_info["mean"] / truth,
        yerr=SA_info["std"] / truth,
        ms=marker_size,
        fmt="*",
        color="purple",
    )

    # Plot HYB
    if quantum == True:
        HYB_chi2 = HYB_info["chi2"]
        label = r"{} ($\chi^2 = {:.2f}$)".format(r"$\mathtt{QUnfold}$ (HYB)", HYB_chi2)
        ax1.errorbar(
            x=bin_midpoints,
            y=HYB_info["mean"],
            yerr=HYB_info["std"],
            label=label,
            marker="*",
            ms=marker_size,
            c="orange",
            linestyle="None",
        )

        ax2.errorbar(
            x=bin_midpoints,
            y=HYB_info["mean"] / truth,
            yerr=HYB_info["std"] / truth,
            ms=marker_size,
            fmt="*",
            color="orange",
        )

    # Set var name to latex
    variable_labels = {
        "pT_lep1": r"$p_T^{lep1}$ [GeV]",
        "pT_lep2": r"$p_T^{lep2}$ [GeV]",
        "eta_lep1": r"$\eta^{lep1}$",
        "eta_lep2": r"$\eta^{lep2}$",
        "DR_b1b2": r"$\Delta R_{b1b2}$",
        "m_l1l2": r"$m_{l1l2}$ [GeV]",
        "m_b1b2": r"$m_{b1b2}$ [GeV]",
    }
    varname = variable_labels.get(var)

    # Plot settings
    ax1.tick_params(axis="x", which="both", bottom=True, top=False, direction="in")
    ax2.tick_params(axis="x", which="both", bottom=True, top=True, direction="in")
    ax1.set_xlim(binning[0], binning[-1])
    ax1.set_ylim(0, ax1.get_ylim()[1])
    ax2.set_yticks([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75])
    ax2.set_yticklabels(["", "0.5", "", "1.0", "", "1.5", ""])
    ax1.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
    ax2.set_ylabel("Ratio to\ntruth")
    ax2.set_xlabel(varname, loc="center")
    ax1.set_ylabel("Entries", loc="center")
    ax1.legend(loc="best")

    # Save plot
    plt.tight_layout()
    if not os.path.exists("studies/img/paper"):
        os.makedirs("studies/img/paper/png")
        os.makedirs("studies/img/paper/pdf")
    plt.savefig(f"studies/img/paper/png/comparison_{var}.png")
    plt.savefig(f"studies/img/paper/pdf/comparison_{var}.pdf")
    plt.close()


def make_comparisons(reco, particle):
    # Variables
    variables = [
        "pT_lep1",
        "pT_lep2",
        "m_l1l2",
        "m_b1b2",
        # "DR_b1b2",
        # "eta_lep1",
        # "eta_lep2",
    ]
    num_toys = 50
    quantum = False

    # RUnning over variables
    for var in variables:
        print(f"Processing the {var} variable...")

        # Raw input
        m_response = reco.Get(f"particle_{var}_vs_{var}")
        h_measured = reco.Get(var)
        h_truth = particle.Get(f"particle_{var}")
        h_mc_measured = reco.Get(f"mc_{var}")
        h_mc_truth = particle.Get(f"mc_particle_{var}")

        # Prepare unfolding input
        measured = TH1_to_array(h_measured, overflow=True)
        truth = TH1_to_array(h_truth, overflow=True)
        response = normalize_response(
            TH2_to_array(m_response, overflow=True),
            TH1_to_array(h_mc_truth, overflow=True),
        )
        binning = [
            reco.Get(var).GetXaxis().GetBinLowEdge(bin)
            for bin in range(1, reco.Get(var).GetNbinsX() + 2)
        ]

        # Unfold with QUnfold (basic settings)
        lam = 0.0
        num_reads = 100  # 1000
        if var == "pT_lep1":
            lam = 0.0001  # 0.00001
        elif var == "pT_lep2":
            lam = 0.0  # 0.0001
        elif var == "m_l1l2":
            lam = 0.0  # 0.0005
        elif var == "m_b1b2":
            lam = 0.0  # 0.00005
        elif var == "DR_b1b2":
            lam = 0.0001
        elif var == "eta_lep1":
            lam = 0.00001
        elif var == "eta_lep2":
            lam = 0.00001
        unfolder = QUnfoldQUBO(measured=measured, response=response, lam=lam)

        # Simulated annealing
        unfolded_SA, error_SA, cov_SA, _ = unfolder.solve_simulated_annealing(
            num_reads=num_reads, num_toys=num_toys
        )
        chi2_SA = None
        if cov_SA is None:
            chi2_SA = compute_chi2(unfolded_SA, truth)
        else:
            chi2_SA = compute_chi2(unfolded_SA, truth, cov_SA)

        # Hybrid solver
        unfolded_HYB, error_HYB, chi2_HYB = None, None, None
        if quantum == True:
            unfolded_HYB, error_HYB, cov_HYB, _ = unfolder.solve_hybrid_sampler(
                num_toys=num_toys
            )
            chi2_HYB = None
            if cov_HYB is None:
                chi2_HYB = compute_chi2(unfolded_HYB, truth)
            else:
                chi2_HYB = compute_chi2(unfolded_HYB, truth, cov_HYB)

        # Make RooUnfold response
        m_response = ROOT.RooUnfoldResponse(h_mc_measured, h_mc_truth, m_response)
        m_response.UseOverflow(True)

        # Unfold with RooUnfold IBU
        unfolder = ROOT.RooUnfoldBayes("IBU", "Iterative Bayesian")
        unfolder.SetIterations(4)
        unfolder.SetVerbose(0)
        unfolder.SetSmoothing(0)
        unfolder.SetResponse(m_response)
        unfolder.SetMeasured(h_measured)
        unfolded_IBU_histo = None
        if num_toys == 1:
            unfolded_IBU_histo = unfolder.Hunfold(unfolder.kErrors)
        elif num_toys > 1:
            unfolder.SetNToys(num_toys)
            unfolded_IBU_histo = unfolder.Hunfold(unfolder.kCovToys)
        unfolded_IBU = TH1_to_array(unfolded_IBU_histo)
        start, stop = 0, unfolded_IBU_histo.GetNbinsX() + 2
        error_IBU = np.array(
            [unfolded_IBU_histo.GetBinError(i) for i in range(start, stop)]
        )
        chi2_IBU = None
        if num_toys == 1:
            chi2_IBU = compute_chi2(unfolded_IBU, truth)
        elif num_toys > 1:
            cov_IBU = unfolder.Eunfold(unfolder.kCovToys)
            chi2_IBU = compute_chi2(unfolded_IBU, truth, TMatrix_to_array(cov_IBU))

        # Unfold with RooUnfold Matrix Inversion
        unfolder = ROOT.RooUnfoldInvert("MI", "Matrix Inversion")
        unfolder.SetVerbose(0)
        unfolder.SetResponse(m_response)
        unfolder.SetMeasured(h_measured)
        unfolded_MI_histo = None
        if num_toys == 1:
            unfolded_MI_histo = unfolder.Hunfold(unfolder.kErrors)
        elif num_toys > 1:
            unfolder.SetNToys(num_toys)
            unfolded_MI_histo = unfolder.Hunfold(unfolder.kCovToys)
        unfolded_MI = TH1_to_array(unfolded_MI_histo)
        start, stop = 0, unfolded_MI_histo.GetNbinsX() + 2
        error_MI = np.array(
            [unfolded_MI_histo.GetBinError(i) for i in range(start, stop)]
        )
        chi2_MI = None
        if num_toys == 1:
            chi2_MI = compute_chi2(unfolded_MI, truth)
        elif num_toys > 1:
            cov_MI = unfolder.Eunfold(unfolder.kCovToys)
            chi2_MI = compute_chi2(unfolded_MI, truth, TMatrix_to_array(cov_MI))

        # SA results
        SA_info = {
            "mean": unfolded_SA,
            "std": error_SA,
            "chi2": np.round(chi2_SA, 4),
        }

        # HYB results
        HYB_info = None
        if quantum == True:
            HYB_info = {
                "mean": unfolded_HYB,
                "std": error_HYB,
                "chi2": np.round(chi2_HYB, 4),
            }

        # IBU results
        IBU_info = {
            "mean": unfolded_IBU,
            "std": error_IBU,
            "chi2": np.round(chi2_IBU, 4),
        }

        # MI results
        MI_info = {
            "mean": unfolded_MI,
            "std": error_MI,
            "chi2": np.round(chi2_MI, 4),
        }

        # Make plots
        make_plots(
            SA_info,
            HYB_info,
            IBU_info,
            MI_info,
            truth,
            measured,
            binning,
            var,
            quantum,
        )
