"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
Licensed under LICENSE, see LICENSE file for details.

The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import streamlit as st
import webbrowser

import y_gradient_active as gya
import y_gradient_not_active as gyn
import x_gradient as gx
import t1t2 as t12

def centered_image(image_path, caption="", width=[1, 2, 1] ):
    col1, col2, col3 = st.columns(width)
    with col2:
        st.image(image_path, caption=caption)


st.title("Magnet resonance imaging (MRI) - BASICS")

sections = [
    ("intro", "Introductions"),
    ("basic_physic", "1. Basic Physic"),
    ("rf_relax", "2. Introduction to RF-Pulses and Relaxation Times in MRI"),
    ("gradient", "3. Magnetic Field Gradient"),
    ("simulator", "4. Bloch-Simulator"),
    ("task", "5. Task")

]


sidebar_logo = "./logo/sidebar_logo_v2.jpg"
mainbody_logo = "./logo/main_body_log.png"

st.sidebar.header("Table of contents")

st.markdown("""
<style>
html { scroll-behavior: smooth; }
            
/* Sidebar-Header (st.sidebar.header) weiß */
[data-testid="stSidebar"] h2 {
    color: #ffffff !important;
    margin-top: 4px;
    font-size: 18px;
}
/* Sidebar-Background */
[data-testid="stSidebar"] {
    background-color: #2B2E37;
}

/* Navigationslinks */
[data-testid="stSidebar"] .navlink {
    display: block;
    padding: 8px 16px;
    margin: 2px 0;
    color: #FFFFFF;
    text-decoration: none;
    font-size: 16px;
    line-height: 1.4;
    border-radius: 4px;
}

/* Hover-effect */
[data-testid="stSidebar"] .navlink:hover {
    background: #3A3D46;
    border-left: 4px solid #4169e1;
    color: #eaeaea;
}


/* Main container with margin */
[data-testid="stAppViewContainer"] .block-container {
    max-width: 1100px;   /* bei Bedarf anpassen (z.B. 900–1200px) */
    margin-left: auto;
    margin-right: auto;
    padding-left: 1rem;
    padding-right: 1rem;
}

            
p {
    text-align: justify;
}            
                     
</style>
""", unsafe_allow_html=True)

for sid, label in sections:
    st.sidebar.markdown(f'<a class="navlink" href="#{sid}">{label}</a>', unsafe_allow_html=True)



st.header("Introduction", anchor="intro")
st.write("Magnetic Resonance Imaging (MRI) is a non-invasive medical imaging technique, which relies on strong magnetic fields, " \
"radio waves and the principles of nuclear magnetic resonance (NMR). " \
"MRI excels at imaging soft tissues like the brain, spinal cord, muscles, " \
"ligaments and tendons and as it doesn't use ionizing radiation, " \
"MRI is generally considered safe for repeated scans.")

st.write("**Magnetic Resonance Imaging (MRI)** is based on the behavior of protons in a magnetic field."
" The atoms consist, beside other things, of protons, which have a positive electrical charge and possess a spin."
" The spin of protons, combined with the electrical charge, causes them to"
" behave like small magnets with their own magnetic fields. And as we know, an electrical"
" current induces a magnetic field. In short: Where there is an electrical current, there is also a magnetic field.")
st.write("**So how do we use the natural magnetic field in MRI?**")
st.write("We use the natural magnetic fields of spinning protons by aligning them in a strong external magnetic field. This allows us to apply radiofrequency pulses (more in chapter 2) that manipulate the net magnetization, creating signals that are detected by coils and used to form images.")



st.header("1. Basic Physic", anchor="basic_physic")

