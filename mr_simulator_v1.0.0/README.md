# TACTIX Tutorials


## MRI Basic Simulator

## Description
The Basic MRI Simulator is an interactive visualization tool that demonstrates the fundamental concepts of magnetic resonance imaging (MRI). Users can explore how magnetic fields, RF pulses, and relaxation times influence spin dynamics using 3D graphics and real-time simulation. The tool is ideal for teaching, learning, and experimenting with basic MRI physics.

## Installation

### 0.Prerequisite: Install Node.js

Before you can use npm install or run the project, you must have Node.js installed on your system.
Node.js includes npm, which is required to install project dependencies.
To check if Node.js and npm are installed, run:

<code>node -v
npm -v</code>

Both commands should output a version number.
If not, download and install Node.js from https://nodejs.org/ 

### 1. Download the repository

<code>git clone --branch simulator-mri-basics https://gitlab.fme.lan/tactix/tactix-tutorials.git</code>

### 2. Install dependencies

Before you install the dependencies, navigate into the folder:

<code>cd tactix-tutorials/Simulator</code>

After that you only need to run one command to install all dependencies:

<code>npm install</code>



### 3. Simulator directory structure
Your Simulator directory should look like this:


<code>/project-root/Simulator
│
├── Simulator_Bloch.html
├── styles.css
├── package.json
├── package-lock.json
├── web_logo.jpeg
├── js/
│   ├── Bloch_simulator.js
│   ├── graph.js
│   └── sequenz.js
└── models/
    └── LeePerrySmith.glb
    
</code>


## Start the project

Before you start the simulator, navigate back to the tactix-tutorials folder by typing:

<code>cd ..</code>

Then: 

<code>parcel ./Simulator/Simulator_Bloch.html</code> or <code>npx parcel ./Simulator/Simulator_Bloch.html</code> in case if Parcel is installed locally instead of globally.

After running the command, open your browser and navigate to http://localhost:1234 or click the localhost link in your terminal.

## Support
If you have any questions or need help, please feel free to contact me.
nima.mozaffari@mevis.fraunhofer.de