st.subheader("Influence of an External Magnetic Fiel on an Atom")
st.write("As mentioned, we align the atoms in a strong external magnetic field $B_0$. Either they are parallel or antiparallel to the magnetic field. The protons prefer the state with less energy, which is parallel. "
" Just imagine: If they are parallel, it's like they are walking on their feet, so they need less energy than when they are walking on their hands, which is antiparallel."
" Because these two orientations are opposite, they cancel each other out, leaving a residual magnetization. We call this the net magnetization M."
" It is important to know that they don't just lie there, aligned to the external magnetic field. The protons' angular momentum prevents them from immediately aligning with the"
" external magnetic field, so they move in a certain way which is called precession."
" It's like giving a spinning top a gentle tap. It won't fall over, instead it will wobble or tumble around, so that the axis of the spinning top forms a cone shape.")
st.write("The frequency of the precession is defined by the Lamor frequency: ")
st.latex(r"\omega_0 = \gamma B_0")
st.write("As we see in this equation, the higher the magnetic field the faster the precession rate and the higher the precession frequency")
centered_image("./img/IMG_1.jpg", "**Figure 1:** Atoms aligning parallel or antiparallel to the magnetic field and creating the net magnetization M \n Source: https://physics.stackexchange.com/questions/138253/about-nuclear-magnetic-resonance", width=[1,5,1])



st.header("2. Introduction to RF-Pulses and Relaxation Times in MRI", anchor="rf_relax")

st.subheader("RF-Pulse")
st.write("The Radio Frequency Pulse (RF-Pulse) is crucial in the MRI because it is used to excite the protons in the body, enabling the generation of measurable signals." \
" Before an RF pulse is applied to the body, all atoms need to align parallel or antiparallel to an external magnetic field, so that they all start from the same direction. (see chapter 1)")
st.space("xxsmall")
st.write("**What does the Pulse do to the magnetic field?**")
st.write("When the RF-Pulse is applied, it transfers energy to the protons, causing the net magnetization vector to tip away from the $B_0$-axis and more towards the *transverse plane*. To absorb energy, the frequency of the RF pulse needs to match the Larmor frequency of the protons, allowing them to transition into a higher energy state." \
" It's important to note that the relaxation process occurs during and after the RF-Pulse, which affects the RF-Pulse.")
st.space("xxsmall")
st.write("**Pulse Types**")
st.write("To excite the atoms from the longitudinal to the transverse plane, we use different types of radiofrequency pulses."
" As an example, the pulse type Square is a constant pulse that depends on time and amplitude. It's a simple pulse shape and easy to generate, but is not ideal for precise slice selection and is therefore not as effective as the commonly used Sinc-Pulse.")
st.write("The sinc pulse has a more complex shape, like a sinc function, and provides better frequency selectivity, making it more suitable for precise slice excitation."
" By adding multiple frequencies together, the resulting RF-pulse takes the shape of a sinc function:")
st.latex(r"sinc(x)=\frac{sin(x)}{x}")
st.write("This sinc-shaped pulse contains a controllable frequency spectrum, which makes it ideal for selective excitation.")

st.subheader("T1 and T2 Relaxation")
st.write("Like mentioned, the relaxation process occurs **during** and **after the RF-Pulse**")
st.space("xxsmall")
st.write("**But what exactly is relaxation?**")
st.write("Relaxation is when the spin system wants to return to equilibrium. This means it gives away the excess energy to " \
" achieve a state with lower energy. The time it takes to achieve this state is defined by the T1 and T2 relaxation times.")

col1, col2, col3 = st.columns([4,1,4])
with col1:
    st.write("**T1-Relaxation** is the longitudinale relaxation (i.e. spin-lattice-relaxation).")
    st.write("It describes the time that it takes for the *longitudinal magnetization* to recover to its original value.")
with col3:
    st.write("**T2-Relaxation** is the transverse relaxation (i.e. spin-spin-relaxation).")
    st.write("The T2 relaxation describes the time that it takes for the *transverse magnetization* to decay.")
st.space("xxsmall")


# === T1 und T2 Kurven ===
fig = t12.make_figure()  # ggf. Parameter übergeben
st.pyplot(fig, clear_figure=True)
st.caption("**Figure 2:** T1 and T2 curve")


#centered_image("./img/T1_T2.png",  caption="**Figure 2:** T1 and T2 curve")
st.space("xxsmall")
st.write("Note that this is *not the exact time* it takes, but describes how fast this process occurs.")
st.write("As we see in **Figure 2**, after one T1 time, the net magnetization in the longitudinal plane recovered back to its 63% original value $M_0$.")
st.write("For one T2 time, the net magnetization in the transverse plane decayed by 37% of the original value $M_0$.")
st.space("xxsmall")
st.write("**How does it influence the RF-Pulse?**")
st.write("As we know, the relaxation process describes how fast the protons give away the excess energy to achieve the state"
" with lower energy. That means if the RF pulse isn't strong and long enough to flip, it won't flip fully. Instead, it"
" will reach a point where it stagnates and then relaxes back to the original state after the RF pulse.")


st.header("3. Magnetic Field Gradient", anchor="gradient")

st.write("The gradient is defined as the change in the magnetic field over the change in distance." \
" To calculate the gradient, we can use the following equation:")
st.write("$G = \Delta B/ \Delta s = (B_b - B_a)/ \Delta s$ ")
st.write("where $\Delta B$ is the change in field and $\Delta s$ is the change in distance.")
st.write("In MRI, three different gradients are needed to encode the signal spatially: the x-, y-, and z-axis gradients." \
" In each of these directions, they produce a linear variation in the magnetic field, which is added to the main magnetic field $B_0$.")
st.space("xxsmall")
st.write("**But why do we need this?**")
st.write("Each gradient axis has a different function:")

tab1, tab2, tab3 = st.tabs(["z-axis", "y-axis", "x-axis"])

with tab1:
    st.subheader("z-axis gradient ($G_z$)")
    st.write("The z-gradient, also known as the 'slice selecting gradient', is primarily used for the excitation of the specific slice that is to be imaged."
" By applying the principles mentioned in chapter two, we can excite the protons within a single slice. This gradient is active only during the slice selection process.")
    #centered_image("./img/z-gradient.jpg", caption="Variation in the magnteic fiel in z-direction", width=[1, 2, 1])
    
    
    st.write("We have two ways to determine a certain **slice thickness**:")

    col1, col2, col3 = st.columns([3, 0.1, 3])
    with col1:
        st.write("**1.) Wider RF pulse frequency**")
        st.write("To adjust the slice thickness, we can transmit an RF pulse with a specific range of frequencies (bandwidth); the wider the frequency range, the thicker the resulting slice.")
        st.write("For example, if we use an RF pulse with frequencies ranging from 64 to 65 MHz, we obtain a slice thickness $S_1$ from 64 to 65 MHz. Similarly, using a range from 64 to 64.5 MHz results in a thinner slice")
        #st.image("./img/rfPulse_sliceThickness.png", caption="Figure []: Adjust slice thickness with rf pulse.")
        
    
    with col3:
        st.write("**2.) Change the slope of the gradient field**")
        st.write("If we modify the z-gradient to be steeper—meaning there is a greater difference in field strength over a specific distance—the precession frequency will also vary to a greater degree")
        #st.image("./img/modifyZ_sliceThickness.png", caption="Figure []: Change slice thickness with steeper gradient field")
    

with tab2: 
    st.subheader("y-axis gradient ($G_y$)")
    st.write("The y-gradient is the 'phase-encoding gradient', which is applied after the slice selection. Every proton within the slice has the same frequency after the RF pulse." \
    " To locate each column for the readout, we must differentiate them by applying an additional gradient in the y-axis direction to alter their phases.")
    col1, col2, col3 = st.columns([4, 2, 4])
    with col1:
        fig = gyn.make_figure()  # ggf. Parameter übergeben
        st.pyplot(fig, clear_figure=True)
        st.caption("**Figure 3a:** Protons have the same frequency after the RF pulse.")
        #st.image("./img/protons_after_pulse.png", caption="Figure []: Protons have the same frequency after the rf pulse.")
    with col2:
        st.space("xxlarge") 
        st.write("Now activating the y-gradient $\Longrightarrow$")
    with col3:
        fig = gya.make_figure(labels=("65 ms","64 ms","63 ms"), angles_deg=(-55, -15, 60))
        st.pyplot(fig, use_container_width=True, clear_figure=True)
        st.caption("**Figure 3b:** Protons in different columns have different frequencies after activating the y-gradient.")
        #st.image("./img/protons_phase_yAxis.png", caption="Figure []: Protons in different columns havedifferent frequencies after activating the y-gradient.")



with tab3:
    st.subheader("x-axis gradient ($G_x$)")
    st.write("The x-gradient is the 'frequency-encoding gradient' and is activated during the readout." \
    " After dephasing the columns (Fig. [ ]a), we now want to differentiate every proton within the column (Fig. [ ]b) so that we can measure how much energy each atom emits.")
    fig = gx.make_figure()
    st.pyplot(fig, clear_figure=True)
    st.caption("**Figure 4:** Dephasing a column with a gradient in direction of the x-axis.")
    #centered_image("./img/frequency_encoding.png", caption="Figure []:Dephasing a column with a gradient in direction of the x-axis.")






st.header("4. Bloch-Simulator", anchor="simulator")
st.write("To translate the theory of magnetization dynamics into a visual experience, "
    " this simulator combines the abstract Bloch equations with physical reality. "
    " Therefore, the parameters in this interactive environment aren't just numbers, "
    " but dynamic motions. By manipulating pulse amplitude, duration, relaxation times, "
    " and other parameters, it is possible to see the behavior of the magnetization."
)



st.write("This simulator offers two modes: single mode and multi-atom mode." \
" In both modes, the user can adjust the following parameters:")
parameters = [("B0", "The constant, homogeneous magnetic field (T)."), 
                ("Relaxation", "If selected, you can change the T1 and T2 relaxation times (s)."), 
                ("Pulse Type", "Select the type of pulse."),
                ("B1", "Adjust the amplitude of the RF field B1."),
                ("B1freq", "Adjust the RF frequency (Hz).")]

n_cols = 3  # Anzahl Spalten pro Zeile

st.subheader("Parameters")

for i in range(0, len(parameters), n_cols):
    cols = st.columns(n_cols)
    for col, (title, desc) in zip(cols, parameters[i:i+n_cols]):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)


tab1, tab2 = st.tabs(["Single Mode", " Multi-Atom Mode"])

with tab1:
    st.header("Single Mode")
    st.write("In Single Mode, you can observe the dynamic magnetization of a single atom. " \
    " Adjustable visual aids-such as trajectory lines and axes-in the Single Mode Visualizer help you analyze how the atom responds to different parameters (e.g., B0, B1, pulse type, T1, T2).")
    centered_image("./img/screen.jpg", caption="Figure 5: Single-Mode", width=[1, 8, 1])

with tab2:
    st.header("Multi Atom Mode")
    st.write("The main goal of Multi-Atom Mode is to understand how to target a single slice. " \
    " The user-interface is the same, but a special feature is the option to switch the visualization to a 3D head model, allowing the user to simulate a slice.")
    centered_image("./img/multi_atom_screen.jpg", caption="Figure 6: Multi Atom Mode", width=[1, 8, 1])

st.subheader("Installation")
st.write("To install the Bloch-Simulator, please follow the instructions after pressing the download button.")
if st.button("Download"):
    webbrowser.open("https://github.com/FraunhoferMEVIS/MR-Tools/tree/main/mr_simulator_v1.0.0")




st.header("5. Tasks", anchor="task")

task1 = st.expander("Task 1: 90° Flip")
with task1:
    st.write("**Mode:** Single")
    
    st.write("Flip the magnetization of the single atom by 90 degrees. Perform this once with a square pulse and once with a sinc pulse. Which pulse flips it faster and why?" \
             " Adjust the parameters accordingly!")
    st.write("**Predefined parameter**")
    st.write("**B1:** 1.6")

    with st.popover("Show solution"):
        st.write("**B0:** 2.5")
        st.write("**B1_freq:** 2.5")
        st.write("With a peak-amplitude constraint, a constant-amplitude square pulse maximizes the area per unit" \
        ". A sinc pulse spends time at amplitudes below the peak (and includes zero-crossings), so it need longer to accumulate the same area. ")
        st.caption("Click outside to close.")

    

task2 = st.expander("Task 2: Slice selection")
with task2:
    st.write("**Mode**: Multi")
    st.write("**Pulse type:** square")
    st.write("If the frequency of the first slice is 2.5 and that of the second slice is 3.0, what frequencies do the third and fourth ones have? Excite the fourth slice!")
    st.caption("**Tip:** Set $\Delta s = 1$")

    with st.popover("Show solution"):
        st.write("**B0:** 2.5")
        st.write("**B1_freq:** 2.5")
        st.write("$G = (3.0 - 2.5)/ 1 = 0.5$ ")
        st.write("Third slice: 3.5; Fourth slice: 4.0")
        st.write("Parameter settings for the fourth slice: B0=2.5, B1=1.0 (or any other number), B1_freq=4.0")
        st.caption("Click outside to close.")